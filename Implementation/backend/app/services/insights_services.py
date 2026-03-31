import os
import sys
import re
import math
from typing import Optional

import pandas as pd
from sqlalchemy import text

if __name__ == "__main__":
    # Allow direct execution via `python app/services/insights_services.py`.
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

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


def get_temporal_heatmap(upload_id: Optional[int] = None, lookback: int = 3) -> dict:
    """Builds a 7x4 daily heatmap (4x6h slices) for patient volume using temporal_summary from recent uploads."""
    effective_id = upload_id or get_latest_upload_id()
    day_labels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slice_labels = ['Dawn ', 'Morning ', 'Afternoon ', 'Night ']

    if not effective_id:
        return {
            "upload_id": None,
            "day_labels": day_labels,
            "slice_labels": slice_labels,
            "volume_matrix": [[0,0,0,0] for _ in range(7)]
        }

    # Get the last N completed upload IDs to aggregate recent patterns
    recent_uploads_query = text("""
        SELECT upload_id
        FROM upload_history
        WHERE status = 'completed'
        ORDER BY upload_id DESC
        LIMIT :lookback
    """)

    with engine.connect() as conn:
        recent_rows = conn.execute(recent_uploads_query, {"lookback": lookback}).mappings().all()
        recent_upload_ids = [row['upload_id'] for row in recent_rows]

    if not recent_upload_ids:
        return {
            "upload_id": effective_id,
            "day_labels": day_labels,
            "slice_labels": slice_labels,
            "volume_matrix": [[0,0,0,0] for _ in range(7)]
        }

    query = text("""
        SELECT
            ((day_of_week - 1) % 7) AS dow,
            FLOOR(hour_of_day / 6) AS slice,
            AVG(total_volume) AS avg_volume
        FROM temporal_summary
        WHERE upload_id IN :u_ids
        GROUP BY dow, slice
        ORDER BY dow, slice;
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"u_ids": tuple(recent_upload_ids)}).mappings().all()

    volume_matrix = [[0, 0, 0, 0] for _ in range(7)]

    for row in rows:
        dow = int(row['dow']) if row['dow'] is not None else 0
        slice_idx = int(row['slice']) if row['slice'] is not None else 0
        if 0 <= dow <= 6 and 0 <= slice_idx <= 3:
            volume_matrix[dow][slice_idx] = round(float(row['avg_volume'] or 0))

    return {
        "upload_id": effective_id,
        "day_labels": day_labels,
        "slice_labels": slice_labels,
        "volume_matrix": volume_matrix
    }


# disposition mix pie chart visualization
def get_disposition_mix(upload_id: int) -> dict:
    # We query the permanent table 'stay_info'
    # Since we aren't using upload_id yet, we get the distribution of all processed records
    query = text("""
        SELECT
            CASE
                WHEN LOWER(TRIM(disposition)) = 'home' THEN 'Home'
                WHEN LOWER(TRIM(disposition)) = 'admitted' THEN 'Admitted'
                WHEN LOWER(TRIM(disposition)) IN (
                    'eloped',
                    'left without being seen',
                    'left against medical advice',
                    'expired',
                    'transfer',
                    'other'
                ) THEN 'Other'
                ELSE 'Other'
            END AS disposition_group,
            COUNT(DISTINCT stay_id) AS cnt,
            ROUND(
                COUNT(DISTINCT stay_id) * 100.0
                / SUM(COUNT(DISTINCT stay_id)) OVER (),
                2
            ) AS pct
        FROM stay_info
        WHERE disposition IS NOT NULL
        AND disposition <> ''
        AND upload_id = :upload_id
        GROUP BY disposition_group
        ORDER BY pct DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    disposition_mix = [
        {
            "type": r["disposition_group"],
            "count": int(r["cnt"]),
            "percentage": float(round(r["pct"], 2))
        }
        for r in rows
    ]

    return disposition_mix

# chiefcomplaint top 5 bar chart visualization
def get_top_chief_complaints(upload_id: int) -> dict:
    query = text("""
        WITH stay_duration AS (
            SELECT
                stay_id,
                upload_id,
                MAX(total_ed_stay_time) AS total_ed_stay_time
            FROM event_log
            WHERE total_ed_stay_time IS NOT NULL
              AND upload_id = :upload_id
            GROUP BY stay_id, upload_id
        )
        SELECT
            si.chiefcomplaint,
            COUNT(*) AS cnt,
            AVG(sd.total_ed_stay_time) AS avg_total_ed_stay_time
        FROM stay_info si
        JOIN stay_duration sd
            ON si.stay_id = sd.stay_id
           AND si.upload_id = sd.upload_id
        WHERE si.upload_id = :upload_id
          AND si.chiefcomplaint IS NOT NULL
          AND si.chiefcomplaint <> ''
        GROUP BY si.chiefcomplaint
        ORDER BY cnt DESC
        LIMIT 5
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    top_chief_complaints = [
        {
            "chiefcomplaint": r["chiefcomplaint"],
            "count": r["cnt"],
            "avg_total_ed_stay_time": float(round(r["avg_total_ed_stay_time"], 2)) if r["avg_total_ed_stay_time"] is not None else None
        }
        for r in rows
    ]

    return top_chief_complaints

# chief complaint count bar chart visualization
def get_chief_complaint_counts(upload_id: int) -> list[dict]:
    query = text("""
        SELECT
            chiefcomplaint,
            COUNT(*) AS count
        FROM stay_info
        WHERE upload_id = :upload_id
          AND chiefcomplaint IS NOT NULL
          AND chiefcomplaint <> ''
        GROUP BY chiefcomplaint
        ORDER BY count DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    chief_complaint_counts = [
        {
            "chiefcomplaint": r["chiefcomplaint"],
            "count": r["count"]
        }
        for r in rows
    ]

    return chief_complaint_counts

# Demographics flow audit bar chart visualization

def get_equity_audit(upload_id: int) -> list[dict]:
    query = text("""
        WITH stay_duration AS (
            SELECT
                stay_id,
                upload_id,
                MAX(total_ed_stay_time) AS total_ed_stay_time
            FROM event_log
            WHERE total_ed_stay_time IS NOT NULL
              AND upload_id = :upload_id
            GROUP BY stay_id, upload_id
        ),
        base AS (
            SELECT
                si.race,
                sd.total_ed_stay_time
            FROM stay_info si
            JOIN stay_duration sd
              ON si.stay_id = sd.stay_id
             AND si.upload_id = sd.upload_id
            WHERE si.upload_id = :upload_id
              AND si.race IS NOT NULL
              AND si.race <> ''
        ),
        overall AS (
            SELECT
                AVG(total_ed_stay_time) AS overall_avg_stay_time
            FROM base
        )
        SELECT
            b.race,
            COUNT(*) AS cnt,
            ROUND(AVG(b.total_ed_stay_time), 2) AS race_avg_stay_time,
            ROUND(o.overall_avg_stay_time, 2) AS overall_avg_stay_time,
            ROUND(
                ((AVG(b.total_ed_stay_time) - o.overall_avg_stay_time) / o.overall_avg_stay_time) * 100,
                2
            ) AS variance_pct
        FROM base b
        CROSS JOIN overall o
        GROUP BY b.race, o.overall_avg_stay_time
        ORDER BY variance_pct DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    equity_audit = [
         {
            "group": r["race"],
            "variance": float(r["variance_pct"]),
            #"race_avg_total_ed_stay_time": float(r["race_avg_stay_time"]),
            #"overall_avg_total_ed_stay_time": float(r["overall_avg_stay_time"]),
            #"count": int(r["cnt"])
        }
        for r in rows
    ]

    return equity_audit

def get_chief_complaint_bottleneck_insights(upload_id: int):
    query = text("""
        SELECT
            e.stay_id,
            COALESCE(NULLIF(TRIM(s.chiefcomplaint), ''), 'unknown / missing') AS chiefcomplaint,
            MAX(e.total_ed_stay_time) / 60 AS los_hours
        FROM event_log e
        LEFT JOIN stay_info s
            ON s.stay_id = e.stay_id
           AND s.upload_id = e.upload_id
        WHERE e.upload_id = :u_id
          AND e.total_ed_stay_time IS NOT NULL
        GROUP BY e.stay_id, COALESCE(NULLIF(TRIM(s.chiefcomplaint), ''), 'unknown / missing')
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"u_id": upload_id})

    if df.empty:
        return []

    draft_operational_keywords = {
        "Long_Stay_Boarders": [
            "alcohol intoxication", "altered mental status", "mental status",
            "psych", "si", "detox", "behavioral", "depression", "clearance",
        ],
        "High_Nursing_Intensity": [
            "chest pain", "dyspnea", "shortness of breath",
            "tachycardia", "hypotension", "palpitations", "allergic reaction",
        ],
        "Trauma_MVC_or_Injury": [
            "mvc", "motor vehicle crash", "motor vehicle collision",
            "status post fall", "fall", "injury",
        ],
        "High_Imaging_Demand": [
            "abdominal pain", "flank pain", "quadrant abdominal pain",
            "lower abdominal pain", "right lower quadrant",
            "left lower quadrant", "right upper quadrant",
            "upper quadrant abdominal",
        ],
        "Neuro_or_Syncope": [
            "headache", "syncope", "seizure", "stroke",
            "dizziness", "numbness", "weakness",
        ],
        "MSK_Back_or_Extremity_Pain": [
            "back pain", "lower back pain", "neck pain", "shoulder pain",
            "leg pain", "arm pain", "hip pain", "knee pain",
            "ankle pain", "finger pain", "hand pain", "wrist pain",
            "foot pain", "toe pain",
        ],
        "GU_Urinary": [
            "dysuria", "uti", "urinary frequency", "hematuria",
        ],
        "Skin_Soft_Tissue": [
            "cellulitis", "abscess", "wound infection", "skin infection",
        ],
        "GI_Bleeding": [
            "bright red blood per rectum", "brbpr", "gi bleed",
            "rectal bleed", "bloody stool", "melena",
        ],
        "Viral_Respiratory_ILI": [
            "influenza like illness", "ili", "viral syndrome", "flu like illness",
        ],
        "Quick_Turnaround": [
            "sore throat", "wound eval", "ear pain", "rash",
            "dental pain", "tooth pain", "laceration", "refill",
        ],
        "Workup_Required": [
            "abnormal labs", "fever", "cough", "n v", "n v d",
        ],
        "Evaluation_or_Followup": [
            "for eval", "re eval", "recheck", "follow up",
        ],
        "Abnormal_Test_or_Outside_Result": [
            "abnormal mri", "abnormal ct", "abnormal xray", "abnormal ultrasound",
        ],
    }

    compiled_patterns = {
        group: re.compile(
            r"\b(" + "|".join(re.escape(k) for k in keywords) + r")\b"
        )
        for group, keywords in draft_operational_keywords.items()
    }

    def normalize_complaint(text):
        if pd.isna(text):
            return "unknown / missing"

        text = str(text).lower().strip()
        if not text:
            return "unknown / missing"

        replacements = {
            r"\bh/a\b": "headache",
            r"\bsob\b": "shortness of breath",
            r"\betoh\b": "alcohol intoxication",
            r"\bams\b": "altered mental status",
            r"\babd\b": "abdominal",
            r"\bs/p\b": "status post",
            r"\bcva\b": "stroke",
            r"\bili\b": "influenza like illness",
            r"\bbrbpr\b": "bright red blood per rectum",
            r"\blac\b": "laceration",
        }
        for pat, repl in replacements.items():
            text = re.sub(pat, repl, text)

        text = re.sub(r"[/,;:+()\-]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def map_to_op_group(text):
        text = normalize_complaint(text)
        if text == "unknown / missing":
            return "Unknown/Missing"
        for group, pattern in compiled_patterns.items():
            if pattern.search(text):
                return group
        return "Other/Misc"

    def has_transfer_flag(text):
        text = normalize_complaint(text)
        return int(bool(re.search(r"\btransfer\b", text)))

    df["chiefcomplaint_clean"] = df["chiefcomplaint"].apply(normalize_complaint)
    df["op_group"] = df["chiefcomplaint"].apply(map_to_op_group)
    df["is_transfer"] = df["chiefcomplaint"].apply(has_transfer_flag)

    stats = (
        df.groupby("op_group")
        .agg(
            patient_count=("op_group", "count"),
            avg_los=("los_hours", "mean"),
            total_bed_hours=("los_hours", "sum"),
            transfer_count=("is_transfer", "sum"),
        )
        .reset_index()
        .sort_values(by="total_bed_hours", ascending=False)
    )

    stats["transfer_pct"] = (
        stats["transfer_count"] / stats["patient_count"] * 100
    ).round(2)

#    print(f"\n--- OPERATIONAL BOTTLENECKS (ID: {upload_id}) ---")
#    print(stats[[
#        "op_group", "patient_count", "transfer_count",
#        "transfer_pct", "total_bed_hours"
#    ]].head(10))

    return [
        {
            "label": row["op_group"],
            "value": round(row["total_bed_hours"], 2),
            "avg_los": round(row["avg_los"], 2),
            "count": int(row["patient_count"]),
            "transfer_count": int(row["transfer_count"]),
            "transfer_pct": float(row["transfer_pct"]),
        }
        for _, row in stats.iterrows()
    ]

# Volume vs Efficiency correlation scatter plot visualization
def get_volume_efficiency_correlation():
    sql = text("""
        SELECT
            u.upload_id,
            m.p90_value,
            COUNT(DISTINCT s.stay_id) AS patient_volume
        FROM upload_history u
        JOIN metrics m
            ON u.upload_id = m.upload_id
        AND m.metric_name = 'total_ed_stay_time'
        LEFT JOIN stay_info s
            ON u.upload_id = s.upload_id
        GROUP BY u.upload_id, m.p90_value
        ORDER BY u.upload_id;
    """)

    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()

    return {
        "correlation_chart": [
            {
                "upload_id": row["upload_id"],
                "patient_volume": int(row["patient_volume"]),
                "p90_wait_time": float(row["p90_value"])
            }
            for row in rows
        ]
    }
# disposition breakdown by milestone bar chart visualization
def get_disposition_milestone_breakdown(upload_id: int):
    query = text("""
        SELECT 
            si.disposition,
            AVG(e.time_to_vital) AS avg_vital,
            AVG(e.time_to_medrecon) AS avg_medrecon,
            AVG(e.time_to_dispen) AS avg_dispen,
            AVG(e.time_to_discharge) AS avg_discharge
        FROM event_log e
        JOIN stay_info si
          ON e.stay_id = si.stay_id
         AND e.upload_id = si.upload_id
        WHERE e.upload_id = :u_id
          AND si.disposition IN ('Admitted', 'Home')
        GROUP BY si.disposition
    """)

    with engine.begin() as conn:
        rows = conn.execute(query, {"u_id": upload_id}).mappings().all()

    def safe_float(value):
        if value is None:
            return None
        value = float(value)
        return None if math.isnan(value) else value

    result = {
        "upload_id": upload_id,
        "disposition_milestone_analysis": {
            "admitted": {
                "avg_vital": None,
                "avg_medrecon": None,
                "avg_dispen": None,
                "avg_discharge": None
            },
            "home": {
                "avg_vital": None,
                "avg_medrecon": None,
                "avg_dispen": None,
                "avg_discharge": None
            }
        }
    }

    for row in rows:
        disposition = str(row["disposition"]).strip().lower()
        if disposition in result["disposition_milestone_analysis"]:
            result["disposition_milestone_analysis"][disposition] = {
                "avg_vital": safe_float(row["avg_vital"]),
                "avg_medrecon": safe_float(row["avg_medrecon"]),
                "avg_dispen": safe_float(row["avg_dispen"]),
                "avg_discharge": safe_float(row["avg_discharge"])
            }

    return result

# acuity level milestone bar chart visualization
def get_acuity_level_breakdown(upload_id: int):
    query = text("""
        SELECT 
            si.scale_level,
            AVG(e.time_to_triage) AS avg_triage,
            AVG(e.time_to_vital) AS avg_vital,
            AVG(e.time_to_medrecon) AS avg_medrecon,
            AVG(e.time_to_dispen) AS avg_dispen,
            AVG(e.time_to_discharge) AS avg_discharge,
            AVG(e.total_ed_stay_time) AS avg_total_stay
        FROM event_log e
        JOIN stay_info si
          ON e.stay_id = si.stay_id
         AND e.upload_id = si.upload_id
        WHERE e.upload_id = :u_id
          AND si.scale_level IS NOT NULL
        GROUP BY si.scale_level
        ORDER BY si.scale_level
    """)

    with engine.begin() as conn:
        rows = conn.execute(query, {"u_id": upload_id}).mappings().all()

    def safe_float(value):
        if value is None:
            return None
        value = float(value)
        return None if math.isnan(value) else value

    return {
        "upload_id": upload_id,
        "acuity_level_analysis": [
            {
                "scale_level": int(row["scale_level"]),
                "avg_triage": safe_float(row["avg_triage"]),
                "avg_vital": safe_float(row["avg_vital"]),
                "avg_medrecon": safe_float(row["avg_medrecon"]),
                "avg_dispen": safe_float(row["avg_dispen"]),
                "avg_discharge": safe_float(row["avg_discharge"]),
                "avg_total_stay": safe_float(row["avg_total_stay"]),
            }
            for row in rows
            if row["scale_level"] is not None
        ]
    }
