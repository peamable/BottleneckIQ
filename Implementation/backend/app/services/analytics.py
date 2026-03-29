import pandas as pd
import numpy as np
from sqlalchemy import text
import json
from app.core.database import engine
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor



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
    metric_columns = [
        col for col in df.columns
        if col.startswith("time_to") or col == "total_ed_stay_time"
    ]

    for col in metric_columns:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue

        avg_val = round(float(series.mean()), 2)
        p75_val = round(float(np.percentile(series, 75)), 2)
        p90_val = round(float(np.percentile(series, 90)), 2)
        p99_val = round(float(np.percentile(series, 99)), 2)
        min_val = round(float(series.min()), 2)
        max_val = round(float(series.max()), 2)

        acuity_df = df[["scale_level", col]].copy()
        acuity_df[col] = pd.to_numeric(acuity_df[col], errors="coerce")
        acuity_group = acuity_df.groupby("scale_level")[col].mean().to_dict()
        clean_acuity = {
            str(int(k)): round(float(v), 2)
            for k, v in acuity_group.items()
            if pd.notnull(v)
        }

        metrics_to_insert.append({
            "metric_name": col,
            "avg_value": avg_val,
            "p90_value": p90_val,
            "p75_value": p75_val,
            "p99_value": p99_val,
            "min_value": min_val,
            "max_value": max_val,
            "stay_time_per_acuity": json.dumps(clean_acuity),
            "upload_id": upload_id,
        })

    if not metrics_to_insert:
        return f"No eligible metric columns found for upload_id={upload_id}."

    # 2. Database Insert
    insert_sql = text("""
        INSERT INTO metrics (
            metric_name, avg_value, p90_value, p75_value, p99_value, 
            min_value, max_value, stay_time_per_acuity, upload_id
        ) VALUES (
            :metric_name, :avg_value, :p90_value, :p75_value, :p99_value, 
            :min_value, :max_value, :stay_time_per_acuity, :upload_id
        )
        ON DUPLICATE KEY UPDATE
            avg_value = VALUES(avg_value),
            p90_value = VALUES(p90_value),
            p75_value = VALUES(p75_value),
            p99_value = VALUES(p99_value),
            min_value = VALUES(min_value),
            max_value = VALUES(max_value),
            stay_time_per_acuity = VALUES(stay_time_per_acuity)
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
        FROM ed_stay s
        JOIN stay_info si
          ON s.stay_id = si.stay_id
         AND s.upload_id = si.upload_id
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
        with engine.begin() as conn:
            # Rebuilding the upload should replace this upload's existing hourly summary.
            conn.execute(text("DELETE FROM temporal_summary WHERE upload_id = :uid"), {"uid": upload_id})

        final_df.to_sql('temporal_summary', engine, if_exists='append', index=False)
        return f"Successfully generated tomporal summary. Rows: {len(final_df)}"
    except Exception as e:
        return f"Error: {e}"


def train_volume_model():
    """
    Fetches historical data from temporal_summary, prepares lagged features,
    trains a Random Forest model for volume prediction, and saves the pipeline.
    """
    query = text("SELECT * FROM temporal_summary ORDER BY upload_id, day_of_week, hour_of_day")
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        
    if df.empty:
        return "No data available to train the model."
        
    # 1. Bucket by 4-hour time windows
    df['hour_of_day'] = pd.to_numeric(df['hour_of_day'], errors='coerce')
    df['time_window'] = df['hour_of_day'] // 4
    
    data_binned = df.groupby(['upload_id', 'day_of_week', 'time_window'], as_index=False).agg({
        'total_volume': 'sum',
        'acuity_1': 'sum',
        'acuity_2': 'sum',
        'acuity_3': 'sum',
        'acuity_4': 'sum',
        'acuity_5': 'sum',
        'month_of_year': 'first'
    })
    
    # 2. Feature Engineering: Lagging
    data_binned['prev_volume'] = data_binned.groupby('upload_id')['total_volume'].shift(1)
    for i in range(1, 6):
        data_binned[f'prev_acuity_{i}'] = data_binned.groupby('upload_id')[f'acuity_{i}'].shift(1)
        
    data_clean = data_binned.dropna().copy()
    
    if data_clean.empty:
        return "Not enough data to create lagged features for training."

    # 3. Define features and target
    categorical_features = ['day_of_week', 'time_window']
    numeric_features = [
        'month_of_year', 'prev_volume', 
        'prev_acuity_1', 'prev_acuity_2', 'prev_acuity_3', 'prev_acuity_4', 'prev_acuity_5'
    ]
    
    X = data_clean[categorical_features + numeric_features]
    y = data_clean['total_volume']
    
    # 4. Preprocessing Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
            ('num', StandardScaler(), numeric_features)
        ]
    )
    
    # 5. Pipeline with Random Forest
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    # 6. Train Model
    pipeline.fit(X, y)
    
    # 7. Export Model
    export_path = os.path.join(os.path.dirname(__file__), 'volume_prediction_pipeline.joblib')
    joblib.dump(pipeline, export_path)
    
    r2 = pipeline.score(X, y)
    return f"Model successfully trained and saved to '{export_path}'. R2 Score: {r2:.4f}"


def predict_next_volume(upload_id: int):
    """
    Predicts the patient volume for the next 4-hour window using the most recent 
    window's data from the given upload_id.
    """
    model_path = os.path.join(os.path.dirname(__file__), 'volume_prediction_pipeline.joblib')
    if not os.path.exists(model_path):
        return {"error": "Prediction model not found. Please train it first."}
        
    pipeline = joblib.load(model_path)
    
    query = text("SELECT * FROM temporal_summary WHERE upload_id = :uid")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"uid": upload_id})
        
    if df.empty:
        return {"error": f"No data found for upload_id={upload_id}"}
        
    df['hour_of_day'] = pd.to_numeric(df['hour_of_day'], errors='coerce')
    df['time_window'] = df['hour_of_day'] // 4
    
    data_binned = df.groupby(['day_of_week', 'time_window'], as_index=False).agg({
        'total_volume': 'sum',
        'acuity_1': 'sum',
        'acuity_2': 'sum',
        'acuity_3': 'sum',
        'acuity_4': 'sum',
        'acuity_5': 'sum',
        'month_of_year': 'first'
    })
    
    data_binned = data_binned.sort_values(by=['day_of_week', 'time_window'])
    last_window = data_binned.iloc[-1]
    
    current_day = last_window['day_of_week']
    current_window = last_window['time_window']
    current_month = last_window['month_of_year']
    
    next_window = (current_window + 1) % 6
    next_day = current_day if next_window > 0 else (current_day % 7) + 1
    
    input_data = pd.DataFrame([{
        'day_of_week': next_day,
        'time_window': next_window,
        'month_of_year': current_month,
        'prev_volume': last_window['total_volume'],
        'prev_acuity_1': last_window['acuity_1'],
        'prev_acuity_2': last_window['acuity_2'],
        'prev_acuity_3': last_window['acuity_3'],
        'prev_acuity_4': last_window['acuity_4'],
        'prev_acuity_5': last_window['acuity_5']
    }])
    
    predicted_volume = pipeline.predict(input_data)[0]
    
    return {
        "current_window": int(current_window),
        "target_window": int(next_window),
        "target_day_of_week": int(next_day),
        "predicted_volume": round(predicted_volume)
    }

if __name__ == "__main__":
   # print(calculate_and_store_metrics())
    print(calculate_and_store_metrics(upload_id=1))
    print(generate_hourly_aggregates(upload_id=1))
