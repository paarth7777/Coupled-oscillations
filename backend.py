from flask import Flask
from flask_cors import CORS
import pandas as pd
from report import get_comparison_data, get_portfolio_performances
from flask import request

app = Flask(__name__)
CORS(app)

portfolio = {
    # "INR": {
    #     "ADANIENT.NS": [
    #         {
    #             "type": "buy",
    #             "date": "2020-06-15 09:30:00",
    #             "quantity": 1000,
    #             "price": 151.00,
    #         },
    #     ],
    # },
    "USD": {
        "RGTI": [
            {
                "type": "buy",
                "date": "2025-03-10 18:00:00",
                "quantity": 45,
                "price": 7.65,
            },
        ]
    },
    "CAD": {
        "AC.TO": [
            {
                "type": "buy",
                "date": "2025-02-06 09:30:00",
                "quantity": 101,
                "price": 18.22,
            },
            {
                "type": "buy",
                "date": "2025-02-14 09:30:00",
                "quantity": 50,
                "price": 18.61,
            },
            {
                "type": "sell",
                "date": "2025-03-20 12:00:00",
                "quantity": 151,
                "price": 15.11,
            },
        ]
    },
}

start_date = "2025-02-05"
end_date = "2025-04-02"


@app.route("/comparison", methods=["GET", "POST"])
def helloWorld():
    if request.method == 'POST':
        request_data = request.get_json()
        print(request_data)
        comparison = request_data.get('comparison')
        return get_comparison_data(portfolio, start_date, end_date, comparison=comparison)
    else:
        return get_comparison_data(portfolio, start_date, end_date)

@app.route("/indiv_performance")
def get_portfolio():
    return get_portfolio_performances(portfolio, start_date, end_date)


if __name__ == "__main__":
    app.run(debug=True, port=3000)
