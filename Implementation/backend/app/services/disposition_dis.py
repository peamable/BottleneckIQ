from sqlalchemy import text
from app.core.database import engine


def get_disposition_mix() -> dict:
    # We query the permanent table 'stay_info'
    # Since we aren't using upload_id yet, we get the distribution of all processed records
    query = text("""
        SELECT
            disposition,
            COUNT(*) AS cnt,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS pct
        FROM stay_info
        WHERE disposition IS NOT NULL AND disposition <> ''
        GROUP BY disposition
        ORDER BY pct DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()

    disposition_mix = [
        {
            "type": r["disposition"],
            "percentage": float(round(r["pct"], 2))
        }
        for r in rows
    ]

    return {"logistics_root_cause": {"disposition_mix": disposition_mix}}