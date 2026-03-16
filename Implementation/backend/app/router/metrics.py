from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services import metrics_services as service

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/dashboard")
async def get_dashboard_data(
    upload_id: Optional[int] = Query(None)
):
    # Use service to find ID if not provided
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        # Return a 200 with empty data instead of a 404/422 
        # to keep the frontend from crashing
        return {"upload_id": None, "metrics": [], "message": "No data available"}
        
    rows = service.get_metrics_data(effective_id)
    
    return {
        "upload_id": effective_id,
        "metrics": rows
    }

@router.get("/acuity-benchmarks")
def get_acuity_benchmarks(
    upload_id: Optional[int] = Query(None)
):
    effective_id = upload_id or service.get_latest_upload_id()
    if not effective_id:
        raise HTTPException(status_code=404, detail="No completed upload found.")

    return service.build_acuity_benchmarks(effective_id)

@router.get("/hourly-aggregates")
async def get_hourly_aggregates(
    upload_id: Optional[int] = Query(None)
):
    # Determine which ID to use
    effective_id = upload_id or service.get_latest_upload_id()
    
    if not effective_id:
        raise HTTPException(status_code=404, detail="No valid data period found.")

    # Call the new service function
    volume_data = service.get_hourly_patient_density(effective_id)
    
    return {
        "upload_id": effective_id,
        "volume_chart": volume_data
    }