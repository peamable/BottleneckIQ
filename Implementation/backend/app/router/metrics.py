from fastapi import APIRouter, HTTPException, Query
from typing import Optional # Add this import
from sqlalchemy import text
import json
from app.core.database import engine

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"]
)

# --- Updated Logic Function ---

def get_metrics_filtered(upload_id: int, batch_id: Optional[int] = None):
    # Base query
    query_str = "SELECT * FROM metrics WHERE upload_id = :upload_id"
    params = {"upload_id": upload_id}
    
    # Ready for the batch change!
    if batch_id is not None:
        query_str += " AND batch_id = :batch_id"
        params["batch_id"] = batch_id
        
    query = text(query_str + " ORDER BY metric_name")
    
    with engine.connect() as conn:
        rows = conn.execute(query, params).mappings().all()

    normalized_rows = []
    for row in rows:
        row_dict = dict(row)
        # Standard JSON normalization
        acuity_val = row_dict.get("stay_time_per_acuity")
        if isinstance(acuity_val, str):
            try:
                row_dict["stay_time_per_acuity"] = json.loads(acuity_val)
            except json.JSONDecodeError:
                row_dict["stay_time_per_acuity"] = {}
        normalized_rows.append(row_dict)
    return normalized_rows

# --- Updated Endpoints ---

@router.get("/dashboard")
async def get_dashboard_data(
    upload_id: Optional[int] = Query(None), 
    batch_id: Optional[int] = Query(None) 
):
    # 1. Logic to find the ID (your existing code is good)
    if upload_id is None:
        query_latest = text("SELECT MAX(upload_id) AS upload_id FROM metrics")
        with engine.connect() as conn:
            result = conn.execute(query_latest).mappings().first()
            upload_id = result["upload_id"] if result else None

    if upload_id is None:
        raise HTTPException(status_code=404, detail="No metrics found.")
        
    # 2. Get the actual rows
    rows = get_metrics_filtered(upload_id, batch_id)
    
    # 3. FIX: Wrap the response so React can read 'payload.metrics'
    return {
        "upload_id": upload_id,
        "batch_id": batch_id,
        "metrics": rows  # This is the key your ViewMetrics.jsx is looking for
    }