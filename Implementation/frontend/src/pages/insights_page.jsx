import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js'; // You'll need to install this
import BottleneckBanner from '../components/bottleneck_banner';
import '../insights.css';
import mockData from "../insights_mock.json";


const InsightsPage = () => {
  const [insightsData, setInsightsData] = useState(mockData);
  const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

useEffect(() => {
  const controller = new AbortController();

  const fetchDispositionMix = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/insights/logistics_root_cause', {
        signal: controller.signal 
      });

      if (!response.ok) throw new Error(`Error: ${response.status}`);

      const payload = await response.json();
      
      setInsightsData(prev => ({
        ...prev,
        logistics_root_cause: {
          ...prev.logistics_root_cause,
          disposition_mix: payload.logistics_root_cause.disposition_mix
        },
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

  fetchDispositionMix();
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

    {/* Part B: Chief Complaint Delay Bar Chart */}
    <div className="chart_wrapper">
      <h4>Delay Impact by Chief Complaint</h4>
      <Plot
        data={[{
          // Extracting the number from "+18m" so the bar has a length
          x: mockData?.logistics_root_cause?.top_complaints?.map(c => parseInt(c.delay_impact)) || [],
          y: mockData?.logistics_root_cause?.top_complaints?.map(c => c.complaint) || [],
          type: 'bar',
          orientation: 'h',
          marker: { color: '#6366f1' },
          text: mockData?.top_complaints?.map(c => c.delay_impact), // Shows the "+18m" on hover
          hoverinfo: 'text+y'
        }]}
        layout={{
          height: 320,
          margin: { t: 20, b: 40, l: 140, r: 20 },
          xaxis: { title: {text:'Minutes of Delay Impact', standoff:20} },
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
       <div className="audit_grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
    
    {/* Part A: Demographic Flow Audit */}
    <div className="equity_audit">
      <h3>Demographic Flow Audit</h3>
      <Plot
        data={[{
          x: mockData?.equity_audit?.map(e => e.variance) || [],
          y: mockData?.equity_audit?.map(e => e.group) || [],
          type: 'bar',
          orientation: 'h',
          marker: {
            color: mockData?.equity_audit?.map(e => e.variance > 15 ? '#ef4444' : '#3b82f6') 
          },
          text: mockData?.equity_audit?.map(e => `${e.variance}%`),
          hoverinfo: 'text+y'
        }]}
        layout={{
          height: 350,
          margin: { t: 20, b: 80, l: 180, r: 20 },
          xaxis: { title: {text: '% Variance from Mean Wait', zeroline: true, standoff:20} },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent'
        }}
        useResizeHandler={true}
        style={{ width: '100%' }}
      />
    </div>

    {/* Part B: Efficiency vs. Volume Correlation (The Stress Test) */}
    <div className="volume_stress_test">
      <h3>Efficiency vs. Volume Correlation</h3>
      <Plot
        data={[
          {
            x: mockData?.efficiency_stress_test?.map(s => s.volume) || [],
            y: mockData?.efficiency_stress_test?.map(s => s.p90_wait) || [],
            mode: 'markers',
            type: 'scatter',
            name: 'Historical Data',
            marker: { color: '#6366f1', size: 10 }
          },
          {
            // Simple regression line logic
            x: [12, 62],
            y: [35, 275],
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
                // Title must be an object to use 'standoff' and 'text'
                title: { 
                text: 'Patient Volume (Current Census)', 
                standoff: 20 
                },
                automargin: true // Automatically expands the margin to fit the title
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
    </div>
  );
};

export default InsightsPage;