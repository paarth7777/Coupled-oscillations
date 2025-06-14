export const layout = {
    xaxis: {
        autorange: true,
        // range: [ '2015-02-17', '2017-02-16' ],
        color: "white",
        gridcolor: "rgba(255, 255, 255, 0.1)",
        rangeselector: {
            bgcolor: 'transparent',
            activecolor: '#00000099',
            // bordercolor: 'white',
            // borderwidth: 1,
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
                    stepmode: 'backward',
                    bgcolor: 'black'
                },
                { step: 'all' }
            ]
        },
        rangeslider: true,
        type: 'date',
        showspikes: true,
        spikethickness: -2,
        spikemode: "toaxis",
    },
    yaxis: {
        autorange: true,
        // range: [ 86.8700008333, 138.870004167 ],
        gridcolor: "rgba(255, 255, 255, 0.1)",
        showspikes: true,
        spikethickness: -2,
        spikemode: "toaxis",
        type: 'linear',
        hoverformat: '.2f',
    },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: {
        color: "white",
    },
    margin: { pad: 5, },
    legend: {
        orientation: 'h',
        yanchor: 'bottom',
        y: 1.15,
        xanchor: 'left',
        x: 0,
        // bgcolor: 'transparent',
        // bordercolor: 'white',
        // borderwidth: 1,
    },
    hovermode: "x",
};

export const info_layout = { paper_bgcolor: "transparent", plot_bgcolor: "transparent", font: { color: "white" }, };