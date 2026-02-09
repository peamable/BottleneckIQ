import React from 'react';
import { DatabaseBackup, PlusCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const EmptyMetricsState = () => {
  const navigate = useNavigate();

  return (
    <div className="empty_state_container">
      <div className="empty_state_card">
        <div className="empty_icon_wrapper">
          <DatabaseBackup size={48} color="#94a3b8" />
        </div>
        <h2>No Patient Data Found</h2>
        <p>
          It looks like there aren't any records in the database yet. 
          Upload a CSV to generate your first bottleneck analysis.
        </p>
        <button 
          className="btn_primary_large" 
          onClick={() => navigate('/upload')}
        >
          <PlusCircle size={20} />
          Upload New Dataset
        </button>
      </div>
    </div>
   
    
  );
};

export default EmptyMetricsState;