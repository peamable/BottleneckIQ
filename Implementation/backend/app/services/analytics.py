import pandas as pd
import numpy as np
from sqlalchemy import text
import json
from app.core.database import engine
from datetime import datetime



# this feeds the metrics table

def calculate_and_store_metrics():
    # 1. Fetch data from joined tables
    query = """
        SELECT el.*, si.scale_level
        FROM event_log el
        JOIN stay_info si ON el.stay_id = si.stay_id
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    if df.empty:
        return "No data found to calculate metrics."

    metrics_to_insert = []
    
    # Hardcoded for now per your plan
    HARDCODED_UPLOAD_ID = 1 

    for col in df.columns:
        if col.startswith('time_to') or col == 'total_ed_stay_time':
            series = df[col].dropna()
            
            if not series.empty:
                # Calculate stats - keeping as floats for precision
                avg_val = round(float(series.mean()), 2)
                p75_val = round(float(np.percentile(series, 75)), 2)
                p90_val = round(float(np.percentile(series, 90)), 2)
                p99_val = round(float(np.percentile(series, 99)), 2)
                min_val = round(float(series.min()), 2)
                max_val = round(float(series.max()), 2)

                # Acuity Breakdown (JSON)
                acuity_group = df.groupby('scale_level')[col].mean().to_dict()
                # Ensure we handle potential NaN values in the breakdown
                clean_acuity = {
                    str(int(k)): round(float(v) , 2)
                    for k, v in acuity_group.items() 
                    if pd.notnull(v)
                }

                metrics_to_insert.append({
                    'metric_name': col,
                    'avg_value': avg_val,
                    'p90_value': p90_val,
                    'p75_value': p75_val,
                    'p99_value': p99_val,
                    'min_value': min_val,
                    'max_value': max_val,
                    'stay_time_per_acuity': json.dumps(clean_acuity),
                    'upload_id': HARDCODED_UPLOAD_ID ## to be changed
                })

    # 2. Database Insert
    insert_sql = text("""
        INSERT INTO metrics (
            metric_name, avg_value, p90_value, p75_value, p99_value, 
            min_value, max_value, stay_time_per_acuity, upload_id
        ) VALUES (
            :metric_name, :avg_value, :p90_value, :p75_value, :p99_value, 
            :min_value, :max_value, :stay_time_per_acuity, :upload_id
        )
    """)

    try:
        with engine.begin() as conn:
            conn.execute(insert_sql, metrics_to_insert)
        return f"Successfully populated metrics for Upload ID {HARDCODED_UPLOAD_ID}."
    except Exception as e:
        return f"Database Error: {e}"

if __name__ == "__main__":
    print(calculate_and_store_metrics())