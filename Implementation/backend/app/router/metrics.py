from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services import metrics_services as service
from app.services.analytics import (
    bottleneck_analysis,
    calculate_and_store_bottleneck_status_counts,
    get_bottleneck_status_counts,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _pluralize(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return singular
    return plural or f"{singular}s"


def _format_bottleneck_summary(upload_id: int) -> dict:
    stored_status_counts = get_bottleneck_status_counts(upload_id)
    raw_message = None

    if not stored_status_counts:
        raw_result = bottleneck_analysis(upload_id=upload_id)
        stored_status_counts = raw_result.get("status_counts", [])
        raw_message = raw_result.get("message")

    if raw_message and not stored_status_counts:
        return {
            "overall_status": "No Data",
            "banner_message": raw_message,
            "stages": [],
        }

    stage_map = {}
    for row in stored_status_counts:
        stage_name = row["stage"]
        stage_entry = stage_map.setdefault(stage_name, {
            "stage": stage_name,
            "status": "Normal",
            "bottleneck_count": 0,
            "needs_improvement_count": 0,
            "normal_count": 0,
            "no_data_count": 0,
            "no_threshold_count": 0,
        })

        status = row["status"]
        count = int(row["patient_count"])
        if status == "Bottleneck":
            stage_entry["bottleneck_count"] = count
        elif status == "Needs Improvement":
            stage_entry["needs_improvement_count"] = count
        elif status == "Normal":
            stage_entry["normal_count"] = count
        elif status == "No Data":
            stage_entry["no_data_count"] = count
        elif status == "No Threshold":
            stage_entry["no_threshold_count"] = count

    formatted_stages = []
    for stage_name, stage_entry in stage_map.items():
        if stage_entry["bottleneck_count"] > 0:
            stage_entry["status"] = "Bottleneck"
        elif stage_entry["needs_improvement_count"] > 0:
            stage_entry["status"] = "Needs Improvement"
        elif stage_entry["normal_count"] > 0:
            stage_entry["status"] = "Normal"
        elif stage_entry["no_data_count"] > 0:
            stage_entry["status"] = "No Data"
        else:
            stage_entry["status"] = "No Threshold"

        if stage_entry["status"] == "No Threshold":
            continue

        formatted_stages.append({
            "stage": stage_name,
            "status": stage_entry["status"],
            "bottleneck_count": stage_entry["bottleneck_count"],
            "needs_improvement_count": stage_entry["needs_improvement_count"],
            "normal_count": stage_entry["normal_count"],
        })

    bottleneck_stage_count = sum(1 for stage in formatted_stages if stage["status"] == "Bottleneck")
    needs_stage_count = sum(1 for stage in formatted_stages if stage["status"] == "Needs Improvement")

    if bottleneck_stage_count > 0:
        overall_status = "Bottleneck"
    elif needs_stage_count > 0:
        overall_status = "Needs Improvement"
    elif formatted_stages:
        overall_status = "Normal"
    else:
        overall_status = "No Data"

    if overall_status == "Bottleneck" and needs_stage_count > 0:
        banner_message = (
            f"Bottleneck detected in {bottleneck_stage_count} "
            f"{_pluralize(bottleneck_stage_count, 'stage')}. "
            f"Additional {needs_stage_count} "
            f"{_pluralize(needs_stage_count, 'stage')} need improvement."
        )
    elif overall_status == "Bottleneck":
        banner_message = (
            f"Bottleneck detected in {bottleneck_stage_count} "
            f"{_pluralize(bottleneck_stage_count, 'stage')}."
        )
    elif overall_status == "Needs Improvement":
        banner_message = (
            f"No bottlenecks detected. {needs_stage_count} "
            f"{_pluralize(needs_stage_count, 'stage')} need improvement."
        )
    elif overall_status == "Normal":
        banner_message = "All monitored stages are within normal thresholds."
    else:
        banner_message = "No bottleneck data available."

    return {
        "overall_status": overall_status,
        "banner_message": banner_message,
        "stages": formatted_stages,
    }

# @router.get("/dashboard")
# async def get_dashboard_data(
#     upload_id: Optional[int] = Query(None)
# ):
#     # Use service to find ID if not provided
#     effective_id = upload_id or service.get_latest_upload_id()

#     if effective_id is None:
#         # Return a 200 with empty data instead of a 404/422 
#         # to keep the frontend from crashing
#         return {"upload_id": None, "metrics": [], "message": "No data available"}
        
#     rows = service.get_metrics_data(effective_id)
    
#     return {
#         "upload_id": effective_id,
#         "metrics": rows
#     }
@router.get("/dashboard-horizon")
async def get_horizon(upload_id: Optional[int] = Query(None)):
    return service.get_dashboard_horizon(upload_id)

@router.get("/dashboard")
async def get_summary(
    upload_id: Optional[int] = Query(None)
):

    effective_id = upload_id or service.get_latest_upload_id()
    
    if effective_id is None:
         # Return a 200 with empty data instead of a 404/422 
         # to keep the frontend from crashing
         return {"upload_id": None, "summary": {}, "message": "No data available"}
    
    summary_data = service.get_dashboard_summary(effective_id)
    
    return {
        "upload_id": effective_id,
        "summary": summary_data
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

@router.get("/performance-trend")
async def get_performance_trend(
    lookback: int = Query(10, description="Number of past uploads to include")
):
    """
    Endpoint for the Line Chart.
    Returns a list of historical metrics labeled by Upload Date and ID.
    """
    # Call the service we just built
    trend_data = service.get_performance_trend_data(lookback=lookback)
    
    if not trend_data:
        # Return empty list instead of 404 to keep Recharts from crashing
        return {"trend_chart": []}

    return {"trend_chart": trend_data}


@router.get("/bottleneck-analysis")
async def get_bottleneck_analysis(
    upload_id: Optional[int] = Query(None)
):
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        return {
            "overall_status": "No Data",
            "banner_message": "No data available",
            "stages": [],
        }

    return _format_bottleneck_summary(effective_id)


@router.get("/bottleneck-status-counts")
async def fetch_bottleneck_status_counts(
    upload_id: Optional[int] = Query(None),
    refresh: bool = Query(False, description="Recalculate and refresh stored counts before returning them")
):
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        return {
            "upload_id": None,
            "status_counts": [],
            "message": "No data available"
        }

    if refresh:
        refresh_message = calculate_and_store_bottleneck_status_counts(upload_id=effective_id)
    else:
        refresh_message = None

    rows = get_bottleneck_status_counts(effective_id)
    if not rows:
        raw_result = bottleneck_analysis(upload_id=effective_id)
        rows = raw_result.get("status_counts", [])
        refresh_message = refresh_message or raw_result.get("message")

    return {
        "upload_id": effective_id,
        "status_counts": rows,
        "message": refresh_message,
    }


@router.get("/bottleneck-test")
async def get_bottleneck_test(
    upload_id: Optional[int] = Query(None)
):
    effective_id = upload_id or service.get_latest_upload_id()

    if effective_id is None:
        return {
            "upload_id": None,
            "message": "No data available"
        }

    return bottleneck_analysis(upload_id=effective_id)
