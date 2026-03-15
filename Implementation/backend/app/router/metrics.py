from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services import metrics_services as service

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/dashboard")
async def get_dashboard_data(
    upload_id: Optional[int] = Query(None), 
    batch_id: Optional[str] = Query(None) 
):
    # Use service to find ID if not provided
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        # Return a 200 with empty data instead of a 404/422 
        # to keep the frontend from crashing
        return {"upload_id": None, "metrics": [], "message": "No data available"}
        
    rows = service.get_metrics_data(effective_id, batch_id)
    
    return {
        "upload_id": effective_id,
        "batch_id": batch_id,
        "metrics": rows
    }