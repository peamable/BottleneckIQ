import React, { useState } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend, ReferenceLine 
} from 'recharts';
// import Banner from './Banner'; // Your existing separate JSX
import BottleneckBanner from '../components/bottleneck_banner';
import '../view_metrics.css';


const ViewMetrics = () => {
  // These states would be populated by your 'metrics' table row
  const [selectedStage, setSelectedStage] = useState('triage_to_vital');
  const [lookback, setLookback] = useState(10);

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
              <span className="stat_value_large">185<small className="stat_unit">m</small></span>
              <span className="trend_indicator trend_up">▲ 12m</span>
            </div>
          </div>
          
          {/* Card 1: Entry to Triage */}
          <div className="metric_card_mini">
            <span className="stat_label_mini">ENTRY → TRIAGE</span>
            <div className="card_body_mini">
              <span className="stat_value_large">42<small className="stat_unit">m</small></span>
              <span className="trend_indicator trend_up">▲ 4m</span>
            </div>
          </div>

          {/* Card 2: Triage to Vitals */}
          <div className="metric_card_mini">
            <span className="stat_label_mini">TRIAGE → VITALS</span>
            <div className="card_body_mini">
              <span className="stat_value_large">18<small className="stat_unit">m</small></span>
              <span className="trend_indicator trend_down">▼ 2m</span>
            </div>
          </div>

          {/* Card 3: Vitals to MedRecon */}
          <div className="metric_card_mini">
            <span className="stat_label_mini">VITALS → MEDRECON</span>
            <div className="card_body_mini">
              <span className="stat_value_large">115<small className="stat_unit">m</small></span>
              <span className="trend_indicator trend_up">▲ 12m</span>
            </div>
          </div>

          {/* Card 4: MedRecon to Dispense */}
          <div className="metric_card_mini">
            <span className="stat_label_mini">MEDRECON → DISPENSE</span>
            <div className="card_body_mini">
              <span className="stat_value_large">30<small className="stat_unit">m</small></span>
              <span className="trend_indicator">--</span>
            </div>
          </div>

          {/* Card 5: Dispense to Discharge */}
          <div className="metric_card_mini">
            <span className="stat_label_mini">DISPENSE → EXIT</span>
            <div className="card_body_mini">
              <span className="stat_value_large">55<small className="stat_unit">m</small></span>
              <span className="trend_indicator trend_down">▼ 8m</span>
            </div>
          </div>
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
      </select>
    </div>

    <div className="control_item">
      <label>Analysis Level</label>
      <select className="global_percentile_dropdown">
        <option>P90 (Bottleneck Focus)</option>
        <option>P50 (Average Flow)</option>
      </select>
    </div>
  </div>

  {/* THE DATA WINDOW & SYNC STATUS */}
  <div className="data_horizon_badge">
    <span className="horizon_label">Operational Window</span>
    <span className="horizon_value">Feb 12, 2026 | 08:00 - 14:00</span>
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
                <option value="triage_to_vital">Triage to Vitals</option>
                <option value="vital_to_medrecon">Vitals to MedRecon</option>
                <option value="total_stay">Total Stay Time</option>
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
              <LineChart data={[] /* Data from your metrics history API */}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="period_start" hide />
                <YAxis unit="m" stroke="#64748b" fontSize={12} />
                <Tooltip />
                <ReferenceLine y={60} label="Target" stroke="#ef4444" strokeDasharray="5 5" />
                <Line type="monotone" dataKey="p90_value" stroke="#4338CA" strokeWidth={3} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="avg_value" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 5" />
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
                <BarChart data={[] /* Data from your hourly aggregation API */}>
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
            
            {/* Example Acuity Row */}
            <div className="acuity_row">
              <span className="acuity_name">Level 2 (Emergent)</span>
              <span className="stat_avg">210m</span>
              <span className="benchmark_pill pill_warning">+25m</span>
            </div>
            <div className="acuity_row">
              <span className="acuity_name">Level 4 (Less Urgent)</span>
              <span className="stat_avg">115m</span>
              <span className="benchmark_pill pill_good">-70m</span>
            </div>
            {/* ... etc */}
          </div>
        </div>

      </div>
    </div>
  );
};

export default ViewMetrics;