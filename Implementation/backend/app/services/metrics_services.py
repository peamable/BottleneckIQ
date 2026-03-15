from typing import Optional, List, Dict, Any
from sqlalchemy import text
import json
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

def get_metrics_data(upload_id: int, batch_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches and normalizes metrics for a specific ID."""
    query_str = "SELECT * FROM metrics WHERE upload_id = :upload_id"
    params = {"upload_id": upload_id}
    
    if batch_id:
        query_str += " AND batch_id = :batch_id"
        params["batch_id"] = batch_id
        
    query = text(query_str + " ORDER BY metric_name")
    
    with engine.connect() as conn:
        rows = conn.execute(query, params).mappings().all()

    normalized_rows = []
    for row in rows:
        row_dict = dict(row)
        # Handle the JSON string conversion safely
        acuity_val = row_dict.get("stay_time_per_acuity")
        if isinstance(acuity_val, str):
            try:
                row_dict["stay_time_per_acuity"] = json.loads(acuity_val)
            except json.JSONDecodeError:
                row_dict["stay_time_per_acuity"] = {}
        normalized_rows.append(row_dict)
    return normalized_rows