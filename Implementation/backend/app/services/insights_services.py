from typing import Optional
from sqlalchemy import text
from app.core.database import engine

def get_latest_upload_id() -> Optional[int]:
    """Helper to find the most recent successful upload ID."""
    query = text("""
        SELECT upload_id FROM upload_history 
        WHERE status = 'completed' 
        ORDER BY upload_id DESC LIMIT 1
    """)
    with engine.connect() as conn:
        result = conn.execute(query).mappings().first()
        return result["upload_id"] if result else None
    

# disposition mix pie chart visualization
def get_disposition_mix(upload_id: int) -> dict:
    # We query the permanent table 'stay_info'
    # Since we aren't using upload_id yet, we get the distribution of all processed records
    query = text("""
        SELECT
            CASE
                WHEN LOWER(TRIM(disposition)) = 'home' THEN 'Home'
                WHEN LOWER(TRIM(disposition)) = 'admitted' THEN 'Admitted'
                WHEN LOWER(TRIM(disposition)) IN (
                    'eloped',
                    'left without being seen',
                    'left against medical advice',
                    'expired',
                    'transfer',
                    'other'
                ) THEN 'Other'
                ELSE 'Other'
            END AS disposition_group,
            COUNT(DISTINCT stay_id) AS cnt,
            ROUND(
                COUNT(DISTINCT stay_id) * 100.0
                / SUM(COUNT(DISTINCT stay_id)) OVER (),
                2
            ) AS pct
        FROM stay_info
        WHERE disposition IS NOT NULL
        AND disposition <> ''
        AND upload_id = :upload_id
        GROUP BY disposition_group
        ORDER BY pct DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    disposition_mix = [
        {
            "type": r["disposition_group"],
            "percentage": float(round(r["pct"], 2))
        }
        for r in rows
    ]

    return disposition_mix

# chiefcomplaint top 5 bar chart visualization
def get_top_chief_complaints(upload_id: int) -> dict:
    query = text("""
        WITH stay_duration AS (
            SELECT
                stay_id,
                MAX(total_ed_stay_time) AS total_ed_stay_time
            FROM event_log
            WHERE total_ed_stay_time IS NOT NULL
            GROUP BY stay_id
        )
        SELECT
            si.chiefcomplaint,
            COUNT(*) AS cnt,
            AVG(sd.total_ed_stay_time) AS avg_total_ed_stay_time
        FROM stay_info si
        JOIN stay_duration sd
            ON si.stay_id = sd.stay_id
        WHERE si.upload_id = :upload_id
          AND si.chiefcomplaint IS NOT NULL
          AND si.chiefcomplaint <> ''
        GROUP BY si.chiefcomplaint
        ORDER BY cnt DESC
        LIMIT 5
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    top_chief_complaints = [
        {
            "chiefcomplaint": r["chiefcomplaint"],
            "count": r["cnt"],
            "avg_total_ed_stay_time": float(round(r["avg_total_ed_stay_time"], 2)) if r["avg_total_ed_stay_time"] is not None else None
        }
        for r in rows
    ]

    return top_chief_complaints

# Demographics flow audit bar chart visualization

def get_equity_audit(upload_id: int) -> list[dict]:
    query = text("""
        WITH stay_duration AS (
            SELECT
                stay_id,
                MAX(total_ed_stay_time) AS total_ed_stay_time
            FROM event_log
            WHERE total_ed_stay_time IS NOT NULL
            GROUP BY stay_id
        ),
        base AS (
            SELECT
                si.race,
                sd.total_ed_stay_time
            FROM stay_info si
            JOIN stay_duration sd
              ON si.stay_id = sd.stay_id
            WHERE si.upload_id = :upload_id
              AND si.race IS NOT NULL
              AND si.race <> ''
        ),
        overall AS (
            SELECT
                AVG(total_ed_stay_time) AS overall_avg_stay_time
            FROM base
        )
        SELECT
            b.race,
            COUNT(*) AS cnt,
            ROUND(AVG(b.total_ed_stay_time), 2) AS race_avg_stay_time,
            ROUND(o.overall_avg_stay_time, 2) AS overall_avg_stay_time,
            ROUND(
                ((AVG(b.total_ed_stay_time) - o.overall_avg_stay_time) / o.overall_avg_stay_time) * 100,
                2
            ) AS variance_pct
        FROM base b
        CROSS JOIN overall o
        GROUP BY b.race, o.overall_avg_stay_time
        ORDER BY variance_pct DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    equity_audit = [
         {
            "group": r["race"],
            "variance": float(r["variance_pct"]),
            #"race_avg_total_ed_stay_time": float(r["race_avg_stay_time"]),
            #"overall_avg_total_ed_stay_time": float(r["overall_avg_stay_time"]),
            #"count": int(r["cnt"])
        }
        for r in rows
    ]

    return equity_audit
