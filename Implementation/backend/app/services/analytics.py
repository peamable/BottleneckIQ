import pandas as pd
import numpy as np
from sqlalchemy import text
import json
from app.core.database import engine



# this feeds the metrics table

#def calculate_and_store_metrics():
def calculate_and_store_metrics(upload_id: int, batch_id: str | None = None):
    """
    Re-calculate whatever dashboard numbers you need and persist them.
    `batch_id`/`upload_id` are purely for traceability; you can also use them
    in the SQL to restrict the input rows.
    """
    # 1. Fetch data from joined tables
    query = """
        SELECT el.*, si.scale_level
        FROM event_log el
        JOIN stay_info si ON el.stay_id = si.stay_id
            AND el.upload_id = si.upload_id
        WHERE el.upload_id = :upload_id
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn,params={
            "upload_id": upload_id
        })

    if df.empty:
        return f"No data found to calculate metrics for upload_id={upload_id}."

    metrics_to_insert = []
    
    for col in df.columns:
        if col.startswith('time_to') or col == 'total_ed_stay':
            series = df[col].dropna()
            
            if not series.empty:
                # Calculate stats - keeping as floats for precision
                avg_val = round(float(series.mean()), 2)
                p75_val = round(float(np.percentile(series, 75)), 2)
                p90_val = round(float(np.percentile(series, 90)), 2)
                p99_val = round(float(np.percentile(series, 99)), 2)
                min_val = round(float(series.min()), 2)
                max_val = round(float(series.max()), 2)
#     metric_columns = [
#         col for col in df.columns
#         if col.startswith("time_to") or col == "total_ed_stay_time"
#     ]

#     for col in metric_columns:
#         series = pd.to_numeric(df[col], errors="coerce").dropna()
#         if series.empty:
#             continue

        # Calculate stats - keeping as floats for precision
        avg_val = round(float(series.mean()), 2)
        p75_val = round(float(np.percentile(series, 75)), 2)
        p90_val = round(float(np.percentile(series, 90)), 2)
        p99_val = round(float(np.percentile(series, 99)), 2)
        min_val = round(float(series.min()), 2)
        max_val = round(float(series.max()), 2)

                metrics_to_insert.append({
                    'metric_name': col,
                    'avg_value': avg_val,
                    'p90_value': p90_val,
                    'p75_value': p75_val,
                    'p99_value': p99_val,
                    'min_value': min_val,
                    'max_value': max_val,
                    'stay_time_per_acuity': json.dumps(clean_acuity),
                    'upload_id': upload_id
                })
#         # Use the same numeric coercion for the acuity breakdown.
#         acuity_df = df[["scale_level", col]].copy()
#         acuity_df[col] = pd.to_numeric(acuity_df[col], errors="coerce")
#         acuity_group = acuity_df.groupby("scale_level")[col].mean().to_dict()
#         clean_acuity = {
#             str(int(k)): round(float(v), 2)
#             for k, v in acuity_group.items()
#             if pd.notnull(v)
#         }

#         metrics_to_insert.append({
#             'metric_name': col,
#             'avg_value': avg_val,
#             'p90_value': p90_val,
#             'p75_value': p75_val,
#             'p99_value': p99_val,
#             'min_value': min_val,
#             'max_value': max_val,
#             'stay_time_per_acuity': json.dumps(clean_acuity),
#             'upload_id': upload_id
#         })

#     if not metrics_to_insert:
#         return f"No eligible metric columns found for upload_id={upload_id}."

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
            if metrics_to_insert:
                conn.execute(insert_sql, metrics_to_insert)

            # optionally annotate the upload_history row
            # if upload_id is not None:
            #     conn.execute(text("""
            #         UPDATE upload_history
            #         SET metrics_calculated = NOW()
            #         WHERE upload_id = :u
            #     """), {"u": upload_id})

        return f"Successfully populated metrics for Upload ID {upload_id}."
    except Exception as e:
        return f"Database Error: {e}"
    
#             conn.execute(insert_sql, metrics_to_insert)
#         return f"Successfully populated metrics for Upload ID {upload_id}."
    except Exception as e:
        return f"Database Error: {e}"
    
def generate_hourly_aggregates(upload_id: int, batch_id: str | None = None):
    """
    Aggregates volume and acuity into hourly buckets for forecasting.
    Temporal features (month, day, hour) are extracted for pattern analysis.
    """
    # 1. Retrieve Data (Simplified: only need timestamp and acuity)
    query = text("""
        SELECT 
            s.ed_timestamp,
            si.scale_level,
            s.stay_id
        FROM ed_stay_staging s
        JOIN stay_info si ON s.stay_id = si.stay_id
        WHERE s.upload_id = :uid 
          AND s.activity = 'entry'
    """)
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"uid": upload_id})
        
    if df.empty:
        return "No data found for hourly aggregation."

    # 2. Bucket by Hour
    df['timestamp_hour'] = pd.to_datetime(df['ed_timestamp']).dt.floor('h')
    
    # 3. Aggregation: Total Volume
    volume_df = df.groupby('timestamp_hour').agg(
        total_volume=('stay_id', 'count')
    ).reset_index()

    # 4. Pivot Acuity (Clinical Intensity Mix)
    acuity_pivot = df.pivot_table(
        index='timestamp_hour', 
        columns='scale_level', 
        values='stay_id', 
        aggfunc='count', 
        fill_value=0
    )
    
    # Ensure columns 1-5 exist for the bar chart segments
    acuity_pivot = acuity_pivot.reindex(columns=[1, 2, 3, 4, 5], fill_value=0)
    acuity_pivot.columns = [f'acuity_{int(c)}' for c in acuity_pivot.columns]
    
    # Combine Volume and Acuity
    final_df = volume_df.merge(acuity_pivot, on='timestamp_hour', how='left')
    
    # 5. Extract Pattern Attributes (Features for forecasting)
    final_df['month_of_year'] = final_df['timestamp_hour'].dt.month
    # 1=Sun, 2=Mon...
    final_df['day_of_week'] = (final_df['timestamp_hour'].dt.dayofweek + 1) % 7 + 1
    final_df['hour_of_day'] = final_df['timestamp_hour'].dt.hour
    final_df['upload_id'] = upload_id
    
    # 6. Insert into Database
    try:
        final_df.to_sql('temporal_summary', engine, if_exists='append', index=False)
        return f"Successfully generated tomporal summary. Rows: {len(final_df)}"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
   # print(calculate_and_store_metrics())
    print(calculate_and_store_metrics(upload_id=1))
