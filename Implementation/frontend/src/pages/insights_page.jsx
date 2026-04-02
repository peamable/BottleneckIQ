import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js'; // You'll need to install this
import BottleneckBanner from '../components/bottleneck_banner';
import '../insights.css';
import mockData from "../insights_mock.json";
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend, ReferenceLine 
} from 'recharts';

function getAxisRange(values, { minPad = 5, padRatio = 0.1 } = {}) {
  const numericValues = values.filter((value) => Number.isFinite(value));
  if (!numericValues.length) {
    return [0, 100];
  }

  const minValue = Math.min(...numericValues);
  const maxValue = Math.max(...numericValues);

  if (minValue === maxValue) {
    const pad = Math.max(minPad, Math.abs(minValue) * padRatio || minPad);
    return [Math.max(0, minValue - pad), maxValue + pad];
  }

  const span = maxValue - minValue;
  const pad = Math.max(minPad, span * padRatio);
  return [Math.max(0, minValue - pad), maxValue + pad];
}

function buildTrendLine(points) {
  const validPoints = points.filter(
    (point) => Number.isFinite(point.x) && Number.isFinite(point.y)
  );

  if (validPoints.length < 2) {
    return null;
  }

  const n = validPoints.length;
  const sumX = validPoints.reduce((total, point) => total + point.x, 0);
  const sumY = validPoints.reduce((total, point) => total + point.y, 0);
  const sumXY = validPoints.reduce((total, point) => total + (point.x * point.y), 0);
  const sumXX = validPoints.reduce((total, point) => total + (point.x * point.x), 0);
  const denominator = (n * sumXX) - (sumX * sumX);

  if (denominator === 0) {
    return null;
  }

  const slope = ((n * sumXY) - (sumX * sumY)) / denominator;
  const intercept = (sumY - (slope * sumX)) / n;
  const sortedX = validPoints.map((point) => point.x).sort((a, b) => a - b);
  const startX = sortedX[0];
  const endX = sortedX[sortedX.length - 1];

  return {
    x: [startX, endX],
    y: [slope * startX + intercept, slope * endX + intercept],
  };
}

const InsightsPage = () => {
  const [insightsData, setInsightsData] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isUsingMockData, setIsUsingMockData] = useState(false);

useEffect(() => {
  const controller = new AbortController();

  const fetchInsights = async () => {
    try {
      setLoading(true);
      setError(null);
      setIsUsingMockData(false);

      const [
        logisticsRes,
        demographicsRes,
        bottlenecksRes,
        volumeEfficiencyRes,
        dispositionsRes,
        acuityRes,
        temporalHeatmapRes,
        stageTemporalRes,
        eventFlowRes
      ] = await Promise.all([
        fetch('http://localhost:8000/insights/logistics_root_cause', {
          signal: controller.signal
        }),
        fetch('http://localhost:8000/insights/demographics_audit', {
          signal: controller.signal
        }),
        fetch('http://localhost:8000/insights/chief_complaint_bottlenecks', {
          signal: controller.signal
        }),
        fetch('http://localhost:8000/insights/volume-efficiency-correlation', {
          signal: controller.signal
        }),
        fetch('http://localhost:8000/insights/disposition_milestone_analysis', {
          signal: controller.signal
        }),
        fetch('http://localhost:8000/insights/acuity_level_analysis', {
          signal: controller.signal
        }),
        fetch('http://localhost:8000/insights/temporal_heatmap', {
          signal: controller.signal
        }),
        fetch('http://localhost:8000/insights/stage_temporal_forecast', {
          signal: controller.signal
        }),
        fetch('http://localhost:8000/insights/event_flow_forecast', {
          signal: controller.signal
        })
      ]);
      if (!logisticsRes.ok) throw new Error(`Logistics Error: ${logisticsRes.status}`);
      if (!demographicsRes.ok) throw new Error(`Demographics Error: ${demographicsRes.status}`);
      if (!bottlenecksRes.ok) throw new Error(`Chief Complaint Bottlenecks Error: ${bottlenecksRes.status}`);
      if (!volumeEfficiencyRes.ok) throw new Error(`Volume-Efficiency Correlation Error: ${volumeEfficiencyRes.status}`);
      if (!dispositionsRes.ok) throw new Error(`Disposition Comparison Error: ${dispositionsRes.status}`);
      if (!acuityRes.ok) throw new Error(`Acuity Level Analysis Error: ${acuityRes.status}`);
      if (!stageTemporalRes.ok) throw new Error(`Stage Temporal Forecast Error: ${stageTemporalRes.status}`);
      if (!eventFlowRes.ok) throw new Error(`Event Flow Forecast Error: ${eventFlowRes.status}`);

      const logisticsPayload = await logisticsRes.json();
      const demographicsPayload = await demographicsRes.json();
      const bottlenecksPayload = await bottlenecksRes.json();
      const volumeEfficiencyPayload = await volumeEfficiencyRes.json();
      const dispositionsPayload = await dispositionsRes.json();
      const acuityPayload = await acuityRes.json();
      const temporalHeatmapPayload = await temporalHeatmapRes.json();
      const stageTemporalPayload = await stageTemporalRes.json();
      const eventFlowPayload = await eventFlowRes.json();
      setHeatmapData(temporalHeatmapPayload || null);

      setInsightsData(prev => ({
        ...(prev || {}),
        logistics_root_cause: {
          ...((prev && prev.logistics_root_cause) || {}),
          disposition_mix: logisticsPayload.logistics_root_cause.disposition_mix || [],
          top_chief_complaints: logisticsPayload.logistics_root_cause.top_chief_complaints || []
        },
        equity_audit: demographicsPayload.equity_audit || [],
        chief_complaint_bottlenecks: bottlenecksPayload.chief_complaint_bottlenecks || [],
        efficiency_stress_test: volumeEfficiencyPayload.correlation_chart || [],
        disposition_chart: dispositionsPayload.disposition_milestone_analysis || [],
        acuity_chart: acuityPayload.acuity_level_analysis || [],
        stage_temporal_forecast: stageTemporalPayload || null,
        event_flow_forecast: eventFlowPayload || null
      }));
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.warn('Falling back to mock data', err);
        setError(err.message);
        setInsightsData(mockData);
        setIsUsingMockData(true);
      }
    } finally {
      setLoading(false);
    }
  };

  fetchInsights();
  return () => controller.abort(); // Cleanup
}, []);

  const correlationPoints = (insightsData?.efficiency_stress_test || [])
    .map((item) => ({
      x: Number(item.patient_volume),
      y: Number(item.p90_wait_time),
    }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));

  const correlationX = correlationPoints.map((point) => point.x);
  const correlationY = correlationPoints.map((point) => point.y);
  const correlationTrend = buildTrendLine(correlationPoints);
  // Fit the chart to the observed data so small datasets do not sit in a huge static range.
  const correlationXRange = getAxisRange(correlationX, { minPad: 10, padRatio: 0.12 });
  const correlationYRange = getAxisRange(correlationY, { minPad: 10, padRatio: 0.12 });
  const dispositionMix = insightsData?.logistics_root_cause?.disposition_mix || [];
  const dispositionTotalCount = dispositionMix.every((item) => Number.isFinite(Number(item.count)))
    ? dispositionMix.reduce((total, item) => total + Number(item.count), 0)
    : null;

  // Helper function to transform temporal_summary heatmap data into display format
  const generateHeatmapData = () => {
    const defaultDayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const defaultSliceLabels = ['Dawn ', 'Morning', 'Afternoon', 'Night '];
    const defaultMatrix = Array(7).fill(null).map(() => Array(4).fill(0));

    const dayNames = heatmapData?.day_labels || mockData?.heatmap_data?.y_days || defaultDayNames;
    const sliceLabels = heatmapData?.slice_labels || mockData?.heatmap_data?.x_hours || defaultSliceLabels;
    const volumeMatrix = heatmapData?.volume_matrix || mockData?.heatmap_data?.z_matrix || defaultMatrix;

    return { matrix: volumeMatrix, dayNames, sliceLabels };
  };

  const { matrix: heatmapMatrix, dayNames, sliceLabels } = generateHeatmapData();

  const stageForecast = insightsData?.stage_temporal_forecast || null;
  const eventFlowForecast = insightsData?.event_flow_forecast || null;
  const stageHourlyRisk = stageForecast?.today_hourly_risk || [];
  const contextNow = stageForecast?.current_context || null;
  const currentSlot = stageForecast?.current_slot || null;
  const nextSlot = stageForecast?.next_slot || null;
  const currentDaySummary = stageForecast?.current_day_summary || null;
  const nextDaySummary = stageForecast?.next_day_summary || null;
  const stageAlerts = stageForecast?.alerts || [];
  const topFlowRisks = eventFlowForecast?.top_delay_flows || [];

  const stageRiskOrZero = (slot, key) => Number(slot?.[key] ?? 0);
  const maxStageRisk = (slot) => Math.max(
    stageRiskOrZero(slot, 'vital'),
    stageRiskOrZero(slot, 'medrecon'),
    stageRiskOrZero(slot, 'dispen'),
    stageRiskOrZero(slot, 'discharge')
  );

  if (loading && !insightsData) {
    return (
      <div className="insights_container">
        <section className="insight_block">
          <h3>Insights</h3>
          <p className="insights_status_message">Loading live insights data...</p>
        </section>
      </div>
    );
  }


    return (
    <div className="insights_container">
      {isUsingMockData ? (
        <section className="insight_block insights_status_warning">
          <p className="insights_status_message">
            Live API data is currently unavailable. Showing mock data for demonstration.
            {error ? ` (${error})` : ''}
          </p>
        </section>
      ) : null}
      {/* SECTION 1: THE FORECAST HUB */}
      <section className="insight_block forecast_hub">
        <h3>Proactive Analytics & Forecasting</h3>
        <div className="forecast_grid">
          <div className="forecast_chart">
            {/* Stage-specific bottleneck risk by hour (today) */}
            <Plot
              data={[
                {
                  x: stageHourlyRisk.map((r) => r.time_label),
                  y: stageHourlyRisk.map((r) => Number(r.vital || 0)),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Vitals',
                  line: { color: '#2563eb', width: 2 }
                },
                {
                  x: stageHourlyRisk.map((r) => r.time_label),
                  y: stageHourlyRisk.map((r) => Number(r.medrecon || 0)),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Med Recon',
                  line: { color: '#f59e0b', width: 2 }
                },
                {
                  x: stageHourlyRisk.map((r) => r.time_label),
                  y: stageHourlyRisk.map((r) => Number(r.dispen || 0)),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Dispensing',
                  line: { color: '#9333ea', width: 2 }
                },
                {
                  x: stageHourlyRisk.map((r) => r.time_label),
                  y: stageHourlyRisk.map((r) => Number(r.discharge || 0)),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Discharge',
                  line: { color: '#dc2626', width: 2 }
                }
              ]}
              layout={{
                height: 350,
                margin: { t: 30, b: 60, l: 60, r: 20 },
                xaxis: {
                  title: { text: 'Hour (Today)', standoff: 15 },
                  automargin: true,
                  tickangle: -45
                },
                yaxis: {
                  title: { text: 'Bottleneck Risk (%)', standoff: 15 },
                  automargin: true,
                  range: [0, 100]
                },
                legend: { orientation: 'h', y: -0.25 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                shapes: contextNow ? [
                  {
                    type: 'line',
                    x0: `${String(contextNow.hour_of_day).padStart(2, '0')}:00`,
                    x1: `${String(contextNow.hour_of_day).padStart(2, '0')}:00`,
                    y0: 0,
                    y1: 100,
                    line: { color: '#0f172a', dash: 'dot', width: 1 }
                  }
                ] : []
              }}
              useResizeHandler={true}
              style={{ width: '100%' }}
            />
          </div>
          <div className="risk_cards_container">
            <div className="risk_card">
              <h4>Now</h4>
              <p className="risk_metric">{contextNow ? `${contextNow.day_label} ${String(contextNow.hour_of_day).padStart(2, '0')}:00` : 'N/A'}</p>
              <p className="risk_value">Max Stage Risk: {Math.round(maxStageRisk(currentSlot))}%</p>
            </div>
            <div className="risk_card">
              <h4>Next Hour</h4>
              <p className="risk_metric">{contextNow ? `${contextNow.next_hour_day_label || contextNow.day_label} ${String(contextNow.next_hour_of_day).padStart(2, '0')}:00` : 'N/A'}</p>
              <p className="risk_value">Max Stage Risk: {Math.round(maxStageRisk(nextSlot))}%</p>
            </div>
            <div className="risk_card">
              <h4>Today (Day-Level)</h4>
              <p className="risk_metric">{contextNow ? contextNow.day_label : 'N/A'}</p>
              <p className="risk_value">Max Stage Risk: {Math.round(maxStageRisk(currentDaySummary))}%</p>
            </div>
            <div className="risk_card">
              <h4>Next Day (Day-Level)</h4>
              <p className="risk_metric">{contextNow ? contextNow.next_day_label : 'N/A'}</p>
              <p className="risk_value">Max Stage Risk: {Math.round(maxStageRisk(nextDaySummary))}%</p>
            </div>
            <div className="risk_card">
              <h4>Prep Recommendations</h4>
              {stageAlerts.length ? (
                <ul className="forecast_alert_list">
                  {stageAlerts.slice(0, 3).map((alert) => (
                    <li key={alert.stage}>
                      <strong>{alert.stage_label}:</strong> {alert.recommendation}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="risk_metric">No elevated next-hour stage risk detected.</p>
              )}
            </div>
            <div className="risk_card">
              <h4>High-Risk Patient Pathways</h4>
              {topFlowRisks.length ? (
                <ul className="forecast_alert_list">
                  {topFlowRisks.slice(0, 3).map((flow) => (
                    <li key={flow.event_flow}>
                      <strong>{flow.event_flow_label}</strong>: {Math.round(flow.avg_los_min)} min avg LOS ({flow.share_label || `${flow.share_pct}%`} of stays, n={flow.stay_count})
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="risk_metric">No event flow pathway trends available yet.</p>
              )}
            </div>
          </div>
        </div>
      </section>

      <div className="insights_middle_row">
        {/* SECTION 2: TEMPORAL HEATMAP */}
        <section className="insight_block heatmap_section">
          <div className="heatmap_header">
            <h3>Temporal Patterns by Day </h3>
            {/* <small style={{ color: '#64748b' }}>Aggregated to 4 slices: Dawn, Morning, Afternoon, Night.</small> */}
          </div>

          <Plot
            data={[
              {
                  z: heatmapMatrix,
                  x: sliceLabels,
                  y: dayNames,
                  type: 'heatmap',
                  colorscale: 'Viridis',
                  showscale: true,
                  colorbar: { title: 'Patient Volume' },
                  hovertemplate: '<b>%{y}</b><br>%{x}<br>Volume: %{z}<extra></extra>'
              }
            ]}
              layout={{
                title: 'Patient Volume by 6-hour Slice & Day of Week',
                autosize: true,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                margin: { t: 60, b: 60, l: 120, r: 10 },
                xaxis: { title: '6-hour Time Slice' },
                yaxis: { title: 'Day of Week' }
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '500px' }}
            />
        </section>

        {/* SECTION 3: ARRIVAL & DISPOSITION */}
        <section className="insight_block logistics_root_cause">
          <h3>Patient Flow Analysis</h3>
          {/* Plotly Bar/Sankey Chart */}
          <div className="logistics_grid_container" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          
       {/* Part A: Disposition Pie Chart */}
    <div className="chart_wrapper">
      <h4>Disposition Distribution</h4>
      <Plot
        data={[{
          values: dispositionMix.map(d => d.percentage) || [],
          labels: dispositionMix.map(d => d.type) || [],
          type: 'pie',
          hole: 0.4,
          marker: { colors: ['#2563eb', '#10b981', '#ef4444', '#f59e0b', '#94a3b8'] },
          textinfo: 'label+percent'
        }]}
        layout={{ 
          height: 320, 
          margin: { t: 10, b: 10, l: 10, r: 10 },
          showlegend: false,
          annotations: dispositionTotalCount !== null ? [{
            x: 0.5,
            y: 0.5,
            xref: 'paper',
            yref: 'paper',
            text: `<span style="font-size:28px;"><b>${dispositionTotalCount}</b></span><br><span style="font-size:15px;">patients</span>`,
            showarrow: false,
            font: { size: 18, color: '#0f172a' },
            align: 'center'
          }] : [],
          paper_bgcolor: 'transparent'
        }}
        useResizeHandler={true}
        style={{ width: '100%' }}
      />
    </div>

    {/* Part B: Chief Complaint Bottleneck Bar Chart */}
    <div className="chart_wrapper">
      <h4>Bed Occupancy Analysis by Case Mix</h4>
      <Plot
        data={[{
          x: insightsData?.chief_complaint_bottlenecks?.map(c => c.value) || [],
          y: insightsData?.chief_complaint_bottlenecks?.map(c => c.label.replaceAll('_', ' ')) || [],
          type: 'bar',
          orientation: 'h',
          marker: { color: '#6366f1' },
          text: insightsData?.chief_complaint_bottlenecks?.map(c => `${c.count} patients`) || [],
          customdata: insightsData?.chief_complaint_bottlenecks?.map(c => [c.avg_los, c.transfer_pct]) || [],
          hovertemplate:
            'Category: %{y}<br>' +
            'Total bed-hours: %{x}<br>' +
            'Patients: %{text}<br>' +
            'Avg LOS: %{customdata[0]} hours<br>' +
            'Transfer rate: %{customdata[1]}%<extra></extra>',
        }]}
        layout={{
          height: 320,
          margin: { t: 20, b: 40, l: 140, r: 20 },
          xaxis: { title: { text: 'Total Bed-Hours', standoff: 20 } },
          yaxis: { autorange: 'reversed' },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent'
        }}
        useResizeHandler={true}
        style={{ width: '100%' }}
      />
    </div>
    
  </div>
        </section>
      </div>

      {/* SECTION 4: EQUITY & VOLUME STRESS TEST */}
      <section className="insight_block bottom_audit">
        <div
          className="audit_grid"
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}
        >
          <div className="equity_audit">
            <h3>Demographic Flow Audit</h3>
            <Plot
              data={[{
                x: insightsData?.equity_audit?.map(e => e.variance) || [],
                y: insightsData?.equity_audit?.map(e => e.group) || [],
                type: 'bar',
                orientation: 'h',
                marker: {
                  color: insightsData?.equity_audit?.map(e => e.variance > 15 ? '#ef4444' : '#3b82f6')
                },
                text: insightsData?.equity_audit?.map(e => `${e.variance}%`),
                hoverinfo: 'text+y'
              }]}
              layout={{
                height: 350,
                margin: { t: 20, b: 80, l: 180, r: 20 },
                xaxis: { title: { text: '% Variance from Mean Wait', zeroline: true, standoff: 20 } },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent'
              }}
              useResizeHandler={true}
              style={{ width: '100%' }}
            />
          </div>

          <div className="volume_stress_test">
            <h3>P90 Total ED Stay Time vs. Patient Volume Correlation</h3>
            <Plot
              data={[
                {
                  x: correlationX,
                  y: correlationY,
                  mode: 'markers',
                  type: 'scatter',
                  name: 'Historical Data',
                  marker: { color: '#6366f1', size: 10 }
                },
                ...(correlationTrend ? [{
                  x: correlationTrend.x,
                  y: correlationTrend.y,
                  mode: 'lines',
                  type: 'scatter',
                  name: 'Trend Line',
                  line: { color: '#ef4444', dash: 'dot' }
                }] : [])
              ]}
              layout={{
                height: 350,
                margin: { t: 20, b: 100, l: 100, r: 20 },
                xaxis: {
                  title: {
                    text: 'Patient Volume (Current Census)',
                    standoff: 20
                  },
                  range: correlationXRange,
                  automargin: true
                },
                yaxis: {
                  title: {
                    text: 'P90 Wait Time (Min)',
                    standoff: 20
                  },
                  range: correlationYRange,
                  automargin: true
                },
                showlegend: true,
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent'
              }}
              useResizeHandler={true}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      </section>
      {/* SECTION 5: DISPOSITION & ACUITY ANALYSIS */}
      <section className="insight_block bottom_comparison">
        <div
          className="analysis_grid"
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}
        >
          <div className="disposition_chart">
            <h3>Milestone Duration: Admitted vs. Home</h3>
            {(() => {
              // 1. Check if dictionary keys match exactly (e.g., 'admitted' vs 'Admitted')
              const data = insightsData?.disposition_chart ||{};
              const admitted = data.admitted || {};
              const home = data.home || {};
              const milestoneMap = [
                    { label: 'Vitals', key: 'avg_vital' },
                    { label: 'Med Recon', key: 'avg_medrecon' },
                    { label: 'Dispensing', key: 'avg_dispen' },
                    { label: 'Discharge', key: 'avg_discharge' }
                  ];
              // 2. The labels 
              const labels = milestoneMap.map(item => item.label);
              const admittedValues = milestoneMap.map(item => Number(admitted[item.key]) || 0);
              const homeValues = milestoneMap.map(item => Number(home[item.key]) || 0);
              const admittedHoverText = milestoneMap.map(item => {
              const value = Number(admitted[item.key]) || 0;
                return `admitted_${item.label.toLowerCase().replace(/\s+/g, '')}: ${value.toFixed(1)} min`;
              });

            const homeHoverText = milestoneMap.map(item => {
            const value = Number(home[item.key]) || 0;
                return `home_${item.label.toLowerCase().replace(/\s+/g, '')}: ${value.toFixed(1)} min`;
              });
              return (
                <Plot
                  data={[
                    {
                      x: labels,
                      y: admittedValues,
                      name: 'Admitted',
                      type: 'bar',
                      // orientation: 'h', // <--- This makes it horizontal
                      marker: { color: '#2AA198' },
                      customdata: admittedHoverText,
                      hovertemplate: '%{customdata}<extra></extra>'
                    },
                    {
                      x: labels,
                      y: homeValues,
                      name: 'Home',
                      type: 'bar',
                      marker: { color: '#268BD2' },
                      customdata: homeHoverText,
                      hovertemplate: '%{customdata}<extra></extra>'
                    }
                  ]}
                  layout={{
                    height: 350,
                    barmode: 'group',
                    margin: { t: 30, b: 80, l: 60, r: 20 },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.1 },
                    xaxis: { 
                    title: 'ED Milestones', 
                    tickangle: -45, // Slants labels so they don't overlap
                    automargin: true,
                    showgrid: false,
                    showline: true,
                    linecolor: "#000",
                    linewidth: 1,
                    mirror: false
                    },
                    yaxis: { 
                      title: 'Avg Duration (Min)', 
                      gridcolor: '#e2e8f0',
                      automargin: true,
                      showgrid: false,
                      showline: true,
                      linecolor: "#000",
                      linewidth: 1,
                      zeroline: false  
                    }
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%' }}
                />
              );
            })()}
          </div>

          <div className="acuity_chart">
            <h3>Stay Duration by Acuity Level</h3>
            {(() => {
              const rawData = Array.isArray(insightsData?.acuity_chart)
                ? insightsData.acuity_chart
                : [];

              const sortedData = [...rawData].sort((a, b) => a.scale_level - b.scale_level);

              const milestoneMap = [
                { label: 'Vitals', key: 'avg_vital' },
                { label: 'Med Recon', key: 'avg_medrecon' },
                { label: 'Dispensing', key: 'avg_dispen' },
                { label: 'Discharge', key: 'avg_discharge' }
              ];

              const levelColorMap = {
                1: '#2563eb',
                2: '#ef4444',
                3: '#f59e0b',
                4: '#10b981',
                5: '#94a3b8'
              };

              const traces = sortedData.map(level => {
              const levelLabel = `Level ${level.scale_level}`;

              const hoverText = milestoneMap.map(item => {
                const value = Number(level[item.key]) || 0;
                return `${levelLabel.toLowerCase().replace(' ', '_')}_${item.label.toLowerCase().replace(/\s+/g, '')}: ${value.toFixed(1)} min`;
              });

              return {
                x: milestoneMap.map(item => item.label),
                y: milestoneMap.map(item => Number(level[item.key]) || 0),
                name: levelLabel,
                type: 'bar',
                marker: { color: levelColorMap[level.scale_level] || '#64748b' },
                customdata: hoverText,
                hovertemplate: '%{customdata}<extra></extra>'
              };
            });
              return (
                <Plot
                  data={traces}
                  layout={{
                    height: 420,
                    barmode: 'group',
                    margin: { t: 30, b: 80, l: 60, r: 20 },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    legend: {
                      orientation: 'h',
                      x: 0.5,
                      xanchor: 'center',
                      y: 1.15
                    },
                    xaxis:  {
                      title: 'ED Milestones',
                      tickangle: -30,
                      automargin: true,
                      showgrid: false,
                      showline: true,
                      linecolor: '#000',
                      linewidth: 1
                    },
                    yaxis: {
                      title: 'Avg Duration (Min)',
                      automargin: true,
                      showgrid: false,
                      showline: true,
                      linecolor: '#000',
                      linewidth: 1,
                      zeroline: false
                    }
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '350px' }}
                />
                );
            })()}
              </div>
        </div>
      </section>
    </div>
  );
};

export default InsightsPage;
