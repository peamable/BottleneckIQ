from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services import insights_services as service

router = APIRouter(
    prefix="/insights",
    tags=["insights"]
)


@router.get("/logistics_root_cause")
async def get_logistics_root_cause( upload_id: Optional[int] = Query(None)
):
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        return {
            "upload_id": None,
            "logistics_root_cause": {
                "disposition_mix": [],
                "top_chief_complaints": []
            },
            "message": "No data available"
        }

    return {
        "upload_id": effective_id,
        "logistics_root_cause": {
            "disposition_mix": service.get_disposition_mix(effective_id),
            "top_chief_complaints": service.get_top_chief_complaints(effective_id)
        }
    }

@router.get("/demographics_audit")
async def get_demographics_audit( upload_id: Optional[int] = Query(None)
):
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        return {
            "upload_id": None,
                "equity_audit": [],
                "message": "No data available"
        }

    return {
        "upload_id": effective_id,
            "equity_audit": service.get_equity_audit(effective_id)
        
    }

@router.get("/chief_complaint_counts")
async def get_chief_complaint_counts( upload_id: Optional[int] = Query(None)
):
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        return {
            "upload_id": None,
            "chief_complaint_counts": [],
            "message": "No data available"
        }

    return {
        "upload_id": effective_id,
        "chief_complaint_counts": service.get_chief_complaint_counts(effective_id)
    }


@router.get("/chief_complaint_bottlenecks")
async def get_chief_complaint_bottlenecks(upload_id: Optional[int] = Query(None)):
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        return {
            "upload_id": None,
            "chief_complaint_bottlenecks": [],
            "message": "No data available"
        }

    return {
        "upload_id": effective_id,
        "chief_complaint_bottlenecks": service.get_chief_complaint_bottleneck_insights(effective_id)
    }
   
