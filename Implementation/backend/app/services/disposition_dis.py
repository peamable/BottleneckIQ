from sqlalchemy import text
from app.core.database import engine


def get_latest_upload_id() -> int | None:
    """Returns the most recent upload_id recorded in upload_history."""
    with engine.connect() as conn:
        row = conn.execute(text("SELECT MAX(upload_id) AS upload_id FROM upload_history")).mappings().first()
        return row["upload_id"] if row else None


def get_disposition_mix(upload_id: int | None = None) -> dict:
    """Return disposition percentage mix for the given upload.

    If upload_id is None, the latest upload_id is used.

    Returns:
        {"upload_id": <int|None>, "disposition_mix": [ ... ]}
    """
    if upload_id is None:
        upload_id = get_latest_upload_id()

    if upload_id is None:
        return {"upload_id": None, "disposition_mix": []}

    query = text("""
        SELECT 
            COALESCE(disposition, 'Unknown') AS disposition, 
            COUNT(*) AS cnt,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS pct
        FROM stay_info_staging
        WHERE upload_id = :upload_id
        GROUP BY disposition
        ORDER BY pct DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    disposition_mix = [
        {
            "type": r["disposition"],
            "percentage": float(round(r["pct"], 2))
        }
        for r in rows
    ]

    return {"upload_id": upload_id, "disposition_mix": disposition_mix}
