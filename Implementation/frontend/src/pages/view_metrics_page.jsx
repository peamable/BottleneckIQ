// import EmptyMetricsState from "../components/empty_metrics_state";



// // const ViewMetricsPage = () => {
// //   // TEST: Change this to 'true' to see your charts, 'false' to see the Empty State
// //   const has_data = false; 

// //   if (!has_data) {
// //     return <EmptyMetricsState />;
// //   }

// //   return (
// //     <div className="metrics_dashboard">
// //       <BottleneckBanner stage_name="Triage" />
// //       {/* Your charts go here */}
// //     </div>
// //   );
// // };

// const ViewMetricsPage = () => {
//   const has_data = false;

//   return (
//     <div className="view_metrics_page_wrapper"> 
//       <div className="metrics_content_container">
//         {!has_data ? (
//           <EmptyMetricsState />  /* The message lives inside here! */
//         ) : (
//           <div>Charts will go here</div>
//         )}
//       </div>
//     </div>
//   );
// };

// export default ViewMetricsPage

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import BottleneckBanner from '../components/bottleneck_banner';

const ViewMetricsPage = () => {
  // Mock data for the Hourly Patient Volume chart
  const hourlyData = [
    { hour: '00:00', volume: 8 }, { hour: '02:00', volume: 5 },
    { hour: '04:00', volume: 4 }, { hour: '06:00', volume: 7 },
    { hour: '08:00', volume: 15 }, { hour: '10:00', volume: 22 },
    { hour: '12:00', volume: 28 }, { hour: '14:00', volume: 25 },
    { hour: '16:00', volume: 30 }, { hour: '18:00', volume: 27 },
    { hour: '20:00', volume: 18 }, { hour: '22:00', volume: 12 },
  ];

  return (
    <div className="view_metrics_page_wrapper">
      <div className="metrics_content_container">
        {/* Banner from your reference image */}
        <BottleneckBanner stage_name="Triage to Vitals" delay_time="45" />

        {/* 1. Metrics Cards Grid */}
        <div className="metrics_grid">
          <MetricCard title="Total Stay Time" avg="185" p90="320" />
          <MetricCard title="Entry to Triage" avg="12" p90="28" />
          <MetricCard title="Triage to Vitals" avg="45" p90="95" isBottleneck={true} />
          <MetricCard title="Vitals to Med Recon" avg="22" p90="48" />
          <MetricCard title="Med Recon to Dispense" avg="38" p90="72" />
          <MetricCard title="Dispense to Discharge" avg="68" p90="124" />
        </div>

        {/* 2. Hourly Patient Volume Chart */}
        <div className="main_chart_container">
          <h3>Hourly Patient Volume</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={hourlyData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
              <XAxis dataKey="hour" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
              />
              <Bar dataKey="volume" fill="#10b981" radius={[4, 4, 0, 0]} barSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

// Sub-component for the Metric Cards
const MetricCard = ({ title, avg, p90, isBottleneck }) => (
  <div className={`metric_card ${isBottleneck ? 'bottleneck_border' : ''}`}>
    <div className="card_header">
      <span className="card_title">{title}</span>
      {isBottleneck && <span className="bottleneck_tag">Bottleneck</span>}
    </div>
    <div className="card_body">
      <div className="stat_group">
        <span className="stat_value">{avg} <small>min</small></span>
        <span className="stat_label">Average Value</span>
      </div>
      <div className="stat_divider"></div>
      <div className="stat_group">
        <span className="stat_value highlight">{p90} <small>min</small></span>
        <span className="stat_label">90th Percentile</span>
      </div>
    </div>
  </div>
);

export default ViewMetricsPage;