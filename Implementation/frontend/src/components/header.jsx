import React from "react";
import {Link} from 'react-router-dom';
import {Activity, Bell, User} from 'lucide-react';
import '../header.css'

const Header = () => {
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