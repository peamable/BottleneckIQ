import React from "react";
import {Upload, BarChart2, Lightbulb} from 'lucide-react';
import { Link } from "react-router-dom";

const MainPage = () => {
    const cards = [
        /* Any new card can be added here*/
        {
            title: 'Upload Data',
            desc: 'Import patient flow data',
            icon:<Upload size= {32} color= "#2563eb" />,
            path: '/upload'
        },

        {
            title: 'View Metrics',
            desc: 'Analyze key metrics about the data',
            icon:<BarChart2 size= {32} color= "#2563eb" />,
            path: '/view_metrics'
        },
        {
            title: 'Insights',
            desc: 'Get actionable Insights',
            icon:<Lightbulb size= {32} color= "#2563eb" />,
            path: '/insights'
        }
    ];

    return (
        <div className="Landing-container">
            <header className="landing-header">
                <h1>ED Bottleneck Detection System</h1>
                <p>Track patient flow timelines and identify operational bottlenecks</p>
            </header>

            <div className="card-grid">
                
                {
                    cards.map((card, index) =>(
                        <Link to={card.path} key={index} >
                        <div  className="nav-card">
                            <div className="icon-wrapper">{card.icon}</div>
                            <h3>{card.title}</h3>
                            <p>{card.desc}</p>
                        </div>
                        </Link>
                    ))
                }
               
            </div>
        </div>

        
    );
};

export default MainPage
