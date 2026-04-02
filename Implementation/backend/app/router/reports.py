from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import tempfile
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import json
from datetime import datetime
from app.services.insights_services import (
    get_disposition_mix, get_top_chief_complaints, get_equity_audit,
    get_chief_complaint_bottleneck_insights, get_volume_efficiency_correlation,
    get_disposition_milestone_breakdown, get_acuity_level_breakdown, get_temporal_heatmap,
    get_latest_upload_id
)
from app.services.metrics_services import get_dashboard_horizon

router = APIRouter(prefix="/reports", tags=["reports"])

def cleanup_temp_file(file_path: str):
    """Background task to clean up temporary file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"Error cleaning up temp file {file_path}: {e}")

@router.get("/generate-pdf")
def generate_pdf_report(background_tasks: BackgroundTasks):
    """Generate a comprehensive PDF report of the ED dashboard"""
    
    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf_path = tmp_file.name
    
    try:
        # Initialize PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph("BottleneckIQ ED Analytics Report", title_style))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Gather data from all service functions
        effective_id = get_latest_upload_id()
        data = {}
        try:
            if effective_id:
                data["logistics"] = {
                    "logistics_root_cause": {
                        "disposition_mix": get_disposition_mix(effective_id),
                        "top_chief_complaints": get_top_chief_complaints(effective_id)
                    }
                }
                data["demographics"] = {
                    "equity_audit": get_equity_audit(effective_id)
                }
                data["bottlenecks"] = get_chief_complaint_bottleneck_insights(effective_id)
                data["volume_efficiency"] = get_volume_efficiency_correlation()
                data["dispositions"] = get_disposition_milestone_breakdown(effective_id)
                data["acuity"] = get_acuity_level_breakdown(effective_id)
                data["temporal_heatmap"] = get_temporal_heatmap()
                data["dashboard_horizon"] = get_dashboard_horizon()
            else:
                # Default empty data
                data = {
                    "logistics": {"logistics_root_cause": {"disposition_mix": [], "top_chief_complaints": []}},
                    "demographics": {"equity_audit": []},
                    "bottlenecks": [],
                    "volume_efficiency": [],
                    "dispositions": [],
                    "acuity": [],
                    "temporal_heatmap": {"volume_matrix": [[0]*4 for _ in range(7)], "day_labels": [], "slice_labels": []},
                    "dashboard_horizon": {"display_date": "No data available", "upload_id": None}
                }
        except Exception as e:
            # If any service fails, continue with available data
            print(f"Warning: Some data collection failed: {e}")
            pass
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_text = """
        This report provides a comprehensive analysis of Emergency Department operations, 
        including patient flow patterns, bottleneck identification, demographic insights, 
        and performance metrics. The data is aggregated from recent patient encounters 
        to support operational decision-making and resource allocation.
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Key Metrics Section
        story.append(Paragraph("Key Performance Metrics", styles['Heading2']))
        
        if 'dashboard_horizon' in data and 'display_date' in data['dashboard_horizon']:
            horizon_text = f"Analysis Period: {data['dashboard_horizon']['display_date']}"
            story.append(Paragraph(horizon_text, styles['Normal']))
        
        # Logistics Root Cause
        if 'logistics' in data and 'logistics_root_cause' in data['logistics']:
            story.append(Paragraph("Patient Disposition Analysis", styles['Heading3']))
            logistics = data['logistics']['logistics_root_cause']
            
            if 'disposition_mix' in logistics:
                disp_data = [['Disposition Type', 'Count', 'Percentage']]
                for item in logistics['disposition_mix']:
                    disp_data.append([item['type'], str(item['count']), f"{item['percentage']}%"])
                
                table = Table(disp_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 15))
        
        # Chief Complaint Bottlenecks
        if 'bottlenecks' in data:
            story.append(Paragraph("Chief Complaint Bottlenecks", styles['Heading3']))
            bottlenecks = data['bottlenecks']
            
            if isinstance(bottlenecks, list) and bottlenecks:
                cc_data = [['Chief Complaint', 'Bed-Hours', 'Avg LOS (hrs)', 'Transfer Rate']]
                for item in bottlenecks[:10]:  # Top 10
                    cc_data.append([
                        item.get('label', 'N/A').replace('_', ' '),
                        str(item.get('value', 0)),
                        str(item.get('avg_los', 0)),
                        f"{item.get('transfer_pct', 0)}%"
                    ])
                
                table = Table(cc_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 15))
        
        # Temporal Patterns
        if 'temporal_heatmap' in data:
            story.append(Paragraph("Temporal Volume Patterns", styles['Heading3']))
            heatmap = data['temporal_heatmap']
            
            if 'volume_matrix' in heatmap and 'day_labels' in heatmap and 'slice_labels' in heatmap:
                story.append(Paragraph("Average patient volume by day of week and time slice:", styles['Normal']))
                
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
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 15))
        
        # Recommendations Section (placeholder for future implementation)
        story.append(Paragraph("Recommendations", styles['Heading2']))
        recommendations = """
        Based on the analysis of ED operations:
        
        1. Monitor high-volume time periods identified in the temporal heatmap
        2. Address chief complaint bottlenecks with targeted resource allocation
        3. Review disposition patterns for optimization opportunities
        4. Consider staffing adjustments based on peak volume periods
        5. Implement process improvements for identified bottlenecks
        
        Note: This section will be enhanced with AI-generated recommendations in future updates.
        """
        story.append(Paragraph(recommendations, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Footer
        story.append(Paragraph("Report generated by BottleneckIQ Analytics Platform", styles['Italic']))
        story.append(Paragraph("Confidential - For internal use only", styles['Italic']))
        
        # Build PDF
        try:
            doc.build(story)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
        
        # Verify file was created
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF file was not created successfully")
        
        # Return the PDF file with cleanup task
        response = FileResponse(
            path=pdf_path,
            media_type='application/pdf',
            filename='bottleneckiq-report.pdf'
        )
        
        # Add background task to clean up the file after response is sent (if background_tasks provided)
        if background_tasks:
            background_tasks.add_task(cleanup_temp_file, pdf_path)
        
        return response
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    finally:
        # Clean up temp file after response
        if os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except:
                pass