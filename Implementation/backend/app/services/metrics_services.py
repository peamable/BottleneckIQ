from typing import Optional, List, Dict, Any
from sqlalchemy import text
import json
from app.core.database import engine

def get_latest_upload_id() -> Optional[int]:
    """Helper to find the most recent successful upload ID."""
    query = text("""
        SELECT upload_id FROM upload_history 
        WHERE status = 'completed' 
        ORDER BY upload_id DESC LIMIT 1
    """)
    with engine.connect() as conn:
        result = conn.execute(query).mappings().first()
        return result["upload_id"] if result else None
    

# Overall Avg Stay time per activity, and overall total stay time
def get_metrics_data(upload_id: int, batch_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches and normalizes metrics for a specific ID."""
    query_str = "SELECT * FROM metrics WHERE upload_id = :upload_id"
    params = {"upload_id": upload_id}
    
    if batch_id:
        query_str += " AND batch_id = :batch_id"
        params["batch_id"] = batch_id
        
    query = text(query_str + " ORDER BY metric_name")
    
    with engine.connect() as conn:
        rows = conn.execute(query, params).mappings().all()

    normalized_rows = []
    for row in rows:
        row_dict = dict(row)
        # Handle the JSON string conversion safely
        acuity_val = row_dict.get("stay_time_per_acuity")
        if isinstance(acuity_val, str):
            try:
                row_dict["stay_time_per_acuity"] = json.loads(acuity_val)
            except json.JSONDecodeError:
                row_dict["stay_time_per_acuity"] = {}
        normalized_rows.append(row_dict)
    return normalized_rows

# Acuity Benchmarking Reference Data
ACUITY_REFERENCE = {
    1: {"name": "Level 1 (Resuscitation)", "ref_avg": 195, "color": "#2563eb"},
    2: {"name": "Level 2 (Emergent)", "ref_avg": 255, "color": "#ef4444"},
    3: {"name": "Level 3 (Urgent)", "ref_avg": 304, "color": "#f59e0b"},
    4: {"name": "Level 4 (Less Urgent)", "ref_avg": 193, "color": "#10b981"},
    5: {"name": "Level 5 (Non-Urgent)", "ref_avg": 98, "color": "#94a3b8"},
}

def get_avg_stay_time_by_acuity(upload_id: int) -> List[Dict[str, Any]]:
    query = text("""
        SELECT
            s.scale_level AS acuity_level,
            ROUND(AVG(t.total_ed_stay_time), 0) AS dept_avg
        FROM (
            SELECT
                e.stay_id,
                e.total_ed_stay_time
            FROM event_log e
            WHERE e.upload_id = :upload_id
            GROUP BY e.stay_id
        ) t
        JOIN stay_info s
            ON t.stay_id = s.stay_id
           AND s.upload_id = :upload_id
        WHERE s.scale_level IS NOT NULL
        GROUP BY s.scale_level
        ORDER BY s.scale_level
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    return [dict(row) for row in rows]

def build_acuity_benchmarks(upload_id: int) -> Dict[str, Any]:
    rows = get_avg_stay_time_by_acuity(upload_id)
    dept_map = {int(row["acuity_level"]): int(row["dept_avg"]) for row in rows}

    benchmarks = []
    for level, ref_data in ACUITY_REFERENCE.items():
        ref_avg = ref_data["ref_avg"]
        dept_avg = dept_map.get(level, 0)
        diff = dept_avg - ref_avg

        benchmarks.append({
            "name": ref_data["name"],
            "ref_esi_avg": f"{ref_avg}m",
            "dept_avg": f"{dept_avg}m",
            "diff": f"{diff:+}m",
            "type": "good" if diff <= 0 else "warning",
            "color": ref_data["color"]
        })

    return {"acuity_benchmarks": benchmarks}
