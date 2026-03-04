from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import pandas as pd
import os  
import shutil
from app.config import settings 
from app.services.data_cleaning import clean_to_ed_stay_and_stay_info
from app.services.data_ingestion import process_batch
from app.services.aggregation import insert_duration_event

router = APIRouter()

# Set the path for the upload raw data
UPLOAD_DIR = settings["UPLOAD_DIR"]

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Save the raw file in the file path
    file_path = os.path.join(UPLOAD_DIR, f"raw_{batch_id}.csv")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save raw data: {e}")

    # 2. read the raw file from the file path
    try:
        df_raw = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read saved CSV: {e}")

    # 3. do  raw data cleaning and ingestion the cleaned data in the tables
    try:
        df_ed_stay, df_stay_info = clean_to_ed_stay_and_stay_info(df_raw)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = process_batch(df_ed_stay, df_stay_info, batch_id=batch_id, cleanup=True)

    if not result["ok"]:
        raise HTTPException(status_code=400, detail={"batch_id": batch_id, "errors": result["errors"]})

    # 4. do duration calculation and insert to the event_log
    try:
        affected = insert_duration_event()
    except Exception as e:
        raise HTTPException(status_code=500, detail={"batch_id": batch_id, "errors": [f"Aggregation failed: {e}"]})

    return {
        "status": "success",
        "batch_id": batch_id,
        "saved_path": file_path, 
        "rows_ed_stay": int(len(df_ed_stay)),
        "rows_stay_info": int(len(df_stay_info)) if df_stay_info is not None else 0,
        "event_log_rows_affected": int(affected),
    }