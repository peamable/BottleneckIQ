from datetime import datetime
import pandas as pd
from sqlalchemy import text
from app.core.database import engine
from app.services.staging_tables import ensure_staging_tables, reset_staging_batch
from app.services.data_validation import validate_batch


def load_to_staging(
        df_ed_stay: pd.DataFrame, 
        df_stay_info: pd.DataFrame, 
        batch_id: str,
        upload_id: int | None = None,
    ) -> None:
    ensure_staging_tables()
    reset_staging_batch(batch_id)

    now = datetime.utcnow()

    df1 = df_ed_stay.copy()
    df1["batch_id"] = batch_id
    df1["upload_id"] = upload_id    
    df1["ingested_at"] = now
    df1 = df1.where(pd.notnull(df1), None)

    df1.to_sql(
        "ed_stay_staging",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )

    if df_stay_info is not None and len(df_stay_info) > 0:
        df2 = df_stay_info.copy()
        df2["batch_id"] = batch_id
        df2["upload_id"] = upload_id
        df2["ingested_at"] = now
        df2 = df2.where(pd.notnull(df2), None)

        df2.to_sql(
            "stay_info_staging",
            con=engine,
            if_exists="append",
            index=False,
            chunksize=5000,
            method="multi",
        )

def insert_final_from_staging(batch_id: str):
    with engine.begin() as conn:
        # ed_stay: insert once, ignore duplicates, normalize activity
        res1 = conn.execute(text("""
            INSERT IGNORE INTO ed_stay (stay_id, ed_timestamp, activity)
            SELECT
              stay_id,
              ed_timestamp,
              activity
            FROM ed_stay_staging
            WHERE batch_id=:b
              AND stay_id IS NOT NULL
              AND ed_timestamp IS NOT NULL
              AND activity IS NOT NULL
              AND TRIM(activity) <> ''
        """), {"b": batch_id})

        # stay_info: upsert by stay_id
        res2 = conn.execute(text("""
            INSERT INTO stay_info (stay_id, gender, race, arrival_transport, disposition, scale_level, chiefcomplaint)
            SELECT stay_id, gender, race, arrival_transport, disposition, scale_level, chiefcomplaint
            FROM stay_info_staging
            WHERE batch_id=:b
              AND stay_id IS NOT NULL
              AND gender IS NOT NULL
              AND race IS NOT NULL
              AND arrival_transport IS NOT NULL
              AND disposition IS NOT NULL
              AND scale_level IS NOT NULL
              AND chiefcomplaint IS NOT NULL
            ON DUPLICATE KEY UPDATE
              gender = VALUES(gender),
              race = VALUES(race),
              arrival_transport = VALUES(arrival_transport),
              disposition = VALUES(disposition),
              scale_level = VALUES(scale_level),
              chiefcomplaint = VALUES(chiefcomplaint)
        """), {"b": batch_id})

        return {"ed_stay_inserted": res1.rowcount, "stay_info_affected": res2.rowcount}

#def cleanup_staging(batch_id: str):
#    with engine.begin() as conn:
#        conn.execute(text("DELETE FROM ed_stay_staging WHERE batch_id=:b"), {"b": batch_id})
#        conn.execute(text("DELETE FROM stay_info_staging WHERE batch_id=:b"), {"b": batch_id})

def process_batch(
        df_ed_stay: pd.DataFrame,
        df_stay_info: pd.DataFrame,
        period_start: datetime,
        period_end: datetime, 
        batch_id: str = None, 
        cleanup: bool = True
    ) -> dict:
    # generate batch_id 
    if batch_id is None:
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    load_to_staging(df_ed_stay, df_stay_info, batch_id, upload_id=None)

    errors = validate_batch(batch_id)
    if errors:
        return {"ok": False, "errors": errors, "batch_id": batch_id}

    try:
        stats = insert_final_from_staging(batch_id)
    except Exception as e:
        return {"ok": False, "errors": [f"Final insert failed: {str(e)}"], "batch_id": batch_id}

    
   
#    if cleanup:
#        cleanup_staging(batch_id)

    return {"ok": True, "errors": [], "batch_id": batch_id, **stats}