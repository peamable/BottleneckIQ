from datetime import datetime
import logging
import os
import shutil
import traceback

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from sqlalchemy import text

from app.config import settings
from app.core.database import engine
from app.services.aggregation import insert_duration_event
from app.services.analytics import (
    calculate_and_store_bottleneck_status_counts,
    calculate_and_store_metrics,
    generate_hourly_aggregates,
)
from app.services.data_cleaning import SchemaValidationError, clean_to_ed_stay_and_stay_info
from app.services.data_ingestion import load_to_staging, process_staged_batch
from app.services.data_validation import validate_batch
from app.services.upload_history import create_upload_history, update_upload_status
from app.services.upload_progress import get_upload_job, init_upload_job, set_job_state, update_stage

logger = logging.getLogger(__name__)
router = APIRouter()
UPLOAD_DIR = settings["UPLOAD_DIR"]


def _build_default_period() -> tuple[datetime, datetime, str, str]:
    now = datetime.now()
    period_start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if now.month == 12:
        period_end_dt = period_start_dt.replace(year=now.year + 1, month=1, day=1)
    else:
        period_end_dt = period_start_dt.replace(month=now.month + 1, day=1)
    period_end_dt = period_end_dt.replace(day=1, hour=23, minute=59, second=59) - __import__("datetime").timedelta(days=1)

    return period_start_dt, period_end_dt, period_start_dt.isoformat(), period_end_dt.isoformat()


def _build_pipeline_summary(upload_id: int, result: dict | None = None, event_log_rows_affected: int = 0) -> dict:
    skipped_rows = result.get("skipped_rows", []) if result else []
    skipped_total = sum(int(item.get("rows_deleted", 0)) for item in skipped_rows)

    with engine.begin() as conn:
        ed_stay_events = conn.execute(
            text("SELECT COUNT(*) FROM ed_stay WHERE upload_id = :uid"),
            {"uid": upload_id},
        ).scalar() or 0
        stay_info_count = conn.execute(
            text("SELECT COUNT(*) FROM stay_info WHERE upload_id = :uid"),
            {"uid": upload_id},
        ).scalar() or 0

    return {
        "ed_events_inserted": int(ed_stay_events),
        "stay_ids_inserted": int(stay_info_count),
        "stay_ids_summarized": int(event_log_rows_affected),
        "rows_skipped_or_removed": int(skipped_total),
    }


def _mark_job_failed(upload_id: int, stage_key: str, message: str, *, allow_skip: bool = False, validation_issues=None, missing_fields=None) -> None:
    update_stage(upload_id, stage_key, "failed", message)
    stage_order = ["file_saved", "cleaning", "staging", "validation", "ingestion", "aggregation", "analytics"]
    failed_index = stage_order.index(stage_key) if stage_key in stage_order else -1
    for later_stage in stage_order[failed_index + 1:]:
        update_stage(upload_id, later_stage, "pending")
    needs_user_action = bool(allow_skip or validation_issues or missing_fields)
    update_upload_status(upload_id, "action_required" if needs_user_action else "failed")
    set_job_state(
        upload_id,
        status="action_required" if needs_user_action else "failed",
        message=message,
        allow_skip=allow_skip,
        validation_issues=validation_issues or [],
        missing_fields=missing_fields or [],
    )


def _continue_after_staging(upload_id: int, batch_id: str, skip_invalid_rows: bool) -> None:
    update_stage(upload_id, "validation", "in_progress", "Validating staged data.")
    result = process_staged_batch(
        batch_id=batch_id,
        upload_id=upload_id,
        skip_invalid_rows=skip_invalid_rows,
        cleanup=True,
    )

    if not result["ok"]:
        validation_issues = result.get("validation_issues", [])
        allow_skip = bool(validation_issues) and all(issue.get("skippable") for issue in validation_issues)
        _mark_job_failed(
            upload_id,
            "validation",
            result["errors"][0] if result["errors"] else "Validation failed.",
            allow_skip=allow_skip,
            validation_issues=validation_issues,
        )
        return

    update_stage(upload_id, "validation", "completed", "Validation completed.")
    update_stage(upload_id, "ingestion", "completed", "Data moved into final tables.")
    set_job_state(
        upload_id,
        status="processing",
        allow_skip=False,
        validation_issues=[],
        missing_fields=[],
        skipped_rows=result.get("skipped_rows", []),
        processed_with_skips=result.get("processed_with_skips", False),
        summary_report=_build_pipeline_summary(upload_id, result=result, event_log_rows_affected=0),
        message="Core ingestion completed.",
    )

    update_stage(upload_id, "aggregation", "in_progress", "Building event log records.")
    affected = insert_duration_event(upload_id=upload_id)
    update_stage(upload_id, "aggregation", "completed", f"Aggregation completed for {affected} stays.")

    update_stage(upload_id, "analytics", "in_progress", "Calculating metrics and hourly summaries.")
    try:
        metrics_result = calculate_and_store_metrics(upload_id=upload_id, batch_id=batch_id)
        hourly_result = generate_hourly_aggregates(upload_id=upload_id)
        bottleneck_result = calculate_and_store_bottleneck_status_counts(upload_id=upload_id, batch_id=batch_id)
    except Exception as e:
        logger.warning(f"Metrics failed: {e}")
        update_stage(upload_id, "analytics", "failed", f"Analytics failed: {e}")
        update_upload_status(upload_id, "completed")
        set_job_state(
            upload_id,
            status="completed",
            message=f"Upload completed, but analytics had issues: {e}",
            metrics_status=f"Metrics failed: {e}",
            hourly_aggregates_status="Not run",
            summary_report=_build_pipeline_summary(upload_id, result=result, event_log_rows_affected=int(affected)),
        )
        return

    update_stage(upload_id, "analytics", "completed", "Metrics and hourly summaries completed.")
    update_upload_status(upload_id, "completed")
    set_job_state(
        upload_id,
        status="completed",
        message="Upload completed successfully.",
        metrics_status=metrics_result,
        hourly_aggregates_status=hourly_result,
        bottleneck_status_counts_status=bottleneck_result,
        event_log_rows_affected=int(affected),
        summary_report=_build_pipeline_summary(upload_id, result=result, event_log_rows_affected=int(affected)),
    )


def _run_upload_pipeline(upload_id: int, batch_id: str, file_path: str) -> None:
    try:
        update_stage(upload_id, "file_saved", "completed", "Raw CSV saved.")

        update_stage(upload_id, "cleaning", "in_progress", "Cleaning and splitting raw CSV.")
        df_raw = pd.read_csv(file_path)
        try:
            df_ed_stay, df_stay_info = clean_to_ed_stay_and_stay_info(df_raw)
        except SchemaValidationError as e:
            missing_fields = list(dict.fromkeys(e.missing_ed_stay + e.missing_stay_info))
            _mark_job_failed(
                upload_id,
                "cleaning",
                str(e),
                allow_skip=False,
                missing_fields=missing_fields,
            )
            return
        except ValueError as e:
            _mark_job_failed(upload_id, "cleaning", str(e))
            return

        update_stage(upload_id, "cleaning", "completed", "Data cleaning completed.")

        if df_stay_info is None or df_stay_info.empty:
            _mark_job_failed(upload_id, "cleaning", "stay_info dataframe is empty after cleaning.")
            return

        update_stage(upload_id, "staging", "in_progress", "Loading cleaned data into staging tables.")
        load_to_staging(df_ed_stay, df_stay_info, batch_id, upload_id=upload_id)
        update_stage(upload_id, "staging", "completed", "Staging tables populated.")
        update_stage(upload_id, "ingestion", "in_progress", "Waiting for validation to complete.")

        validation_issues = validate_batch(batch_id)
        if validation_issues:
            allow_skip = all(issue.get("skippable") for issue in validation_issues)
            _mark_job_failed(
                upload_id,
                "validation",
                validation_issues[0]["message"],
                allow_skip=allow_skip,
                validation_issues=validation_issues,
            )
            return

        _continue_after_staging(upload_id, batch_id, skip_invalid_rows=False)

    except Exception as e:
        update_upload_status(upload_id, "failed")
        set_job_state(
            upload_id,
            status="failed",
            message="Internal server error.",
            allow_skip=False,
        )
        logger.error(f"Upload failed: {str(e)}\n{traceback.format_exc()}")


@router.post("/upload")
async def upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    upload_id = None
    batch_id = None

    try:
        period_start_dt, period_end_dt, period_start, period_end = _build_default_period()
        logger.info(f"Upload started: period_start={period_start}, period_end={period_end}")

        upload_id, batch_id = create_upload_history(period_start, period_end)
        file_path = os.path.join(UPLOAD_DIR, f"raw_{batch_id}.csv")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        init_upload_job(upload_id, batch_id, file_path)
        set_job_state(upload_id, message="Upload received. Starting pipeline.")
        background_tasks.add_task(_run_upload_pipeline, upload_id, batch_id, file_path)

        return {
            "status": "accepted",
            "upload_id": upload_id,
            "batch_id": batch_id,
            "saved_path": file_path,
            "period_start": period_start,
            "period_end": period_end,
        }
    except HTTPException:
        raise
    except Exception as e:
        if upload_id is not None:
            try:
                update_upload_status(upload_id, "failed")
            except Exception as status_err:
                logger.error(f"Failed to update upload status: {status_err}")

        logger.error(f"Upload failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.get("/upload-status/{upload_id}")
async def get_upload_status(upload_id: int):
    job = get_upload_job(upload_id)
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found.")
    return job


@router.post("/upload/{upload_id}/process-anyway")
async def process_anyway(upload_id: int, background_tasks: BackgroundTasks):
    job = get_upload_job(upload_id)
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found.")

    if not job.get("allow_skip"):
        raise HTTPException(status_code=400, detail="This upload cannot skip invalid rows.")

    set_job_state(
        upload_id,
        status="processing",
        message="Skipping invalid rows and resuming pipeline.",
        allow_skip=False,
        validation_issues=[],
    )
    background_tasks.add_task(_continue_after_staging, upload_id, job["batch_id"], True)
    return {"status": "accepted", "upload_id": upload_id, "batch_id": job["batch_id"]}
