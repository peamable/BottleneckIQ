from sqlalchemy import text
from app.core.database import engine

def validate_batch(batch_id: str) -> list[str]:
    """
    Returns list of error messages. Empty list = pass.
    """
    errors = []

    with engine.begin() as conn:
        # check null for stay_id and ed_timestamp and activity
        bad_ed = conn.execute(text("""
            SELECT COUNT(*) FROM ed_stay_staging
            WHERE batch_id=:b AND (stay_id IS NULL OR ed_timestamp IS NULL OR activity IS NULL OR activity='')
        """), {"b": batch_id}).scalar()

        if bad_ed and bad_ed > 0:
            errors.append(f"ed_stay_staging has {bad_ed} rows with NULL/empty stay_id, ed_timestamp, or activity.")

        # check duplicates in staging for exact same event for stay_id,ed_timestamp,activity
        repeated_rows = conn.execute(text("""
            SELECT COUNT(*) FROM (
              SELECT stay_id, activity, ed_timestamp, COUNT(*) c
              FROM ed_stay_staging
              WHERE batch_id=:b
              GROUP BY stay_id, activity, ed_timestamp
              HAVING c > 1
            ) t
        """), {"b": batch_id}).scalar()

        if repeated_rows and repeated_rows > 0:
            errors.append(f"ed_stay_staging has {repeated_rows} duplicate event keys (stay_id, ed_timestamp, activity).")

        
        # check scale_level column of acuity within integer range 1 to 5 
        bad_acuity = conn.execute(text("""
            SELECT COUNT(*) FROM acuity_staging
            WHERE batch_id=:b
              AND scale_level IS NOT NULL
              AND (scale_level < 1 OR scale_level > 5 OR scale_level <> FLOOR(scale_level))
        """), {"b": batch_id}).scalar()

        if bad_acuity and bad_acuity > 0:
            errors.append(f"acuity_staging has {bad_acuity} rows with invalid scale_level (expect integer 1–5).")

    return errors
