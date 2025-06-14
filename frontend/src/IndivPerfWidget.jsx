
import { use, useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
// import '../styles/Dashboard.css';

function IndividualPerfWidget() {

    const [ revenueData, setRevenueData ] = useState([]);
    const [ pnlData, setPnlData ] = useState([]);
    const [ compositionData, setCompositionData ] = useState([]);
    const [ info, setInfo ] = useState({});

    useEffect(() => {
        // Simulating data fetch
        const fetchData = async () => {
            const res = await fetch('http://localhost:3000/indiv_performance'); // Replace with actual API endpoint
            const data = await res.json(); // Assuming the API returns JSON data
            console.log(data);
            const investment_comp = JSON.parse(data.investment_comp);
            const pnl_data = JSON.parse(data.pnl_data);
            const revenue = [
                {
                    x: Object.keys(investment_comp[ 0 ]).map(date => new Date(parseInt(date))),
                    y: Object.values(investment_comp[ 0 ]),
                    type: 'scatter',
                    mode: 'lines',
                    marker: { color: 'cornflowerblue' },
                    // fill: 'tozeroy',
                    name: 'Portfolio Value (CAD)'
                },
                {
                    x: Object.keys(investment_comp[ 1 ]).map(date => new Date(parseInt(date))),
                    y: Object.values(investment_comp[ 1 ]),
                    type: 'scatter',
                    mode: 'lines',
                    marker: { color: 'orange' },
                    // fill: 'tozeroy',
                    name: 'Cash Invested (CAD)'
                },
                {
                    x: Object.keys(investment_comp[ 2 ]).map(date => new Date(parseInt(date))),
                    y: Object.values(investment_comp[ 2 ]),
                    type: 'scatter',
                    mode: 'lines',
                    marker: { color: 'seagreen' },
                    // fill: 'tozeroy',
                    name: 'NASDAQ Value (CAD)'
                },
            ];

            const pnl = [
                {
                    x: Object.keys(pnl_data[ 0 ]).map(date => new Date(parseInt(date))),
                    y: Object.values(pnl_data[ 0 ]),
                    type: 'bar',
                    // mode: 'lines+markers',
                    marker: { color: Object.values(pnl_data[ 0 ]).map(value => value >= 0 ? 'green' : 'darkgreen') },
                    // fill: 'tozeroy',
                    name: 'Portfolio Daily % PnL'
                },
                {
                    x: Object.keys(pnl_data[ 1 ]).map(date => new Date(parseInt(date))),
                    y: Object.values(pnl_data[ 1 ]),
                    type: 'bar',
                    // mode: 'lines+markers',
                    marker: { color: Object.values(pnl_data[ 0 ]).map(value => value >= 0 ? 'orange' : 'darkorange') },
                    // fill: 'tozeroy',
                    name: 'NASDAQ % PnL'
                }
            ];

            const comp = [ {
                labels: data.composition.labels,
                values: data.composition.sizes,
                type: 'pie',
                textinfo: 'label',
                // insidetextorientation: 'radial',
                // marker: {
                //     colors: [
                //         '#636efa', '#EF553B', '#00cc96', '#ab63fa', '#FFA15A', '#19d3f3',
                //         '#FF6692', '#B6E880', '#FF97FF', '#FECB52'
                //     ]
                // },
                name: 'Portfolio Composition'
            }]

            setRevenueData(revenue);
            setPnlData(pnl);
            setCompositionData(comp);
            setInfo(data.info);
        };

        fetchData();

        return () => {
        }
    }, [])


    const [ layout, setLayout ] = useState({
        xaxis: {
            autorange: true,
            // range: [ '2015-02-17', '2017-02-16' ],
            rangeselector: {
                buttons: [
                    {
                        count: 1,
                        label: '1m',
                        step: 'month',
                        stepmode: 'backward'
                    },
                    {
                        count: 6,
                        label: '6m',
                        step: 'month',
                        stepmode: 'backward'
                    },
                    { step: 'all' }
                ]
            },
            rangeslider: true,
            type: 'date'
        },
        yaxis: {
            autorange: true,
            // range: [ 86.8700008333, 138.870004167 ],
            type: 'linear'
        }
    });

    return (
        <div className="dashboard">
            {/* <h1>Comparison and Overview</h1> */}
            <div className="cards">
                <Plot
                    data={ compositionData }
                    layout={ { title: { text: "Current Holdings" }, } }
                    useResizeHandler={ true }
                    config={ { responsive: true, displaylogo: false } }
                    // style={ { width: "50%", height: "100%" } }
                />
                <Plot
                    data={ revenueData }
                    layout={ {...layout } }
                    useResizeHandler={ true }
                    config={ { responsive: true, displaylogo: false } }
                    style={ { width: "50%", height: "100%" } }
                />
                <Plot
                    data={ pnlData }
                    layout={ { ...layout, barmode: "group" } }
                    useResizeHandler={ true }
                    config={ { responsive: true, displaylogo: false } }
                    style={ { width: "50%", height: "100%" } }
                />
            </div>
        </div>
    );
}

export default IndividualPerfWidget;