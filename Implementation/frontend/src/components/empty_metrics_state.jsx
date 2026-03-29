import React from 'react';
import { DatabaseBackup, PlusCircle, Sparkles, Activity, BarChart3 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import '../empty_metrics.css';

const EmptyMetricsState = () => {
  const navigate = useNavigate();

  return (
    <div className="empty_state_container">
      <div className="empty_state_card">
        <div className="empty_icon_wrapper">
          <DatabaseBackup size={48} color="#2563eb" />
        </div>

        <h1>No patient flow data detected</h1>
        <h2>Looks like your analytics start here</h2>
        <p>
          There is currently no dataset in the system. Upload a CSV to
          generate your first bottleneck report and unlock metrics/insights.
        </p>

        <button className="btn_primary_large" onClick={() => navigate('/upload')}>
          <PlusCircle size={20} />
          Upload New Dataset
        </button>
      </div>
    </div>
  );
};

export default EmptyMetricsState;