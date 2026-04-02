import React from "react";
import {ShieldCheck} from 'lucide-react';
import '../footer.css';
 
const Footer = () => {
      const currentYear = new Date().getFullYear(); //give us the current year

      return(
            <footer className="main_footer">
        <div className="footer_content">
            {/* LEFT SIDE: Copyright and Branding */}
            <div className="footer_left">
            <p>&copy; {currentYear} BottleneckIQ. All rights reserved.</p>
            </div>

            {/* RIGHT SIDE: System Status and Links */}
            <div className="footer_right">
            <div className="status_indicator">
                <ShieldCheck size={16} color="#10b981" />
                <span>Data Pipeline: Active</span>
            </div>
            <a href="https://github.com/peamable/W26_4495_S2_PhoebeA.git" className="footer_link" target="_blank" rel="noopener noreferrer">Documentation</a>
            <a href="#support" className="footer_link">Support</a>
            </div>
        </div>
        </footer>
    );
};

export default Footer;