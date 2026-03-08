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

        # check null for gender, race, arrival_transport, disposition and chiefcomplaint in stay_info_staging
        bad_stay_info_nulls = conn.execute(text("""
            SELECT COUNT(*) FROM stay_info_staging
            WHERE batch_id=:b AND (gender IS NULL OR race IS NULL OR arrival_transport IS NULL OR disposition IS NULL OR chiefcomplaint IS NULL)
        """), {"b": batch_id}).scalar()

        if bad_stay_info_nulls and bad_stay_info_nulls > 0:
            errors.append(f"stay_info_staging has {bad_stay_info_nulls} rows with NULL values for gender, race, arrival_transport, disposition, or chiefcomplaint.")

        # check scale_level column of stay_info within integer range 1 to 5 
       
        bad_scale_level = conn.execute(text("""
            SELECT COUNT(*) FROM stay_info_staging
            WHERE batch_id=:b
              AND (gender IS NULL OR scale_level < 1 OR scale_level > 5 OR scale_level <> FLOOR(scale_level))
        """), {"b": batch_id}).scalar()

        if bad_scale_level and bad_scale_level > 0:
            errors.append(f"stay_info_staging has {bad_scale_level} rows with invalid scale_level (expect integer 1–5).")

    return errors
