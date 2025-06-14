import React from 'react';
import Plot from 'react-plotly.js';
import ComparisonWidget from './ComparisonWidget';
// import '../styles/Dashboard.css';

function CardWidget({children, style, title}) {

    return (
        <div className="card" style={ style }>
            { children }
            <p>{ title }</p>
        </div>
    );
}

export default CardWidget;