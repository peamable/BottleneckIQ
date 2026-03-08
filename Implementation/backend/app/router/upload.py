from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import pandas as pd
import os  
import shutil
import traceback
import logging
from app.config import settings 
from app.services.data_cleaning import clean_to_ed_stay_and_stay_info
from app.services.data_ingestion import process_batch
from app.services.aggregation import insert_duration_event
from app.services.analytics import calculate_and_store_metrics
from app.services.upload_history import create_upload_history, update_upload_status # New Import 
from app.services.analytics import calculate_and_store_metrics # New Import

# use  logger for the upload history 
logger = logging.getLogger(__name__)
router = APIRouter()
UPLOAD_DIR = settings["UPLOAD_DIR"]

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    # to change after how to determine period, for now we will just use current month as default
    try:
        # Generate default period: current month start to end
        now = datetime.utcnow()
        period_start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Last day of current month
        if now.month == 12:
            period_end_dt = period_start_dt.replace(year=now.year + 1, month=1, day=1)
        else:
            period_end_dt = period_start_dt.replace(month=now.month + 1, day=1)
        period_end_dt = period_end_dt.replace(day=1, hour=23, minute=59, second=59) - __import__('datetime').timedelta(days=1)
        
        # Convert to ISO strings
        period_start = period_start_dt.isoformat()
        period_end = period_end_dt.isoformat()
        
        logger.info(f"Upload started: period_start={period_start}, period_end={period_end}")

        # Create upload history
        upload_id, batch_id = create_upload_history(period_start, period_end)
        logger.info(f"Upload history created: upload_id={upload_id}, batch_id={batch_id}")

        # Save the raw file
        file_path = os.path.join(UPLOAD_DIR, f"raw_{batch_id}.csv")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Raw file saved: {file_path}")

        # Read and clean data
        df_raw = pd.read_csv(file_path)
        df_ed_stay, df_stay_info = clean_to_ed_stay_and_stay_info(df_raw)
        logger.info(f"Data cleaned: ed_stay={len(df_ed_stay)}, stay_info={len(df_stay_info) if df_stay_info is not None else 0}")

        # Process batch
        result = process_batch(
            df_ed_stay, 
            df_stay_info, 
            period_start_dt,
            period_end_dt
        )
        logger.info(f"Batch processed: {result}")

        if not result["ok"]:
            update_upload_status(upload_id, "failed")
            raise HTTPException(status_code=400, detail={"upload_id": upload_id, "batch_id": batch_id, "errors": result["errors"]})

        # Aggregation
        affected = insert_duration_event()
        logger.info(f"Duration events inserted: {affected}")

        # Metrics
        try:
            metrics_result = calculate_and_store_metrics()
        except Exception as e:
            logger.warning(f"Metrics failed: {e}")
            metrics_result = f"Metrics failed: {e}"

        update_upload_status(upload_id, "completed")
        logger.info(f"Upload completed: upload_id={upload_id}")

        return {
            "status": "success",
            "upload_id": upload_id,
            "batch_id": batch_id,
            "saved_path": file_path,
            "period_start": period_start,
            "period_end": period_end,
            "rows_ed_stay": int(len(df_ed_stay)),
            "rows_stay_info": int(len(df_stay_info)) if df_stay_info is not None else 0,
            "event_log_rows_affected": int(affected),
            "metrics_status": metrics_result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
