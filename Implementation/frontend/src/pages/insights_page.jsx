import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js'; // You'll need to install this
import BottleneckBanner from '../components/bottleneck_banner';
import '../insights.css';
import mockData from "../insights_mock.json";
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend, ReferenceLine 
} from 'recharts';

const stageOpsGuide = {
  time_to_triage: {
    label: 'Triage',
    action: 'Open rapid intake coverage and route low-acuity arrivals to fast-track screening.',
    staffing: 'Reassign an experienced triage RN or intake nurse during the surge window.',
  },
  time_to_vital: {
    label: 'Vitals',
    action: 'Move vitals capture closer to intake and pre-stage equipment in high-turn bays.',
    staffing: 'Float a tech or support RN to front-door vitals collection.',
  },
  time_to_medrecon: {
    label: 'Med Recon',
    action: 'Prioritize discharge reconciliations and clear pending pharmacy-dependent cases first.',
    staffing: 'Coordinate with pharmacy lead or assign a discharge-focused clinician to reconciliation tasks.',
  },
  time_to_dispen: {
    label: 'Dispensing',
    action: 'Pre-stage common discharge medications and batch dispense-ready patients before peak release times.',
    staffing: 'Shift pharmacy runner or discharge support toward medication handoff workload.',
  },
  time_to_discharge: {
    label: 'Discharge',
    action: 'Start discharge paperwork earlier and escalate bed-turnover coordination with the charge nurse.',
    staffing: 'Pull support from low-friction downstream work to discharge completion and transport coordination.',
  },
};

function buildBottleneckRecommendations(summary) {
  const stages = summary?.stages ?? [];
  if (!stages.length) {
    return [];
  }

  const bottleneckStages = stages.filter((stage) => stage.status === 'Bottleneck');
  const needsStages = stages.filter((stage) => stage.status === 'Needs Improvement');

  if (!bottleneckStages.length && !needsStages.length) {
    return [{
      id: 'ops-normal',
      stageKey: 'all',
      priority: 'stable',
      title: 'Operational flow stable',
      badge: 'All monitored stages normal',
      message: 'No stage is currently flagged as a bottleneck or needs-improvement concern.',
      action: 'Maintain current staffing pattern and keep discharge prep moving to preserve flow.',
      staffing: 'No immediate staffing rebalance required.',
    }];
  }

  const recommendations = [];

  if (bottleneckStages.length > 1) {
    recommendations.push({
      id: 'ops-multi-stage',
      stageKey: 'multi',
      priority: 'critical',
      title: 'Multi-stage bottleneck response',
      badge: `${bottleneckStages.length} stages in bottleneck`,
      message: 'Delays are stacking across multiple stages, which increases boarding and downstream congestion risk.',
      action: 'Run a charge-nurse huddle now and sequence work toward the most discharge-enabling patients first.',
      staffing: 'Temporarily rebalance staff away from normal stages toward the flagged stages below.',
    });
  }

  bottleneckStages.forEach((stage) => {
    const guide = stageOpsGuide[stage.stage] || {
      label: stage.stage,
      action: 'Escalate this stage for immediate flow review.',
      staffing: 'Rebalance support toward this stage until the queue stabilizes.',
    };
    recommendations.push({
      id: `ops-bottleneck-${stage.stage}`,
      stageKey: stage.stage,
      priority: 'critical',
      title: `${guide.label} bottleneck detected`,
      badge: `${Math.round((stage.bottleneck_rate || 0) * 100)}% bottleneck rate`,
      message: `${stage.bottleneck_count || 0} of ${stage.stage_total || 0} monitored encounters breached the bottleneck threshold.`,
      action: guide.action,
      staffing: guide.staffing,
    });
  });

  needsStages.forEach((stage) => {
    const guide = stageOpsGuide[stage.stage] || {
      label: stage.stage,
      action: 'Review process drift at this stage before it becomes a sustained queue.',
      staffing: 'Keep flex coverage available if the stage continues to slow.',
    };
    recommendations.push({
      id: `ops-needs-${stage.stage}`,
      stageKey: stage.stage,
      priority: 'high',
      title: `${guide.label} needs improvement`,
      badge: `${Math.round((stage.needs_improvement_rate || 0) * 100)}% needs-improvement rate`,
      message: `${stage.needs_improvement_count || 0} of ${stage.stage_total || 0} monitored encounters are drifting above the warning threshold.`,
      action: guide.action,
      staffing: guide.staffing,
    });
  });

  return recommendations;
}

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
        bottleneckStatusRes,
        volumeEfficiencyRes,
        bedOccupancyAnalysisByCaseMixRes,
        p90TotalEdStayTimeVolumeCorrelationsRes,
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
        fetch('http://localhost:8000/insights/bed-occupancy-analysis-by-case-mix', {
          signal: controller.signal
        }),
        fetch('http://localhost:8000/metrics/bottleneck-analysis', {
          signal: controller.signal
        }),
        fetch('http://localhost:8000/insights/volume-efficiency-correlation', {
        fetch('http://localhost:8000/insights/p90-total-ed-stay-time-volume-correlations', {
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
      if (!bedOccupancyAnalysisByCaseMixRes.ok) {
        throw new Error(
          `Bed Occupancy Analysis by Case Mix Error: ${bedOccupancyAnalysisByCaseMixRes.status}`
        );
      }
      if (!p90TotalEdStayTimeVolumeCorrelationsRes.ok) {
        throw new Error(
          `P90 Total ED Stay Time vs. Patient Volume Correlations Error: ${p90TotalEdStayTimeVolumeCorrelationsRes.status}`
        );
      }
      if (!dispositionsRes.ok) throw new Error(`Disposition Comparison Error: ${dispositionsRes.status}`);
      if (!acuityRes.ok) throw new Error(`Acuity Level Analysis Error: ${acuityRes.status}`);
      if (!stageTemporalRes.ok) throw new Error(`Stage Temporal Forecast Error: ${stageTemporalRes.status}`);
      if (!eventFlowRes.ok) throw new Error(`Event Flow Forecast Error: ${eventFlowRes.status}`);

      const logisticsPayload = await logisticsRes.json();
      const demographicsPayload = await demographicsRes.json();
      const bottlenecksPayload = await bottlenecksRes.json();
      const bottleneckStatusPayload = bottleneckStatusRes.ok
        ? await bottleneckStatusRes.json()
        : (mockData.bottleneck_analysis || { overall_status: 'No Data', banner_message: 'No bottleneck data available.', stages: [] });
      const volumeEfficiencyPayload = await volumeEfficiencyRes.json();
      const bedOccupancyAnalysisByCaseMixPayload = await bedOccupancyAnalysisByCaseMixRes.json();
      const p90TotalEdStayTimeVolumeCorrelationsPayload =
        await p90TotalEdStayTimeVolumeCorrelationsRes.json();
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
        bed_occupancy_analysis_by_case_mix:
          bedOccupancyAnalysisByCaseMixPayload.bed_occupancy_analysis_by_case_mix || [],
        bottleneck_analysis: bottleneckStatusPayload || null,
        p90_total_ed_stay_time_volume_correlations:
          p90TotalEdStayTimeVolumeCorrelationsPayload.p90_total_ed_stay_time_volume_correlations || [],
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

  const correlationPoints = (insightsData?.p90_total_ed_stay_time_volume_correlations || [])
    .map((item) => ({
      x: Number(item.patient_volume),
      y: Number(item.p90_total_ed_stay_time),
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
  const bottleneckAnalysis = insightsData?.bottleneck_analysis || null;
  const stageHourlyRisk = stageForecast?.today_hourly_risk || [];
  const contextNow = stageForecast?.current_context || null;
  const currentSlot = stageForecast?.current_slot || null;
  const currentDaySummary = stageForecast?.current_day_summary || null;
  const operationalContext = stageForecast?.operational_context || {};
  const escalationThreshold = Number(stageForecast?.escalation_threshold ?? 30);
  const upcomingHours = stageForecast?.upcoming_hours || [];
  const upcomingDays = stageForecast?.upcoming_days || [];
  const stageAlerts = stageForecast?.alerts || [];
  const topFlowRisks = eventFlowForecast?.top_delay_flows || [];
  const contextBadges = Object.values(operationalContext).filter(Boolean);
  const stageStatusRecommendations = buildBottleneckRecommendations(bottleneckAnalysis);
  const forecastRecommendations = stageAlerts.map((alert) => ({
    id: `forecast-${alert.stage}`,
    stageKey: `time_to_${alert.stage}`,
    priority: alert.priority || 'high',
    title: `${alert.stage_label} forecast watch`,
    badge: `${alert.target_day_label} ${alert.target_time_label}`,
    message: alert.message,
    action: alert.recommendation,
    staffing: alert.staffing_advisory,
  }));
  const hasAnyRecommendations = stageStatusRecommendations.length > 0 || forecastRecommendations.length > 0;

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
        <div className="forecast_metric_row">
          <div className="risk_card risk_card_current forecast_metric_card">
            <h4>Current Hour</h4>
            <p className="risk_metric">{contextNow ? `${contextNow.day_label} ${String(contextNow.hour_of_day).padStart(2, '0')}:00` : 'N/A'}</p>
            <p className="risk_value">Max Stage Risk: {Math.round(maxStageRisk(currentSlot))}%</p>
          </div>
          {upcomingHours.map((slot) => (
            <div key={`hour-${slot.forecast_offset_hours}-${slot.day_of_week}-${slot.hour_of_day}`} className="risk_card risk_card_hour forecast_metric_card">
              <h4>{`+${slot.forecast_offset_hours}h`}</h4>
              <p className="risk_metric">{`${slot.day_label} ${String(slot.hour_of_day).padStart(2, '0')}:00`}</p>
              <p className="risk_value">Max Stage Risk: {Math.round(maxStageRisk(slot))}%</p>
            </div>
          ))}
          <div className="risk_card risk_card_current_day forecast_metric_card">
            <h4>Current Day</h4>
            <p className="risk_metric">{contextNow ? contextNow.day_label : 'N/A'}</p>
            <p className="risk_value">Max Stage Risk: {Math.round(maxStageRisk(currentDaySummary))}%</p>
          </div>
          {upcomingDays.map((slot) => (
            <div key={`day-${slot.forecast_offset_days}-${slot.day_of_week}`} className="risk_card risk_card_day forecast_metric_card">
              <h4>{`+${slot.forecast_offset_days}d`}</h4>
              <p className="risk_metric">{slot.day_label}</p>
              <p className="risk_value">Max Stage Risk: {Math.round(maxStageRisk(slot))}%</p>
            </div>
          ))}
        </div>
        <div className="forecast_main_grid">
          <div className="forecast_chart">
            <div className="forecast_context_row">
              {contextBadges.map((badge) => (
                <div key={badge.label} className={`forecast_context_badge forecast_context_badge_${badge.status || 'stable'}`}>
                  <span className="forecast_context_label">{badge.label}</span>
                  <strong className="forecast_context_value">{badge.value_label}</strong>
                  <span className="forecast_context_detail">{badge.detail}</span>
                </div>
              ))}
            </div>
            {/* Stage-specific bottleneck risk by hour (today) */}
            <Plot
              data={[
                {
                  x: stageHourlyRisk.map((r) => r.time_label),
                  y: stageHourlyRisk.map((r) => Number(r.vital || 0)),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Vitals',
                  line: { color: '#2E5BFF', width: 3, dash: 'solid' }
                },
                {
                  x: stageHourlyRisk.map((r) => r.time_label),
                  y: stageHourlyRisk.map((r) => Number(r.medrecon || 0)),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Med Recon',
                  line: { color: '#F59E0B', width: 3, dash: 'solid' }
                },
                {
                  x: stageHourlyRisk.map((r) => r.time_label),
                  y: stageHourlyRisk.map((r) => Number(r.dispen || 0)),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Dispensing',
                  line: { color: '#10B981', width: 3, dash: 'solid' }
                },
                {
                  x: stageHourlyRisk.map((r) => r.time_label),
                  y: stageHourlyRisk.map((r) => Number(r.discharge || 0)),
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Discharge',
                  line: { color: '#64748B', width: 3, dash: 'dash' }
                }
              ]}
              layout={{
                height: 350,
                margin: { t: 30, b: 60, l: 60, r: 20 },
                xaxis: {
                  title: { text: 'Hour (Today)', standoff: 15 },
                  automargin: true,
                  showgrid: true,
                  gridcolor: '#F1F5F9',
                  tickangle: -45
                },
                yaxis: {
                  title: { text: 'Bottleneck Risk (%)', standoff: 15 },
                  automargin: true,
                  showgrid: true,
                  gridcolor: '#F1F5F9',
                  range: [0, 100]
                },
                legend: { orientation: 'h', y: -0.25 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                shapes: [
                  {
                    type: 'line',
                    x0: stageHourlyRisk[0]?.time_label || '00:00',
                    x1: stageHourlyRisk[stageHourlyRisk.length - 1]?.time_label || '23:00',
                    y0: escalationThreshold,
                    y1: escalationThreshold,
                    line: { color: '#c2410c', dash: 'dash', width: 1.5 }
                  },
                  ...(contextNow ? [
                    {
                      type: 'line',
                      x0: `${String(contextNow.hour_of_day).padStart(2, '0')}:00`,
                      x1: `${String(contextNow.hour_of_day).padStart(2, '0')}:00`,
                      y0: 0,
                      y1: 100,
                      line: { color: '#0f172a', dash: 'dot', width: 1 }
                    }
                  ] : [])
                ],
                annotations: [
                  {
                    x: stageHourlyRisk[stageHourlyRisk.length - 1]?.time_label || '23:00',
                    y: escalationThreshold,
                    xanchor: 'right',
                    yanchor: 'bottom',
                    text: 'Escalation Threshold',
                    showarrow: false,
                    font: { size: 11, color: '#9a3412' },
                    bgcolor: 'rgba(255,255,255,0.85)'
                  },
                  ...(contextNow ? [
                    {
                      x: `${String(contextNow.hour_of_day).padStart(2, '0')}:00`,
                      y: 100,
                      xanchor: 'left',
                      yanchor: 'top',
                      text: 'Now',
                      showarrow: false,
                      font: { size: 11, color: '#0f172a' },
                      bgcolor: 'rgba(255,255,255,0.85)'
                    }
                  ] : [])
                ]
              }}
              useResizeHandler={true}
              style={{ width: '100%' }}
            />
          </div>
          <div className="forecast_panel_column">
            <div className="risk_card risk_card_recommendations">
              <h4>Prep Recommendations</h4>
              {hasAnyRecommendations ? (
                <div className="forecast_recommendation_list">
                  {stageStatusRecommendations.length ? (
                    <div className="forecast_recommendation_section">
                      <p className="forecast_recommendation_section_label">Current Bottleneck Detection</p>
                      {stageStatusRecommendations.map((recommendation) => (
                        <article key={recommendation.id} className={`forecast_recommendation_item forecast_recommendation_${recommendation.priority || 'high'}`}>
                          <div className="forecast_recommendation_header">
                            <strong>{recommendation.title}</strong>
                            <span className="forecast_recommendation_time">{recommendation.badge}</span>
                          </div>
                          <p className="forecast_recommendation_message">{recommendation.message}</p>
                          <p className="forecast_recommendation_action">{recommendation.action}</p>
                          <p className="forecast_recommendation_staffing">Staffing Advisory: {recommendation.staffing}</p>
                        </article>
                      ))}
                    </div>
                  ) : null}
                  {forecastRecommendations.length ? (
                    <div className="forecast_recommendation_section">
                      <p className="forecast_recommendation_section_label">Forecast Watch</p>
                      {forecastRecommendations.map((recommendation) => (
                        <article key={recommendation.id} className={`forecast_recommendation_item forecast_recommendation_${recommendation.priority || 'high'}`}>
                          <div className="forecast_recommendation_header">
                            <strong>{recommendation.title}</strong>
                            <span className="forecast_recommendation_time">{recommendation.badge}</span>
                          </div>
                          <p className="forecast_recommendation_message">{recommendation.message}</p>
                          <p className="forecast_recommendation_action">{recommendation.action}</p>
                          <p className="forecast_recommendation_staffing">Staffing Advisory: {recommendation.staffing}</p>
                        </article>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : (
                <p className="risk_metric">No bottleneck or forecast escalation recommendations available.</p>
              )}
            </div>
            <div className="risk_card risk_card_pathways">
              <h4>High-Risk Patient Pathways</h4>
              {topFlowRisks.length ? (
                <div className="forecast_pathway_list">
                  {topFlowRisks.slice(0, 3).map((flow) => (
                    <article key={flow.event_flow} className="forecast_pathway_item">
                      <div className="forecast_pathway_header">
                        <strong>{Math.round(flow.avg_los_min)} min avg LOS</strong>
                        <span className="forecast_pathway_driver">Primary Driver: {flow.primary_driver || 'Throughput Friction'}</span>
                      </div>
                      <div className="forecast_pathway_steps">
                        {(flow.pathway_steps || []).map((step) => (
                          <span key={`${flow.event_flow}-${step.key}`} className={`forecast_pathway_step ${step.is_primary ? 'is_primary' : ''}`}>
                            {step.label}
                          </span>
                        ))}
                      </div>
                      <p className="forecast_pathway_meta">
                        Bottleneck Stage: <strong>{flow.primary_stage_label || 'Mixed'}</strong> · {flow.share_label || `${flow.share_pct}%`} of stays · n={flow.stay_count} · {flow.high_acuity_pct || 0}% high acuity
                      </p>
                      <p className="forecast_pathway_note">{flow.recommendation}</p>
                    </article>
                  ))}
                </div>
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
          <div className="logistics_grid_container" style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '20px' }}>
          
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
          height: 240, 
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

    {/* Part B: Bed Occupancy Analysis Bar Chart */}
    <div className="chart_wrapper">
      <h4>Bed Occupancy Analysis by Case Mix</h4>
      <Plot
        data={[{
          x: insightsData?.bed_occupancy_analysis_by_case_mix?.map(c => c.value) || [],
          y: insightsData?.bed_occupancy_analysis_by_case_mix?.map(c => c.label.replaceAll('_', ' ')) || [],
          type: 'bar',
          orientation: 'h',
          marker: { color: '#6366f1' },
          text: insightsData?.bed_occupancy_analysis_by_case_mix?.map(c => `${c.count} patients`) || [],
          customdata: insightsData?.bed_occupancy_analysis_by_case_mix?.map(c => [c.avg_los, c.transfer_pct]) || [],
          hovertemplate:
            'Category: %{y}<br>' +
            'Total bed-hours: %{x}<br>' +
            'Patients: %{text}<br>' +
            'Avg LOS: %{customdata[0]} hours<br>' +
            'Transfer rate: %{customdata[1]}%<extra></extra>',
        }]}
        layout={{
          height: 400,
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
