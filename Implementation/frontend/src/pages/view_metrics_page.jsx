import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend, ReferenceLine 
} from 'recharts';
// import Banner from './Banner'; // Your existing separate JSX
import BottleneckBanner from '../components/bottleneck_banner';
import '../view_metrics.css';
import mockData from "../view_metrics_mock.json";


const ViewMetrics = () => {
  // These states would be populated by your 'metrics' table row
  const [selectedStage, setSelectedStage] = useState('triage_to_vital');
  const [lookback, setLookback] = useState(10);
  //for teh data cards
  const cardConfigs = [
    { label: "ENTRY → TRIAGE", key: "entry_to_triage" },
    { label: "TRIAGE → VITALS", key: "triage_to_vitals" },
    { label: "VITALS → MEDRECON", key: "vitals_to_medrecon" },
    { label: "MEDRECON → DISPENSE", key: "medrecon_to_dispense" },
    { label: "DISPENSE → EXIT", key: "dispense_to_exit" }
  ];
  // helper function for the arrows in the card
  const getTrendClass = (dir) => {
    if (dir === 'up') return 'trend_up';   // Red/Up for ED wait times
    if (dir === 'down') return 'trend_down'; // Green/Down for ED wait times
    return ''; 
  };

  const getTrendIcon = (dir) => {
    if (dir === 'up') return '▲';
    if (dir === 'down') return '▼';
    return '';
  };
  //for the line chart
  const [percentileLevel, setPercentileLevel] = useState('p90'); // Default to P90
  const activeDataKey = `${selectedStage}_${percentileLevel}`; //used for the line chart to determine what is shown based on user selection
  // Use a separate variable for the display label in the Legend/Tooltip
  const displayLabel = `${selectedStage.replace(/_/g, ' ')} (${percentileLevel.toUpperCase()})`;
  // Helper to make the Legend/Tooltip look nice
  const getLabel = () => {
    const stageName = selectedStage.replace(/_/g, ' ').toUpperCase();
    const levelName = percentileLevel.toUpperCase();
    return `${stageName} (${levelName})`;
  };
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    setDashboardData(mockData)
  })

  // 1. Determine which keys to pull from the JSON based on state
    const p90Key = `${selectedStage}_p90`;
    const p75Key = `${selectedStage}_p75`;
    const p50Key = `${selectedStage}_p50`;
    const baselineLabel = "AVERAGE FLOW (P50)";
    const focusLabel = `${selectedStage.replace(/_/g, ' ').toUpperCase()} (${percentileLevel.toUpperCase()})`;

  

  return (
    <div className="view_metrics_page_wrapper">
      <div className="dashboard_container">
        
        {/* 1. SYSTEM STATUS BANNER */}
        <section className="dashboard_header_section">
          <BottleneckBanner /> 
        </section>

        

        {/* 2. OPERATIONAL FLOW CARDS (The "Now") */}
        <div className="metrics_grid_flow">
          {/* HERO CARD: THE NORTH STAR METRIC */}
          <div className="metric_card_mini hero_card">
            <span className="stat_label_mini">AVG STAY TIME</span>
            <div className="card_body_mini">
              <span className="stat_value_large">
                {dashboardData?.summary.avg_stay.value ?? '--'}
                <small className="stat_unit">m</small>
              </span>
              <span className={`trend_indicator ${getTrendClass(dashboardData?.summary.avg_stay.direction)}`}>
                {getTrendIcon(dashboardData?.summary.avg_stay.direction)} {dashboardData?.summary.avg_stay.trend}m
              </span>
            </div>
          </div>
          
          {/* Card 1: Entry to Triage */}

          {cardConfigs.map((card) => {
            const data = dashboardData?.summary[card.key];
            return (
              <div className="metric_card_mini" key={card.key}>
                <span className="stat_label_mini">{card.label}</span>
                <div className="card_body_mini">
                  <span className="stat_value_large">
                    {data?.value ?? '--'}
                    <small className="stat_unit">m</small>
                  </span>
                  <span className={`trend_indicator ${getTrendClass(data?.direction)}`}>
                    {getTrendIcon(data?.direction)} {data?.trend}m
                  </span>
                </div>
              </div>
            );
          })}
         
        </div>
        {/* 3. NEW: DASHBOARD CONTROLS & DATA HORIZON */}
<div className="dashboard_controls_bar">
  <div className="control_group">
    <div className="control_item">
      <label>Metric Focus</label>
      <select 
        className="global_percentile_dropdown"
        value={selectedStage}
        onChange={(e) => setSelectedStage(e.target.value)}
      >
        <option value="total_stay">Total Stay Time</option>
        <option value="triage_to_vital">Triage to Vitals</option>
        <option value="vital_to_medrecon">Vitals to MedRecon</option>
        <option value="medrecon_to_dispense">MedRecon to Dispense</option>
        <option value="dispense_to_exit">Dispense to Exit</option>
      </select>
    </div>

    <div className="control_item">
      <label>Analysis Level</label>
      <select className="global_percentile_dropdown" value={percentileLevel}
       onChange={(e) => setPercentileLevel(e.target.value)}>
        <option value="p90">p90 (Slowest 10%)</option>
        <option value="p75">p75 (Slowest 25%)</option>
        <option value="p50">p50 (Average Flow)</option>
      </select>
    </div>
  </div>

  {/* THE DATA WINDOW & SYNC STATUS */}
  <div className="data_horizon_badge">
    <span className="horizon_label">Operational Window</span>
    <span className="horizon_value">Feb 22, 2026 | 08:00 - 14:00</span>
    <div className="sync_status">
      <span className="live_dot"></span> 
      Last Sync: 2m ago
    </div>
  </div>
</div>

        {/* 3. INTERACTIVE PERFORMANCE TREND (The "History") */}
        <section className="trend_chart_section">
          <div className="chart_controls_row">
            <h3 className="visual_header">Performance Trend Analysis</h3>
            <div className="control_group">
              <select 
                className="global_percentile_dropdown"
                value={selectedStage}
                onChange={(e) => setSelectedStage(e.target.value)}
              >
                <option value="total_stay">Total Stay Time</option>
                <option value="triage_to_vital">Triage to Vitals</option>
                <option value="vital_to_medrecon">Vitals to MedRecon</option>
                <option value="medrecon_to_dispense">MedRecon to Dispense</option>
                <option value="dispense_to_exit">Dispense to Exit</option>
              </select>
              
              <select 
                className="global_percentile_dropdown"
                value={lookback}
                onChange={(e) => setLookback(e.target.value)}
              >
                <option value={5}>Last 5 Uploads</option>
                <option value={10}>Last 10 Uploads</option>
                <option value={20}>Last 20 Uploads</option>
              </select>
            </div>
          </div>
          
          <div style={{ width: '100%', height: 350 }}>
            <ResponsiveContainer>
             
              {/* <LineChart data={dashboardData?.trend_chart ?? []}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="period_start" />
              <YAxis unit="m" />
              <Tooltip />
              <Legend />

              {/* P90: The Bottleneck (Thickest) 
              <Line 
                name="P90 (Slowest 10%)" 
                type="monotone" 
                dataKey={p90Key} 
                stroke="#ef4444" // Red: High Stress
                strokeWidth={3} 
                dot={{ r: 4 }}
              />

              {/* P75: The At-Risk Group (Medium) 
              <Line 
                name="P75 (Slowest 25%)" 
                type="monotone" 
                dataKey={p75Key} 
                stroke="#f59e0b" // Orange: Warning
                strokeWidth={2} 
                strokeDasharray="5 5"
              />

              {/* P50: The Median (Thinnest) 
              <Line 
                name="P50 (Median)" 
                type="monotone" 
                dataKey={p50Key} 
                stroke="#94a3b8" // Gray: Baseline
                strokeWidth={1}
              />
            </LineChart> */}
          <LineChart data={dashboardData?.trend_chart ?? []}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="period_start" stroke="#64748b" fontSize={12} />
            <YAxis unit="m" stroke="#64748b" fontSize={12} />
            <Tooltip />
            <Legend />
            
            {/* <ReferenceLine y={60} label="Target" stroke="#ef4444" strokeDasharray="5 5" /> */}
            {/* we do not have a reference. We can add it if we find it*/}
            {/* ONLY ONE LINE RENDERS */}
            <Line 
              name={displayLabel} 
              type="monotone" 
              dataKey={activeDataKey} 
              stroke="#4338CA" // Keep a consistent strong color for the active metric
              strokeWidth={3} 
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              animationDuration={500} // Smooth transition when the line "jumps" to new data
            />
            <Line 
              name={baselineLabel} 
              type="monotone" 
              dataKey={p50Key} 
              stroke="#94a3b8" // Slate Gray
              strokeWidth={2} 
              strokeDasharray="5 5" // Dashed to show it's a reference
              dot={false} // Remove dots to keep it clean
            />
          </LineChart>

            </ResponsiveContainer>
          </div>
        </section>

        {/* 4. LOGISTICS ROW: VOLUME & ACUITY (The "Why") */}
        <div className="data_visual_row">
          
          {/* Stacked Hourly Volume */}
          <div className="visual_container">
            <h3 className="visual_header">Hourly Patient Density (Acuity Mix)</h3>
            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <BarChart data={dashboardData?.volume_chart ?? [] /* Data from your hourly aggregation API */}>
                  <XAxis dataKey="hour" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="Level 1" stackId="a" fill="#2563eb" />
                  <Bar dataKey="Level 2" stackId="a" fill="#ef4444" />
                  <Bar dataKey="Level 3" stackId="a" fill="#f59e0b" />
                  <Bar dataKey="Level 4" stackId="a" fill="#10b981" />
                  <Bar dataKey="Level 5" stackId="a" fill="#94a3b8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* Acuity Benchmarking Table */}
          <div className="visual_container">
            <h3 className="visual_header">Acuity Benchmarking</h3>
            <div className="acuity_table_labels">
              <span>PRIORITY LEVEL</span>
              <span>AVG STAY</span>
              <span>VS DEPT AVG</span>
            </div>

            {dashboardData?.acuity_benchmarks.map((item, index)=> (
              <div className='acuity_row' key={index}>
                <div className="acuity_name_wrapper">
                  <span className="acuity_color_indicator" style={{ backgroundColor: item.color }}></span>
                <span className="acuity_name">{item.name}</span>
                </div>
                <span className="stat_avg">{item.avg}</span>
                <span className={`benchmark_pill ${item.type === 'good' ? 'pill_good' : 'pill_warning'}`}>{item.diff}</span>
              </div>
            ))}
            
          </div>
        </div>

      </div>
    </div>
  );
};

export default ViewMetrics;