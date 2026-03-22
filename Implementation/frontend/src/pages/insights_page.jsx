import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js'; // You'll need to install this
import BottleneckBanner from '../components/bottleneck_banner';
import '../insights.css';
import mockData from "../insights_mock.json";
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend, ReferenceLine 
} from 'recharts';

const InsightsPage = () => {
  const [insightsData, setInsightsData] = useState(mockData); // Initially set to mock data for development
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

useEffect(() => {
  const controller = new AbortController();

  const fetchInsights = async () => {
    try {
      setLoading(true);

      const [logisticsRes, demographicsRes, bottlenecksRes, volumeEfficiencyRes, dispositionsRes, acuityRes] = await Promise.all([
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
        })
      ]);
      if (!logisticsRes.ok) throw new Error(`Logistics Error: ${logisticsRes.status}`);
      if (!demographicsRes.ok) throw new Error(`Demographics Error: ${demographicsRes.status}`);
      if (!bottlenecksRes.ok) throw new Error(`Chief Complaint Bottlenecks Error: ${bottlenecksRes.status}`);
      if (!volumeEfficiencyRes.ok) throw new Error(`Volume-Efficiency Correlation Error: ${volumeEfficiencyRes.status}`);
      if (!dispositionsRes.ok) throw new Error(`Disposition Comparison Error: ${dispositionsRes.status}`);
      if (!acuityRes.ok) throw new Error(`Acuity Level Analysis Error: ${acuityRes.status}`);


      const logisticsPayload = await logisticsRes.json();
      const demographicsPayload = await demographicsRes.json();
      const bottlenecksPayload = await bottlenecksRes.json();
      const volumeEfficiencyPayload = await volumeEfficiencyRes.json();
      const dispositionsPayload = await dispositionsRes.json();
      const acuityPayload = await acuityRes.json();

      setInsightsData(prev => ({
        ...prev,
        logistics_root_cause: {
          ...prev.logistics_root_cause,
          disposition_mix: logisticsPayload.logistics_root_cause.disposition_mix || [],
          top_chief_complaints: logisticsPayload.logistics_root_cause.top_chief_complaints || []
        },
        equity_audit: demographicsPayload.equity_audit || [],
        chief_complaint_bottlenecks: bottlenecksPayload.chief_complaint_bottlenecks || [],
        efficiency_stress_test: volumeEfficiencyPayload.correlation_chart || [],
        disposition_chart: dispositionsPayload.disposition_milestone_analysis || [],
        acuity_chart: acuityPayload.acuity_level_analysis || []
      }));
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.warn('Falling back to mock data', err);
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  fetchInsights();
  return () => controller.abort(); // Cleanup
}, []);

    return (
    <div className="insights_container">
      {/* SECTION 1: THE FORECAST HUB */}
      <section className="insight_block forecast_hub">
        <h3>Proactive Analytics & Forecasting</h3>
        <div className="forecast_grid">
          <div className="forecast_chart">
            {/* Plotly Volume Forecast Line Chart */}
            <Plot
    data={[
      {
        x: mockData?.forecast_hub?.labels || [],
        y: mockData?.forecast_hub?.actual_volume || [],
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Actual Volume',
        line: { color: '#6366f1', width: 3 },
        marker: { size: 6 }
      },
      {
        x: mockData?.forecast_hub?.labels || [],
        y: mockData?.forecast_hub?.predicted_volume || [],
        type: 'scatter',
        mode: 'lines',
        name: 'Forecasted Volume',
        line: { color: '#6366f1', width: 3, dash: 'dot' },
        connectgaps: true // Ensures the line joins the last 'Actual' point
      }
    ]}
    layout={{
      height: 350,
      margin: { t: 30, b: 60, l: 60, r: 20 },
      xaxis: { 
        title: { text: 'Time of Day', standoff: 15 },
        automargin: true 
      },
      yaxis: { 
        title: { text: 'Patient Count', standoff: 15 },
        automargin: true 
      },
      legend: { orientation: 'h', y: -0.2 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent'
    }}
    useResizeHandler={true}
    style={{ width: '100%' }}
  />
          </div>
          <div className="risk_cards_container">
            {/* Risk Probability Cards */}
          </div>
        </div>
      </section>

      <div className="insights_middle_row">
        {/* SECTION 2: LOGISTICS HEATMAP */}
        <section className="insight_block heatmap_section">
          <h3>Temporal Bottleneck Patterns (P90 Gap)</h3>
          {/* Plotly Heatmap */}
          <Plot
  data={[
    {
      z: [[10, 20, 30], [20, 50, 60], [30, 60, 90]], // P90 Values
      x: ['Morning', 'Afternoon', 'Evening'],
      y: ['Monday', 'Tuesday', 'Wednesday'],
      type: 'heatmap',
      colorscale: 'Viridis',
      showscale: true,
    }
  ]}
  layout={{ 
    title: 'Peak Bottleneck Hours',
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { t: 40, b: 40, l: 60, r: 10 }
  }}
  useResizeHandler={true}
  style={{ width: '100%', height: '300px' }}
/>
        </section>

        {/* SECTION 3: ARRIVAL & DISPOSITION */}
        <section className="insight_block logistics_root_cause">
          <h3>Logistics Root Cause Analysis</h3>
          {/* Plotly Bar/Sankey Chart */}
          <div className="logistics_grid_container" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          
       {/* Part A: Disposition Pie Chart */}
    <div className="chart_wrapper">
      <h4>Disposition Distribution</h4>
      <Plot
        data={[{
          values: insightsData?.logistics_root_cause?.disposition_mix?.map(d => d.percentage) || [],
          labels: insightsData?.logistics_root_cause?.disposition_mix?.map(d => d.type) || [],
          type: 'pie',
          hole: 0.4,
          marker: { colors: ['#2563eb', '#10b981', '#ef4444', '#f59e0b', '#94a3b8'] },
          textinfo: 'label+percent'
        }]}
        layout={{ 
          height: 320, 
          margin: { t: 10, b: 10, l: 10, r: 10 },
          showlegend: false,
          paper_bgcolor: 'transparent'
        }}
        useResizeHandler={true}
        style={{ width: '100%' }}
      />
    </div>

    {/* Part B: Chief Complaint Bottleneck Bar Chart */}
    <div className="chart_wrapper">
      <h4>Chief Complaint Bottleneck Categories</h4>
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
            <h3>Efficiency vs. Volume Correlation</h3>
            <Plot
              data={[
                {
                  x: insightsData?.efficiency_stress_test?.map(s => s.patient_volume) || [],
                  y: insightsData?.efficiency_stress_test?.map(s => s.p90_wait_time) || [],
                  mode: 'markers',
                  type: 'scatter',
                  name: 'Historical Data',
                  marker: { color: '#6366f1', size: 10 }
                },
                {
                  x: [100, 125],
                  y: [600, 900],
                  mode: 'lines',
                  type: 'scatter',
                  name: 'Trend Line',
                  line: { color: '#ef4444', dash: 'dot' }
                }
              ]}
              layout={{
                height: 350,
                margin: { t: 20, b: 100, l: 100, r: 20 },
                xaxis: {
                  title: {
                    text: 'Patient Volume (Current Census)',
                    standoff: 20
                  },
                  automargin: true
                },
                yaxis: {
                  title: {
                    text: 'P90 Wait Time (Min)',
                    standoff: 20
                  },
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
                      marker: { color: '#f5e20bac' },
                      customdata: admittedHoverText,
                      hovertemplate: '%{customdata}<extra></extra>'
                    },
                    {
                      x: labels,
                      y: homeValues,
                      name: 'Home',
                      type: 'bar',
                      marker: { color: '#2563eb' },
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
