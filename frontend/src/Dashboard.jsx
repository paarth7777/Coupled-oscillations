import React from 'react';
import Plot from 'react-plotly.js';
import ComparisonWidget from './ComparisonWidget';
import IndividualPerfWidget from './IndivPerfWidget';
// import '../styles/Dashboard.css';

function Dashboard() {

    return (
        <div className="dashboard">
            <h1>Investment Portfolio</h1>
            <ComparisonWidget />
            {/* <IndividualPerfWidget /> */}
        </div>
    );
}

export default Dashboard;