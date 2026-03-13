from fastapi import APIRouter, HTTPException, Query
from app.services.disposition_dis import get_disposition_mix

router = APIRouter(
    prefix="/insights",
    tags=["insights"]
)


@router.get("/logistics_root_cause")
async def get_logistics_root_cause(upload_id: int | None = Query(None)):
    """Return logistics root cause data for the upload (disposition mix, etc.)"""
    result = get_disposition_mix(upload_id)

    return {
        "upload_id": result.get("upload_id"),
        "logistics_root_cause": {
            "disposition_mix": result.get("disposition_mix", [])
        }
    }
