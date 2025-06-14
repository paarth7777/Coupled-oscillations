
import { use, useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import CardWidget from './CardWidget';
import { info_layout, info_txt_layout, layout } from './constants';
// import '../styles/Dashboard.css';

const comp_indices = [
    {
        name: "NASDAQ",
        ticker: "^IXIC",
    },
    {
        name: "S&P 500",
        ticker: "^GSPC",
    },
    {
        name: "Dow Jones",
        ticker: "^DJI",
    },
    {
        name: "TSX Composite",
        ticker: "^GSPTSE",
    },
    {
        name: "FTSE 100",
        ticker: "^FTSE",
    },
]

function ComparisonWidget() {

    const [ revenueData, setRevenueData ] = useState([]);
    const [ pnlData, setPnlData ] = useState([]);
    const [ compositionData, setCompositionData ] = useState([]);
    const [ info, setInfo ] = useState([]);
    const [ revision, setRevision ] = useState(0);
    const [ selectedIndex, setselectedIndex ] = useState("^IXIC");
    const [ summaries, setSummaries ] = useState([]);

    useEffect(() => {
        // Simulating data fetch
        const fetchData = async () => {
            console.log(selectedIndex)
            const res = await fetch('http://localhost:3000/comparison', {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ "comparison": selectedIndex }),
            }); // Replace with actual API endpoint
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
                    name: 'Portfolio Value (CAD)',
                    hoverinfo: "x+y"
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
                    name: 'Comparison Value (CAD)'
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
                    name: 'Comparison % PnL'
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
                name: 'Portfolio Composition',
                textposition: "outside",
            } ]

            var portfolio_info = [
                {
                    type: "indicator",
                    mode: "number",
                    value: data.info.cash_invested,
                    number: { prefix: "$", suffix: " CAD" },
                    // delta: { reference: data.info.cash_invested, relative: true, position: "bottom" }
                },
                {
                    type: "indicator",
                    mode: "number+delta",
                    value: data.info.portfolio_value,
                    number: { prefix: "$", suffix: " CAD" },
                    delta: { reference: data.info.cash_invested, relative: true, position: "bottom" }
                },
                {
                    type: "indicator",
                    mode: "number+delta",
                    value: data.info.comp_value,
                    number: { prefix: "$", suffix: " CAD" },
                    delta: { reference: data.info.cash_invested, relative: true, position: "bottom" }
                },
            ];

            setRevenueData(revenue);
            setPnlData(pnl);
            setCompositionData(comp);
            setInfo(portfolio_info);
            setSummaries(data.summaries);
            setRevision(prev => prev + 1); // Trigger re-render
        };

        fetchData();

        return () => {
        }
    }, [ selectedIndex ])




    const [ layouts, setLayouts ] = useState([ info_layout, { ...layout }, { ...layout, barmode: "group" } ]);

    return (
        <div className="comparison">
            <div className="header">
                <h1 style={ { gridColumn: "1", gridRow: "1" } }>Investment Portfolio</h1>
                <CardWidget style={ { gridColumn: "2", gridRow: "1", height: "15vw" } } title={ "Comparison Index" }>
                    <select onChange={ e => setselectedIndex(e.target.value) } className='comparison-select'>
                        { comp_indices.map((index, idx) => (
                            <option key={ idx } value={ index.ticker }>
                                { index.name }
                            </option>
                        )) }
                    </select>
                </CardWidget>
                <CardWidget style={ { gridColumn: "3", gridRow: "1", height: "15vw" } } title={ "Cash Invested" }>
                    <Plot
                        data={ [ info[ 0 ] ] }
                        layout={ info_txt_layout }
                        useResizeHandler={ true }
                        config={ { responsive: true, displaylogo: false } }
                        style={ { width: "100%", height: "100%" } }
                        revision={ revision }
                    />
                </CardWidget>
                <CardWidget style={ { gridColumn: "4", gridRow: "1", height: "15vw" } } title={ "Portfolio Value" }>
                    <Plot
                        data={ [ info[ 1 ] ] }
                        layout={ info_txt_layout }
                        useResizeHandler={ true }
                        config={ { responsive: true, displaylogo: false } }
                        style={ { width: "100%", height: "100%" } }
                        revision={ revision }
                    />
                </CardWidget>
                <CardWidget style={ { gridColumn: "5", gridRow: "1", height: "15vw" } } title={ "Comparsion Index Value" }>
                    <Plot
                        data={ [ info[ 2 ] ] }
                        layout={ info_txt_layout }
                        useResizeHandler={ true }
                        config={ { responsive: true, displaylogo: false } }
                        style={ { width: "100%", height: "100%" } }
                        revision={ revision }
                    />
                </CardWidget>
            </div>
            <div className="cards">
                <CardWidget style={ {
                    gridColumn: "1 / span 2",
                    gridRow: "1 / span 2",
                    height: "30vw",
                    overflow: "hidden",
                } } title={ "Summary of Current Holdings" }>
                    <div style={ {
                        padding: "2rem",
                        marginTop: "0",
                        display: "flex",
                        flexDirection: "column",
                        overflow: "auto",
                        height: "70%",
                    } }>
                        { summaries.map((summary, index) => <h3 key={ index } style={ { fontSize: "1rem", } }> { summary } </h3>) }
                    </div>
                </CardWidget>
                <CardWidget style={ { gridColumn: "3 / span 2", gridRow: "1 / span 2" } } title={ "Current Holdings" }>
                    <Plot
                        data={ compositionData }
                        layout={ layouts[ 0 ] }
                        useResizeHandler={ true }
                        config={ { responsive: true, displaylogo: false } }
                        style={ { width: "100%", height: "100%" } }
                        revision={ revision }
                    />
                </CardWidget>
                <CardWidget style={ { gridColumn: "1 / span 2", gridRow: "3 / span 2" } } title={ "Portfolio Value vs Cash Invested vs Comparison Index" }>
                    <Plot
                        data={ revenueData }
                        layout={ { ...layouts[ 1 ] } }
                        useResizeHandler={ true }
                        config={ { responsive: true, displaylogo: false } }
                        style={ { width: "100%", height: "100%" } }
                        revision={ revision }
                    />
                </CardWidget>
                <CardWidget style={ { gridColumn: "3 / span 2", gridRow: "3 / span 2", height: "27vw" } } title={ "Daily PnL Chart" }>
                    <Plot
                        data={ pnlData }
                        layout={ { ...layouts[ 2 ] } }
                        useResizeHandler={ true }
                        config={ { responsive: true, displaylogo: false } }
                        style={ { width: "100%", height: "100%" } }
                        revision={ revision }
                    />
                </CardWidget>
            </div>
        </div>
    );
}

export default ComparisonWidget;