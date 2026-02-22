import React from 'react';
import { AlertTriangle, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import '../bottleneck_banner.css';

const BottleneckBanner = ({ stage_name, delay_time }) => {
  const navigate = useNavigate();

  return (
    <div className="bottleneck_banner">
      <div className="banner_left_content">
        <div className="alert_icon_container">
          {/* Using a filled triangle for higher visibility */}
          <AlertTriangle size={24} fill="#fbbf24" color="#1e293b" />
        </div>
        <div className="banner_text_stack">
          <span className="banner_label">Bottleneck Detected</span>
          <h3 className="banner_main_text">
            High latency in <span className="stage_highlight">{stage_name}</span> 
            {delay_time && ` (${delay_time}m avg)`}
          </h3>
        </div>
      </div>

      <button 
        className="banner_action_btn" 
        onClick={() => navigate('/insights')}
      > Insights<ChevronRight size={18} /></button>
    </div>
  );
};

export default BottleneckBanner;