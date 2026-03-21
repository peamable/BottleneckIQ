import { useState, useEffect } from "react";
import React from "react";
import {Link} from 'react-router-dom';
import {Activity, Bell, User} from 'lucide-react';
import '../header.css';

const Header = ({ uploadIdFromUrl }) => {

    const [horizon, setHorizon] = useState({ id: null, date: "Loading..." });

  useEffect(() => {
    const fetchHorizon = async () => {
      // If the URL has an ID, use it. Otherwise, the API defaults to 'Latest'
      const url = uploadIdFromUrl 
        ? `http://localhost:8000/metrics/dashboard-horizon?upload_id=${uploadIdFromUrl}`
        : "http://localhost:8000/metrics/dashboard-horizon";

      try {
        const response = await fetch(url);
        const data = await response.json();
        setHorizon({ id: data.upload_id, date: data.display_date });
      } catch (err) {
        setHorizon({ id: null, date: "System Offline" });
      }
    };

    fetchHorizon();
  }, [uploadIdFromUrl]); // Re-run if the user switches uploads
    return (
        <nav className="main-header">
            {/* LEFT SIDE: The Logo */}
            <Link to="/" className="logo-section">
                <div className="logo-icon">
                <Activity size={24} color="#ffffff" />
                </div>
                <span className="logo-text">
                Bottleneck<span className="logo-accent">IQ</span>
                </span>
            </Link>

            {/* THE DATA WINDOW & SYNC STATUS
            <div className="data_horizon_badge">
                <span className="horizon_label">Operational Window</span>
                <span className="horizon_value">Feb 22, 2026 | 08:00 - 14:00</span>
                <div className="sync_status">
                <span className="live_dot"></span> 
                Last Sync: just now
                </div>
            </div> */}

            {/* THE DATA WINDOW & SYNC STATUS */}
            <div className="data_horizon_badge">
                <span className="horizon_label">Operational Window</span>
                
                {/* This will now show the real upload time or 'Loading...' */}
                <span className="horizon_value">
                    {horizon.date} (ID: {horizon.id ?? '--'})
                </span>

                <div className="sync_status">
                    {/* The live dot stays green to show the system is connected */}
                    <span className="live_dot"></span> 
                    Last Sync: {horizon.id ? 'just now' : 'searching...'}
                </div>
            </div>

            {/* RIGHT SIDE: Navigation Actions */}
            <div className="header-actions">
                <button className="icon-button">
                <Bell size={20} />
                </button>
                <div className="user-profile">
                <User size={20} />
                <span>Analyst Mode</span>
                </div>
            </div>
        </nav>
    );
};

export default Header;