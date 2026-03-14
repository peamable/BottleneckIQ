from fastapi import APIRouter, HTTPException, Query
from app.services.disposition_dis import get_disposition_mix

router = APIRouter(
    prefix="/insights",
    tags=["insights"]
)


@router.get("/logistics_root_cause")
async def get_logistics_root_cause():
    """Return logistics root cause data for the upload (disposition mix, etc.)"""
    result = get_disposition_mix()
    
    return {
        "logistics_root_cause": result["logistics_root_cause"]
    }
