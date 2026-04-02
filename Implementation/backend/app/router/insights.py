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

@router.get("/volume-efficiency-correlation")
async def get_volume_efficiency_correlation():
    return service.get_volume_efficiency_correlation()

@router.get("/disposition_milestone_analysis")
async def get_disposition_milestone_analysis(upload_id: Optional[int] = Query(None)):
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        return {
            "upload_id": None,
            "disposition_milestone_analysis": [],
            "message": "No data available"
        }

    return service.get_disposition_milestone_breakdown(effective_id)

@router.get('/acuity_level_analysis')
async def get_acuity_level_analysis(upload_id: Optional[int] = Query(None)):
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        return {
            "upload_id": None,
            "acuity_level_analysis": [],
            "message": "No data available"
        }

    return service.get_acuity_level_breakdown(effective_id)


@router.get('/temporal_heatmap')
async def get_temporal_heatmap(upload_id: Optional[int] = Query(None), lookback: int = Query(3, description="Number of recent uploads to aggregate")):
    effective_id = upload_id or service.get_latest_upload_id()
    if effective_id is None:
        return {
            "upload_id": None,
            "day_labels": ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
            "slice_labels": ['Dawn (00:00-06:00)', 'Morning (06:00-12:00)', 'Afternoon (12:00-18:00)', 'Night (18:00-24:00)'],
            "volume_matrix": [[0,0,0,0] for _ in range(7)]
        }

    return service.get_temporal_heatmap(effective_id, lookback)


@router.get('/stage_temporal_forecast')
async def get_stage_temporal_forecast(
    upload_id: Optional[int] = Query(None),
    lookback: int = Query(3, description="Number of recent uploads to aggregate")
):
    effective_id = upload_id or service.get_latest_upload_id()
    return service.get_stage_temporal_forecast(effective_id, lookback)


@router.get('/event_flow_forecast')
async def get_event_flow_forecast(
    upload_id: Optional[int] = Query(None),
    lookback: int = Query(3, description="Number of recent uploads to aggregate")
):
    effective_id = upload_id or service.get_latest_upload_id()
    return service.get_event_flow_forecast_insights(effective_id, lookback)
