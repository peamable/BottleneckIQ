from datetime import datetime
import os
import tempfile

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sqlalchemy import text

from app.core.database import engine
from app.services.analytics import predict_next_volume
from app.services.insights_services import (
    get_acuity_level_breakdown, 
    get_bed_occupancy_analysis_by_case_mix,
    get_disposition_mix,
    get_disposition_milestone_breakdown, 
    get_equity_audit,
    get_event_flow_forecast_insights,
    get_latest_upload_id,
    get_p90_total_ed_stay_time_volume_correlations,
    get_stage_temporal_forecast,
    get_temporal_heatmap,
    
)
from app.services.metrics_services import (
    get_dashboard_horizon,
    get_dashboard_summary,
    get_performance_trend_data,
)
from app.services.upload_progress import get_upload_job

router = APIRouter(prefix="/reports", tags=["reports"])

REPORT_NAVY = colors.HexColor("#0f172a")
REPORT_SLATE = colors.HexColor("#334155")
REPORT_MUTED = colors.HexColor("#475569")
REPORT_BORDER = colors.HexColor("#cbd5e1")
REPORT_SURFACE = colors.HexColor("#f8fafc")
REPORT_SURFACE_ALT = colors.HexColor("#f1f5f9")

STAGE_LABELS = {
    "time_to_triage": "Time to Triage",
    "time_to_vital": "Time to Vitals",
    "time_to_medrecon": "Time to Med Recon",
    "time_to_dispen": "Time to Dispense",
    "time_to_discharge": "Time to Discharge",
    "total_ed_stay_time": "Average Stay Time",
}

FORECAST_STAGE_KEYS = ["vital", "medrecon", "dispen", "discharge"]
FORECAST_STAGE_LABELS = {
    "vital": "Vitals",
    "medrecon": "Med Recon",
    "dispen": "Dispensing",
    "discharge": "Discharge",
}
TREND_SERIES = [
    ("time_to_triage_p90", "Triage", colors.HexColor("#7c3aed")),
    ("time_to_vital_p90", "Vitals", colors.HexColor("#be185d")),
    ("time_to_medrecon_p90", "Med Recon", colors.HexColor("#0ea5e9")),
    ("time_to_dispen_p90", "Dispense", colors.HexColor("#16a34a")),
    ("time_to_discharge_p90", "Discharge", REPORT_NAVY),
]

def cleanup_temp_file(file_path: str):
    """Background task to clean up temporary file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"Error cleaning up temp file {file_path}: {e}")


def _build_table(table_data, header_color=REPORT_NAVY, body_color=REPORT_SURFACE, font_size=9):
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), font_size),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('BACKGROUND', (0, 1), (-1, -1), body_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [body_color, REPORT_SURFACE_ALT]),
        ('LINEBELOW', (0, 0), (-1, 0), 0.75, REPORT_BORDER),
        ('GRID', (0, 0), (-1, -1), 0.5, REPORT_BORDER),
        ('TEXTCOLOR', (0, 1), (-1, -1), REPORT_NAVY),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
    ]))
    return table


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _window_label(window_index: int) -> str:
    start_hour = int(window_index) * 4
    end_hour = start_hour + 4
    return f"{start_hour:02d}:00-{end_hour:02d}:00"


def _find_peak_stage(slot: dict) -> tuple[str, float]:
    peak_stage = max(
        FORECAST_STAGE_KEYS,
        key=lambda stage: _safe_float(slot.get(stage)),
    )
    return FORECAST_STAGE_LABELS[peak_stage], round(_safe_float(slot.get(peak_stage)), 1)


def _build_pipeline_summary(upload_id: int) -> dict:
    job = get_upload_job(upload_id)
    summary = (job or {}).get("summary_report") or {}
    if summary:
        return {
            "stay_ids_inserted": int(summary.get("stay_ids_inserted", 0)),
            "rows_skipped_or_removed": int(summary.get("rows_skipped_or_removed", 0)),
            "ed_events_inserted": int(summary.get("ed_events_inserted", 0)),
            "stay_ids_summarized": int(summary.get("stay_ids_summarized", 0)),
        }

    with engine.begin() as conn:
        stay_ids_inserted = conn.execute(
            text("SELECT COUNT(*) FROM stay_info WHERE upload_id = :uid"),
            {"uid": upload_id},
        ).scalar() or 0
        ed_events_inserted = conn.execute(
            text("SELECT COUNT(*) FROM ed_stay WHERE upload_id = :uid"),
            {"uid": upload_id},
        ).scalar() or 0
        stay_ids_summarized = conn.execute(
            text("SELECT COUNT(*) FROM event_log WHERE upload_id = :uid"),
            {"uid": upload_id},
        ).scalar() or 0

    return {
        "stay_ids_inserted": int(stay_ids_inserted),
        "rows_skipped_or_removed": int(summary.get("rows_skipped_or_removed", 0)),
        "ed_events_inserted": int(ed_events_inserted),
        "stay_ids_summarized": int(stay_ids_summarized),
    }


def _build_trend_chart(trend_data: list[dict]) -> Drawing | None:
    if len(trend_data) < 2:
        return None

    categories = []
    chart_series = []
    y_values = []
    for entry in trend_data[-6:]:
        label = str(entry.get("period_start", f"Upload {entry.get('upload_id', '')}"))
        categories.append(label.replace(" (ID:", "\nID:").replace(")", ""))

    for key, _, _ in TREND_SERIES:
        series_values = []
        for entry in trend_data[-6:]:
            value = entry.get(key)
            numeric = _safe_float(value, default=None) if value is not None else None
            if numeric is None:
                numeric = 0.0
            series_values.append(numeric)
            y_values.append(numeric)
        chart_series.append(series_values)

    if not y_values or max(y_values) <= 0:
        return None

    drawing = Drawing(500, 240)
    drawing.add(String(0, 225, "Performance Trend (P90 by Clinical Stage)", fontName="Helvetica-Bold", fontSize=12, fillColor=REPORT_NAVY))

    chart = HorizontalLineChart()
    chart.x = 40
    chart.y = 55
    chart.height = 130
    chart.width = 400
    chart.data = chart_series
    chart.categoryAxis.categoryNames = categories
    chart.categoryAxis.labels.boxAnchor = 'ne'
    chart.categoryAxis.labels.angle = 25
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.fillColor = REPORT_MUTED
    chart.categoryAxis.strokeColor = REPORT_BORDER
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(y_values) * 1.15
    chart.valueAxis.valueStep = max(10, int(chart.valueAxis.valueMax / 5))
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.labels.fillColor = REPORT_MUTED
    chart.valueAxis.strokeColor = REPORT_BORDER
    chart.valueAxis.visibleGrid = 1
    chart.valueAxis.gridStrokeColor = REPORT_BORDER
    chart.joinedLines = 1
    for idx, (_, _, color) in enumerate(TREND_SERIES):
        chart.lines[idx].strokeColor = color
        chart.lines[idx].strokeWidth = 2.5
        chart.lines[idx].symbol = None

    drawing.add(chart)

    legend_x = 40
    for idx, (_, label, color) in enumerate(TREND_SERIES):
        y = 25 - (idx // 3) * 12
        x = legend_x + (idx % 3) * 145
        drawing.add(String(x, y, f"{label}", fontName="Helvetica", fontSize=8, fillColor=color))

    return drawing

@router.get("/generate-pdf")
def generate_pdf_report(background_tasks: BackgroundTasks):
    """Generate a comprehensive PDF report of the ED dashboard"""

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_path = tmp_file.name
    tmp_file.close()
    
    try:
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=44,
            bottomMargin=32,
        )
        styles = getSampleStyleSheet()
        story = []

        body_style = ParagraphStyle(
            'BodySmall',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            spaceAfter=6,
        )
        note_style = ParagraphStyle(
            'Note',
            parent=styles['Italic'],
            fontSize=8,
            textColor=REPORT_MUTED,
            leading=11,
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=REPORT_MUTED,
            alignment=1,
            spaceAfter=4,
        )
        meta_style = ParagraphStyle(
            'Meta',
            parent=styles['Normal'],
            fontSize=9,
            textColor=REPORT_MUTED,
            alignment=1,
            spaceAfter=16,
        )
        section_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=15,
            leading=18,
            textColor=REPORT_NAVY,
            spaceBefore=6,
            spaceAfter=10,
        )
        subsection_style = ParagraphStyle(
            'SubsectionHeading',
            parent=styles['Heading3'],
            fontSize=11,
            leading=14,
            textColor=REPORT_SLATE,
            spaceBefore=4,
            spaceAfter=8,
        )
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=REPORT_NAVY,
            spaceAfter=10,
            alignment=1
        )
        story.append(Paragraph("BottleneckIQ Operational Report", title_style))
        story.append(Paragraph("Operational snapshot, trend review, and near-term risk briefing", subtitle_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}", meta_style))

        effective_id = get_latest_upload_id()
        data = {}
        try:
            if effective_id:
                stage_forecast = get_stage_temporal_forecast(effective_id)
                event_flow_forecast = get_event_flow_forecast_insights(effective_id)
                volume_prediction = predict_next_volume(effective_id)
                dashboard_summary = get_dashboard_summary(effective_id)
                trend_chart = get_performance_trend_data(lookback=8)
                pipeline_summary = _build_pipeline_summary(effective_id)
                data["patient_flow_analysis"] = {
                    "disposition_mix": get_disposition_mix(effective_id),
                    "bed_occupancy_analysis_by_case_mix": get_bed_occupancy_analysis_by_case_mix(effective_id),
                }
                data["demographics"] = {
                    "equity_audit": get_equity_audit(effective_id)
                }
                data["p90_total_ed_stay_time_volume_correlations"] = get_p90_total_ed_stay_time_volume_correlations()
                data["dispositions"] = get_disposition_milestone_breakdown(effective_id)
                data["acuity"] = get_acuity_level_breakdown(effective_id)
                data["temporal_heatmap"] = get_temporal_heatmap()
                data["dashboard_horizon"] = get_dashboard_horizon()
                data["stage_forecast"] = stage_forecast
                data["event_flow_forecast"] = event_flow_forecast
                data["volume_prediction"] = volume_prediction
                data["dashboard_summary"] = dashboard_summary
                data["trend_data"] = trend_chart
                data["pipeline_summary"] = pipeline_summary
            else:
                data = {
                    "patient_flow_analysis": {
                        "disposition_mix": [],
                        "bed_occupancy_analysis_by_case_mix": [],
                    },
                    "demographics": {"equity_audit": []},
                    "p90_total_ed_stay_time_volume_correlations": [],
                    "dispositions": [],
                    "acuity": [],
                    "temporal_heatmap": {"volume_matrix": [[0]*4 for _ in range(7)], "day_labels": [], "slice_labels": []},
                    "dashboard_horizon": {"display_date": "No data available", "upload_id": None},
                    "stage_forecast": {"upcoming_hours": [], "upcoming_days": [], "alerts": [], "operational_context": {}},
                    "event_flow_forecast": {"top_delay_flows": []},
                    "volume_prediction": {"error": "No trained model available."},
                    "dashboard_summary": [],
                    "trend_data": [],
                    "pipeline_summary": {},
                }
        except Exception as e:
            print(f"Warning: Some data collection failed: {e}")
            pass

        story.append(Paragraph("Executive Summary", section_style))
        stage_forecast = data.get("stage_forecast", {})
        upcoming_hours = stage_forecast.get("upcoming_hours", [])
        alerts = stage_forecast.get("alerts", [])
        event_flow_forecast = data.get("event_flow_forecast", {})
        top_pathways = event_flow_forecast.get("top_delay_flows", [])
        volume_prediction = data.get("volume_prediction", {})

        executive_lines = [
            "This report summarizes the latest uploaded emergency department dataset as an operational snapshot and a short-horizon risk review.",
        ]
        if alerts:
            top_alert = alerts[0]
            executive_lines.append(
                f"The highest near-term forecasted pressure is in {top_alert.get('stage_label', 'a monitored stage')} at {top_alert.get('target_day_label', '')} {top_alert.get('target_time_label', '')}, with risk estimated at {top_alert.get('risk_next', 0)}%."
            )
        elif upcoming_hours:
            peak_stage, peak_risk = _find_peak_stage(upcoming_hours[0])
            executive_lines.append(
                f"The next-hour outlook shows the highest projected stage pressure in {peak_stage} at {peak_risk}% risk."
            )
        if volume_prediction and not volume_prediction.get("error"):
            executive_lines.append(
                f"The volume forecast projects approximately {volume_prediction.get('predicted_volume', 0)} arrivals in the next 4-hour window."
            )
        if top_pathways:
            pathway = top_pathways[0]
            executive_lines.append(
                f"The most delay-prone pathway in recent history is {pathway.get('event_flow_label', 'the leading pathway')}, averaging {pathway.get('avg_los_min', 0)} minutes LOS."
            )

        story.append(Paragraph(" ".join(executive_lines), body_style))
        story.append(Spacer(1, 20))

        story.append(Paragraph("Data Snapshot", section_style))
        pipeline_summary = data.get("pipeline_summary", {})
        if pipeline_summary:
            summary_table = _build_table([
                ["Metric", "Value"],
                ["Stay IDs inserted", str(pipeline_summary.get("stay_ids_inserted", 0))],
                ["ED events inserted", str(pipeline_summary.get("ed_events_inserted", 0))],
                ["Stay IDs summarized", str(pipeline_summary.get("stay_ids_summarized", 0))],
                ["Rows skipped or removed", str(pipeline_summary.get("rows_skipped_or_removed", 0))],
            ])
            story.append(summary_table)
            story.append(Spacer(1, 14))

        story.append(Paragraph("Operational Dashboard Snapshot", section_style))
        if 'dashboard_horizon' in data and 'display_date' in data['dashboard_horizon']:
            horizon_text = f"Analysis Period: {data['dashboard_horizon']['display_date']}"
            story.append(Paragraph(horizon_text, body_style))

        dashboard_summary = data.get("dashboard_summary", [])
        if dashboard_summary:
            metrics_table = [["Metric", "Average (min)", "Shift vs Previous Upload"]]
            for item in dashboard_summary:
                label = STAGE_LABELS.get(item.get("metric_name"), item.get("metric_name", "Metric"))
                trend = item.get("trend", 0)
                direction = item.get("direction", "stable")
                if direction == "up":
                    trend_label = f"Longer by {trend}%"
                elif direction == "down":
                    trend_label = f"Shorter by {trend}%"
                else:
                    trend_label = "No material change"
                metrics_table.append([
                    label,
                    f"{_safe_float(item.get('avg_value')):.1f}",
                    trend_label,
                ])
            story.append(_build_table(metrics_table))
            story.append(Spacer(1, 15))

        trend_drawing = _build_trend_chart(data.get("trend_data", []))
        if trend_drawing is not None:
            story.append(trend_drawing)
            story.append(Paragraph(
                "The embedded trend chart uses the same stage palette as the dashboard so the report stays visually aligned with the live metrics view.",
                note_style,
            ))
            story.append(Spacer(1, 14))
        
        if 'patient_flow_analysis' in data:
            story.append(Paragraph("Patient Disposition Analysis", subsection_style))
            patient_flow_analysis = data['patient_flow_analysis']
            
            if 'disposition_mix' in patient_flow_analysis:
                disp_data = [['Disposition Type', 'Count', 'Percentage']]
                for item in patient_flow_analysis['disposition_mix']:
                    disp_data.append([item['type'], str(item['count']), f"{item['percentage']}%"])
                story.append(_build_table(disp_data))
                story.append(Spacer(1, 15))

            bed_occupancy_analysis_by_case_mix = patient_flow_analysis.get('bed_occupancy_analysis_by_case_mix', [])
            story.append(Paragraph("Bed Occupancy Analysis by Case Mix", subsection_style))

            if isinstance(bed_occupancy_analysis_by_case_mix, list) and bed_occupancy_analysis_by_case_mix:
                cc_data = [['Case Mix', 'Bed-Hours', 'Avg LOS (hrs)', 'Transfer Rate']]
                for item in bed_occupancy_analysis_by_case_mix[:10]:  # Top 10
                    cc_data.append([
                        item.get('label', 'N/A').replace('_', ' '),
                        str(item.get('value', 0)),
                        str(item.get('avg_los', 0)),
                        f"{item.get('transfer_pct', 0)}%"
                    ])
                story.append(_build_table(cc_data))
                story.append(Spacer(1, 15))
        
        if 'temporal_heatmap' in data:
            story.append(Paragraph("Temporal Volume Patterns", subsection_style))
            heatmap = data['temporal_heatmap']
            
            if 'volume_matrix' in heatmap and 'day_labels' in heatmap and 'slice_labels' in heatmap:
                story.append(Paragraph("Average patient volume by day of week and time slice.", body_style))
                
                # Create a table for the heatmap data
                matrix = heatmap['volume_matrix']
                days = heatmap['day_labels']
                slices = heatmap['slice_labels']
                
                # Create table data
                table_data = [['Day/Time'] + slices]
                for i, day in enumerate(days):
                    row = [day]
                    for j, volume in enumerate(matrix[i]):
                        row.append(str(volume))
                    table_data.append(row)
                story.append(_build_table(table_data, font_size=8))
                story.append(Spacer(1, 15))

        story.append(Paragraph("Forecasting Hub Summary", section_style))
        operational_context = stage_forecast.get("operational_context", {})
        if operational_context:
            context_rows = [["Signal", "Current Reading", "Interpretation"]]
            for item in operational_context.values():
                context_rows.append([
                    item.get("label", "Signal"),
                    item.get("value_label", "N/A"),
                    item.get("detail", "No context available"),
                ])
            story.append(_build_table(context_rows))
            story.append(Spacer(1, 12))

        if upcoming_hours:
            story.append(Paragraph("Next 4-Hour Outlook", subsection_style))
            hour_rows = [["Offset", "Time", "Highest Risk Stage", "Peak Risk"]]
            for slot in upcoming_hours[:4]:
                peak_stage, peak_risk = _find_peak_stage(slot)
                hour_rows.append([
                    f"+{slot.get('forecast_offset_hours', 0)}h",
                    f"{slot.get('day_label', '')} {slot.get('time_label', '')}",
                    peak_stage,
                    f"{peak_risk:.1f}%",
                ])
            story.append(_build_table(hour_rows))
            story.append(Spacer(1, 12))

        upcoming_days = stage_forecast.get("upcoming_days", [])
        if upcoming_days:
            story.append(Paragraph("Next 4-Day Outlook", subsection_style))
            day_rows = [["Offset", "Day", "Highest Risk Stage", "Peak Risk"]]
            for slot in upcoming_days[:4]:
                peak_stage, peak_risk = _find_peak_stage(slot)
                day_rows.append([
                    f"+{slot.get('forecast_offset_days', 0)}d",
                    slot.get('day_label', 'N/A'),
                    peak_stage,
                    f"{peak_risk:.1f}%",
                ])
            story.append(_build_table(day_rows))
            story.append(Spacer(1, 12))

        if alerts:
            story.append(Paragraph("Prep Recommendations", subsection_style))
            recommendation_rows = [["Stage", "Target Window", "Risk", "Operational Action"]]
            for alert in alerts[:4]:
                recommendation_rows.append([
                    alert.get("stage_label", "Stage"),
                    f"{alert.get('target_day_label', '')} {alert.get('target_time_label', '')}",
                    f"{_safe_float(alert.get('risk_next')):.1f}%",
                    alert.get("recommendation", "No recommendation available"),
                ])
            story.append(_build_table(recommendation_rows, font_size=8))
            story.append(Spacer(1, 12))
            story.append(Paragraph(
                "These recommendations are based on a risk model and should be used as a guide. Always consider the full clinical and operational context when making decisions.",
                note_style,
            ))
            story.append(Spacer(1, 12))

        if top_pathways:
            story.append(Paragraph("High-Risk Patient Pathways", subsection_style))
            pathway_rows = [["Pathway", "Avg LOS (min)", "Primary Driver", "Operational Note"]]
            for pathway in top_pathways[:4]:
                pathway_rows.append([
                    pathway.get("event_flow_label", "Pathway"),
                    str(pathway.get("avg_los_min", 0)),
                    pathway.get("primary_driver", "Throughput Friction"),
                    pathway.get("recommendation", "No pathway note available"),
                ])
            story.append(_build_table(pathway_rows, font_size=8))
            story.append(Spacer(1, 12))

        story.append(Paragraph("Volume Forecast Snapshot", section_style))
        if volume_prediction and not volume_prediction.get("error"):
            model_rows = [["Model Output", "Value"]]
            model_rows.append(["Current 4-hour window", _window_label(volume_prediction.get("current_window", 0))])
            model_rows.append(["Target 4-hour window", _window_label(volume_prediction.get("target_window", 0))])
            model_rows.append(["Target day index", str(volume_prediction.get("target_day_of_week", "N/A"))])
            model_rows.append(["Predicted patient volume", str(volume_prediction.get("predicted_volume", 0))])
            story.append(_build_table(model_rows))
            story.append(Spacer(1, 8))
            story.append(Paragraph(
                "This forecast is produced from the saved Random Forest pipeline scored against the latest upload's temporal summary. It is included here as additional planning context but more accurate data is required to make a reliable model",
                body_style,
            ))
        else:
            story.append(Paragraph(
                "The Random Forest volume model could not be evaluated for this report. This usually means the saved pipeline is missing or the latest upload does not contain enough temporal summary data for scoring.",
                body_style,
            ))
        story.append(Spacer(1, 20))

        story.append(Paragraph("Generated by the BottleneckIQ analytics platform", note_style))
        story.append(Paragraph("Confidential. Internal operational use only.", note_style))

        try:
            doc.build(story)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF file was not created successfully")

        response = FileResponse(
            path=pdf_path,
            media_type='application/pdf',
            filename='BottleneckIQ Operational Report.pdf',
            background=background_tasks
        )

        background_tasks.add_task(cleanup_temp_file, pdf_path)
        
        return response

    except HTTPException:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
        raise
    except Exception as e:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
