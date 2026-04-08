from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services import insights_services as service

router = APIRouter(
    prefix="/insights",
    tags=["insights"]
)


@router.get("/patient_flow_analysis")
async def get_patient_flow_analysis(upload_id: Optional[int] = Query(None)):
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        return {
            "upload_id": None,
            "patient_flow_analysis": {
                "disposition_mix": [],
                "bed_occupancy_analysis_by_case_mix": [],
            },
            "message": "No data available"
        }

    return {
        "upload_id": effective_id,
        "patient_flow_analysis": {
            "disposition_mix": service.get_disposition_mix(effective_id),
            "bed_occupancy_analysis_by_case_mix": service.get_bed_occupancy_analysis_by_case_mix(effective_id),
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


@router.get("/p90-total-ed-stay-time-volume-correlations")
async def get_p90_total_ed_stay_time_volume_correlations():
    return service.get_p90_total_ed_stay_time_volume_correlations()

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
