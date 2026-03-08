from datetime import datetime
from sqlalchemy import text
from uuid import uuid4
from app.core.database import engine

def create_upload_history(period_start: str, period_end: str):
    """Create upload history record and return upload_id and batch_id"""
    try:
        ps_dt = datetime.fromisoformat(period_start)
        pe_dt = datetime.fromisoformat(period_end)
    except ValueError as e:
        raise ValueError(f"Invalid date format: period_start='{period_start}', period_end='{period_end}'. Error: {e}")
    
    # Generate batch_id BEFORE inserting
    batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}"
    
    with engine.begin() as conn:
        res = conn.execute(text("""
            INSERT INTO upload_history (batch_id, upload_timestamp, period_start, period_end, status)
            VALUES (:bid, :ts, :ps, :pe, 'pending')
        """), {
            "bid": batch_id,
            "ts": datetime.utcnow(),
            "ps": ps_dt,
            "pe": pe_dt
        })
        upload_id = res.lastrowid
    
    return upload_id, batch_id

def update_upload_status(upload_id: int, status: str):
    """Update upload history status"""
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE upload_history SET status=:status WHERE upload_id=:uid
        """), {"status": status, "uid": upload_id})