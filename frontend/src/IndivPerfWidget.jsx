
import { use, useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { info_layout, layout } from './constants';
import CardWidget from './CardWidget';
// import '../styles/Dashboard.css';

function IndividualPerfWidget() {

    const [ perfData, setPerfData ] = useState({});
    const [ revision, setRevision ] = useState(0);
    const [ layouts, setLayouts ] = useState({});

    useEffect(() => {
        // Simulating data fetch
        const fetchData = async () => {
            const res = await fetch('http://localhost:3000/indiv_performance', {
                method: "GET",
                // headers: {
                //     "Content-Type": "application/json",
                // },
                // body: JSON.stringify({ "comparison": selectedIndex }),
            }); // Replace with actual API endpoint
            const data = await res.json(); // Assuming the API returns JSON data
            console.log(data);
            const new_perf_data = {}
            const new_layouts = {};
            for (let currency in data) {
                new_perf_data[ currency ] = {};
                new_layouts[ currency ] = {};
                for (let ticker in data[ currency ]) {
                    const invested = data[ currency ][ ticker ][ 'performance' ][ 'total_invested' ];
                    const final = data[ currency ][ ticker ][ 'performance' ][ 'final_value' ];
                    const prices = JSON.parse(data[ currency ][ ticker ][ 'prices' ]);
                    const transactions = data[ currency ][ ticker ][ 'transactions' ];
                    new_perf_data[ currency ][ ticker ] = {
                        info: {
                            invested: [ {
                                type: "indicator",
                                mode: "number",
                                value: invested,
                                number: { prefix: "$", suffix: " CAD" },
                                // delta: { reference: data.info.cash_invested, relative: true, position: "bottom" }
                            } ],
                            final: [ {
                                type: "indicator",
                                mode: "number+delta",
                                value: final,
                                number: { prefix: "$", suffix: " CAD" },
                                delta: { reference: invested, relative: true, position: "bottom" }
                            } ],
                        },
                        prices: [
                            {
                                x: Object.keys(prices).map(date => new Date(parseInt(date))),
                                y: Object.values(prices),
                                type: 'scatter',
                                mode: 'lines',
                                marker: { color: 'white' },
                                // fill: 'tozeroy',
                                name: `${ticker} Prices (CAD)`,
                                hoverinfo: "x+y"
                            },
                            {
                                x: transactions.map(tx => Date.parse(tx.date)),
                                y: transactions.map(tx => tx.price),
                                type: 'scatter',
                                mode: 'markers',
                                marker: {
                                    color:
                                        transactions.map(tx => tx.type === 'buy' ? 'green' : 'red'),
                                },
                                // fill: 'tozeroy',
                                name: 'Transactions',
                                text: transactions.map(tx => `${tx.type} $${tx.price} (${tx.quantity})`),
                                hoverinfo: "text",
                            },
                        ],
                    };

                    new_layouts[ currency ][ ticker ] = {
                        ...layout
                    }
                }
            }
            setPerfData(new_perf_data);
            setLayouts(new_layouts); // Assuming each item has a layout property
            setRevision(prev => prev + 1); // Trigger re-render
        };

        fetchData();

        return () => {
        }
    }, []);


    return (
        <div className="indiv-perf-widget">
            {/* <h1>Comparison and Overview</h1> */ }
            <h2>Individual Performance</h2>
            {
                Object.keys(perfData).length > 0 ? Object.keys(perfData).map(currency => (
                    <div key={ currency } className="currency-section">
                        <h3>{ currency } Equities</h3>
                        {
                            Object.keys(perfData[ currency ]).map(ticker => (
                                <div key={ ticker } className="cards">
                                    <CardWidget style={ { gridColumn: "2", gridRow: "1", height: "15vw" } } title={ "Cash Invested" }>
                                        <Plot
                                            data={ perfData[ currency ][ ticker ].info.invested }
                                            layout={ info_layout }
                                            useResizeHandler={ true }
                                            config={ { responsive: true, displaylogo: false } }
                                            style={ { width: "100%", height: "100%" } }
                                            revision={ revision }
                                        />
                                    </CardWidget>
                                    <CardWidget style={ { gridColumn: "2", gridRow: "2", height: "15vw" } } title={ ticker + " Final Value" }>
                                        <Plot
                                            data={ perfData[ currency ][ ticker ].info.final }
                                            layout={ info_layout }
                                            useResizeHandler={ true }
                                            config={ { responsive: true, displaylogo: false } }
                                            style={ { width: "100%", height: "100%" } }
                                            revision={ revision }
                                        />
                                    </CardWidget>
                                    <CardWidget style={ { gridColumn: "1", gridRow: "1 / span 2" } } title={ ticker + " Prices" }>
                                        <Plot
                                            data={ perfData[ currency ][ ticker ].prices }
                                            layout={ layouts[ currency ][ ticker ] }
                                            useResizeHandler={ true }
                                            config={ { responsive: true, displaylogo: false } }
                                            style={ { width: "100%", height: "100%" } }
                                            revision={ revision }
                                        />
                                    </CardWidget>
                                </div>
                            ))
                        }
                    </div>
                )) : <p>Loading...</p>
            }
        </div>
    );
}

export default IndividualPerfWidget;