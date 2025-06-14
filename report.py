import math
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import pytz
import pandas as pd
import matplotlib.gridspec as gridspec
import textwrap
import numpy as np
import textwrap
from currency_converter import CurrencyConverter

currencyConverter = CurrencyConverter()

USD_TO_CAD = currencyConverter.convert(
    100, "USD", "CAD", date=datetime.now() - timedelta(days=5)
)
print(f"USD to CAD conversion rate: {USD_TO_CAD}")


def calc_ticker_performance(ticker, transactions, current_price, currency=None):

    total_invested = 0
    current_shares = 0
    return_value = 0
    for txn in transactions:  # basic
        if txn["type"] == "buy":
            total_invested += txn["quantity"] * txn["price"]
            current_shares += txn["quantity"]
        elif txn["type"] == "sell":
            return_value += txn["quantity"] * txn["price"]
            current_shares -= txn["quantity"]

    current_value = current_shares * current_price + return_value
    current_value = (
        currencyConverter.convert(current_value, currency, "CAD")
        if currency
        else current_value
    )

    total_invested = (
        currencyConverter.convert(total_invested, currency, "CAD") if currency else total_invested
    )

    growth = ((current_value - total_invested) / total_invested) * 100
    # result = f"{ticker} Stock - Total Invested: {total_invested:.1f}CAD, Final Value: {current_value:.1f}CAD, ROI: {growth:.1f}%"
    return {
        "total_invested": total_invested,
        "final_value": current_value,
        "ROI": growth,
    }


def get_individual_performance(ticker, start_date, end_date, interval, transactions=None, current_price=None, currency=None):
    """
    Downloads historical stock price data and plots it, optionally overlaying buy and sell transactions,
    and the last price directly on the plot.
    """
    data = yf.download(ticker, start_date, end_date, interval=interval)

    if data.index.tz is None:
        data.index = data.index.tz_localize("UTC").tz_convert("America/New_York")
    else:
        data.index = data.index.tz_convert("America/New_York")

    business_days_data = data[data.index.dayofweek < 5]

    market_open = pd.Timestamp("09:30:00", tz="America/New_York").time()
    market_close = pd.Timestamp("16:00:00", tz="America/New_York").time()
    market_hours_data = business_days_data.between_time(market_open, market_close)

    prices = market_hours_data["Close"]

    result = {
        'prices': prices.to_json(),
        'transactions': [],
    }

    if transactions:
        result['transactions'] = transactions

    perf = calc_ticker_performance(ticker, transactions, current_price, currency)
    result['performance'] = perf

    return result


def get_portfolio_performances(portfolio, start_date, end_date):
    result = {}
    for currency in portfolio.keys():
        for ticker, txns in portfolio[currency].items():
            stock = yf.Ticker(ticker)
            current_price = stock.info['currentPrice']
            result[ticker] = get_individual_performance(ticker, start_date, end_date, interval="1h", transactions=txns, current_price=current_price, currency=currency)

    return result


def get_comparison_data(portfolio, start_date, end_date, comparison="^IXIC"):
    # Process all transactions
    transactions = []
    for currency in portfolio.keys():
        for ticker, txns in portfolio[currency].items():
            for txn in txns:
                # Normalize the date (without timezone)
                date = pd.to_datetime(txn["date"]).tz_localize(None).normalize()
                transactions.append(
                    {
                        "date": date,
                        "ticker": ticker,
                        "type": txn["type"],
                        "quantity": txn["quantity"],
                        "price": txn["price"],
                        "currency": currency,
                    }
                )
    # Sort chronologically
    transactions.sort(key=lambda x: x["date"])

    # Identify tickers
    # cad_tickers = list(portfolio["CAD"].keys())
    # all_tickers = []
    # for currency in portfolio.keys():
    #     all_tickers += list(portfolio[currency].keys())

    # ------------------------------
    # Fetch historical prices for portfolio tickers
    # ------------------------------
    historical_prices = {}
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    for currency in portfolio.keys():
        for ticker in portfolio[currency].keys():
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date, interval="1d")["Close"]
            if hist.empty:
                print(f"No data for {ticker}")
                historical_prices[ticker] = pd.Series(0.0, index=date_range)
                continue
            # If tz-naive, localize to UTC; otherwise, convert to UTC
            if hist.index.tz is None:
                hist.index = hist.index.tz_localize("UTC")
            else:
                hist.index = hist.index.tz_convert("UTC")
            # Remove time information and normalize the index
            hist.index = hist.index.tz_localize(None).normalize()
            hist_reindexed = hist.reindex(date_range, method="ffill")
            historical_prices[ticker] = hist_reindexed

    # ------------------------------
    # Fetch NASDAQ historical prices
    # ------------------------------
    nasdaq_stock = yf.Ticker(comparison)  # ^IXIC
    nasdaq_hist = nasdaq_stock.history(start=start_date, end=end_date, interval="1d")[
        "Close"
    ]
    if nasdaq_hist.empty:
        print("No data for NASDAQ")
        nasdaq_hist = pd.Series(0.0, index=date_range)
    else:
        if nasdaq_hist.index.tz is None:
            nasdaq_hist.index = nasdaq_hist.index.tz_localize("UTC")
        else:
            nasdaq_hist.index = nasdaq_hist.index.tz_convert("UTC")
        nasdaq_hist.index = nasdaq_hist.index.tz_localize(None).normalize()
        nasdaq_hist = nasdaq_hist.reindex(date_range, method="ffill")

    # ------------------------------
    # Calculate portfolio time series
    # ------------------------------
    current_holdings = {ticker: 0 for ticker in all_tickers}
    current_cash = 0.0  # Cash on hand (CAD)
    current_cash_invested = 0.0  # Total money invested into the portfolio

    # Create timeseries to track portfolio metrics
    cash_invested_ts = pd.Series(0.0, index=date_range)
    portfolio_value_ts = pd.Series(0.0, index=date_range)
    equity_ts = pd.Series(0.0, index=date_range)
    cash_ts = pd.Series(0.0, index=date_range)

    txn_index = 0
    for i, date in enumerate(date_range):
        # Process all transactions for the current date
        while txn_index < len(transactions) and transactions[txn_index]["date"] == date:
            txn = transactions[txn_index]
            ticker = txn["ticker"]
            txn_type = txn["type"]
            quantity = txn["quantity"]
            price = txn["price"]
            currency = txn["currency"]

            # Convert price to CAD if needed
            price_cad = (
                currencyConverter.convert(price, currency, "CAD", date=txn["date"])
                if currency != "CAD"
                else price
            )
            txn_value = quantity * price_cad

            if txn_type == "buy":
                current_holdings[ticker] += quantity
                if current_cash >= txn_value:
                    current_cash -= txn_value
                else:
                    # Additional funds are invested if cash is insufficient
                    needed = txn_value - current_cash
                    current_cash_invested += needed
                    current_cash = 0
            elif txn_type == "sell":
                current_holdings[ticker] -= quantity
                current_cash += txn_value

            txn_index += 1

        # Calculate portfolio equity from current holdings
        equity = 0.0
        for currency in portfolio.keys():
            for ticker in portfolio[currency].keys():
                if current_holdings[ticker] == 0:
                    continue
                price = historical_prices[ticker].iloc[i]
                price_cad = (
                    currencyConverter.convert(price, currency, "CAD", date=txn["date"])
                    if currency != "CAD"
                    else price
                )
                equity += current_holdings[ticker] * price_cad

        portfolio_value = equity + current_cash
        cash_invested_ts[date] = current_cash_invested
        portfolio_value_ts[date] = portfolio_value
        equity_ts[date] = equity
        cash_ts[date] = current_cash

    # ------------------------------
    # Simulate NASDAQ-equivalent portfolio
    # ------------------------------
    # For the NASDAQ portfolio, assume that whenever additional money is invested in your portfolio,
    # you invest that same cash amount into NASDAQ at that day’s price.
    nasdaq_shares = 0.0
    nasdaq_value_ts = pd.Series(0.0, index=date_range)
    # Calculate the day-to-day increment in cash invested
    cash_invested_diff = cash_invested_ts.diff().fillna(cash_invested_ts.iloc[0])

    for i, date in enumerate(date_range):
        additional_investment = cash_invested_diff[date]
        # If additional cash is invested, buy NASDAQ shares at the closing price for that day.
        if additional_investment > 0 and nasdaq_hist[date] != 0:
            nasdaq_shares += additional_investment / nasdaq_hist[date]
        # The NASDAQ-equivalent portfolio value is the total shares held times the current NASDAQ price.
        nasdaq_value_ts[date] = nasdaq_shares * nasdaq_hist[date]

    nasdaq_pnl = nasdaq_value_ts.diff().fillna(0) - cash_invested_ts.diff().fillna(0)
    n_prev_value = nasdaq_value_ts.shift(1)
    nasdaq_pnl_percentage = (nasdaq_pnl / n_prev_value.replace(0, np.nan)).fillna(
        0
    ) * 100
    nasdaq_pct = pd.Series(nasdaq_pnl_percentage, index=portfolio_value_ts.index)

    daily_pnl = portfolio_value_ts.diff().fillna(0) - cash_invested_ts.diff().fillna(0)
    prev_value = portfolio_value_ts.shift(1)
    daily_pnl_percentage = (daily_pnl / prev_value.replace(0, np.nan)).fillna(0) * 100
    daily_pnl_percentage = pd.Series(
        daily_pnl_percentage, index=portfolio_value_ts.index
    )

    # Final summary text for Section 1
    final_cash_invested = int(cash_invested_ts.iloc[-1])
    final_portfolio_value = int(portfolio_value_ts.iloc[-1])
    final_nasdaq_value = int(nasdaq_value_ts.iloc[-1])
    roi_portfolio = (
        ((final_portfolio_value - final_cash_invested) / final_cash_invested * 100)
        if final_cash_invested != 0
        else 0
    )
    roi_nasdaq = (
        ((final_nasdaq_value - final_cash_invested) / final_cash_invested * 100)
        if final_cash_invested != 0
        else 0
    )
    # final_text = f"Portfolio - Invested: {final_cash_invested}CAD, Final Value: {final_portfolio_value}CAD, ROI: {roi_portfolio:.2f}%, NASDAQ: {roi_nasdaq:.2f}%"

    holdings = []
    labels = []
    for currency in portfolio.keys():
        for ticker in portfolio[currency].keys():
            quantity = current_holdings[ticker]
            if quantity > 0:
                price = historical_prices[ticker].iloc[-1]
                if currency != "USD":
                    value = quantity * currencyConverter.convert(price, currency, "CAD", date=txn["date"])
                else:
                    value = quantity * price
                holdings.append(value)
                labels.append(f"{ticker}\n({quantity} shares)")
    holdings.append(current_cash)
    labels.append(f"Cash\n({current_cash:.2f} CAD)")
    filtered = [(l, v) for l, v in zip(labels, holdings) if v > 0]
    if filtered:
        pie_labels, pie_sizes = zip(*filtered)
    else:
        pie_labels, pie_sizes = ([], [])

    return {
        "info": {
            "portfolio_value": final_portfolio_value,
            "cash_invested": final_cash_invested,
            "comp_value": final_nasdaq_value,
            "roi_portfolio": roi_portfolio,
            "roi_comp": roi_nasdaq,
        },
        "investment_comp": pd.concat(
            [
                portfolio_value_ts,
                cash_invested_ts,
                nasdaq_value_ts,
            ],
            axis=1,
        ).to_json(),
        "pnl_data": pd.concat([daily_pnl_percentage, nasdaq_pct], axis=1).to_json(),
        "composition": {
            "labels": pie_labels,
            "sizes": pie_sizes,
        },
    }


def generate_report(portfolio, start_date, end_date, w, file):
    # Process all transactions
    transactions = []
    for currency in ["USD", "CAD"]:
        for ticker, txns in portfolio[currency].items():
            for txn in txns:
                # Normalize the date (without timezone)
                date = pd.to_datetime(txn["date"]).tz_localize(None).normalize()
                transactions.append(
                    {
                        "date": date,
                        "ticker": ticker,
                        "type": txn["type"],
                        "quantity": txn["quantity"],
                        "price": txn["price"],
                        "currency": currency,
                    }
                )
    # Sort chronologically
    transactions.sort(key=lambda x: x["date"])

    # Identify tickers
    usd_tickers = list(portfolio["USD"].keys())
    cad_tickers = list(portfolio["CAD"].keys())
    all_tickers = usd_tickers + cad_tickers

    # ------------------------------
    # Fetch historical prices for portfolio tickers
    # ------------------------------
    historical_prices = {}
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    for ticker in all_tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, interval="1d")["Close"]
        if hist.empty:
            print(f"No data for {ticker}")
            historical_prices[ticker] = pd.Series(0.0, index=date_range)
            continue
        # If tz-naive, localize to UTC; otherwise, convert to UTC
        if hist.index.tz is None:
            hist.index = hist.index.tz_localize("UTC")
        else:
            hist.index = hist.index.tz_convert("UTC")
        # Remove time information and normalize the index
        hist.index = hist.index.tz_localize(None).normalize()
        hist_reindexed = hist.reindex(date_range, method="ffill")
        historical_prices[ticker] = hist_reindexed

    # ------------------------------
    # Fetch NASDAQ historical prices
    # ------------------------------
    nasdaq_stock = yf.Ticker("^IXIC")  # ^IXIC
    nasdaq_hist = nasdaq_stock.history(start=start_date, end=end_date, interval="1d")[
        "Close"
    ]
    if nasdaq_hist.empty:
        print("No data for NASDAQ")
        nasdaq_hist = pd.Series(0.0, index=date_range)
    else:
        if nasdaq_hist.index.tz is None:
            nasdaq_hist.index = nasdaq_hist.index.tz_localize("UTC")
        else:
            nasdaq_hist.index = nasdaq_hist.index.tz_convert("UTC")
        nasdaq_hist.index = nasdaq_hist.index.tz_localize(None).normalize()
        nasdaq_hist = nasdaq_hist.reindex(date_range, method="ffill")

    # ------------------------------
    # Calculate portfolio time series
    # ------------------------------
    current_holdings = {ticker: 0 for ticker in all_tickers}
    current_cash = 0.0  # Cash on hand (CAD)
    current_cash_invested = 0.0  # Total money invested into the portfolio

    # Create timeseries to track portfolio metrics
    cash_invested_ts = pd.Series(0.0, index=date_range)
    portfolio_value_ts = pd.Series(0.0, index=date_range)
    equity_ts = pd.Series(0.0, index=date_range)
    cash_ts = pd.Series(0.0, index=date_range)

    txn_index = 0
    for i, date in enumerate(date_range):
        # Process all transactions for the current date
        while txn_index < len(transactions) and transactions[txn_index]["date"] == date:
            txn = transactions[txn_index]
            ticker = txn["ticker"]
            txn_type = txn["type"]
            quantity = txn["quantity"]
            price = txn["price"]
            currency = txn["currency"]

            # Convert price to CAD if needed
            price_cad = price * USD_TO_CAD if currency == "USD" else price
            txn_value = quantity * price_cad

            if txn_type == "buy":
                current_holdings[ticker] += quantity
                if current_cash >= txn_value:
                    current_cash -= txn_value
                else:
                    # Additional funds are invested if cash is insufficient
                    needed = txn_value - current_cash
                    current_cash_invested += needed
                    current_cash = 0
            elif txn_type == "sell":
                current_holdings[ticker] -= quantity
                current_cash += txn_value

            txn_index += 1

        # Calculate portfolio equity from current holdings
        equity = 0.0
        for ticker in all_tickers:
            if current_holdings[ticker] == 0:
                continue
            price = historical_prices[ticker].iloc[i]
            price_cad = price * USD_TO_CAD if ticker in usd_tickers else price
            equity += current_holdings[ticker] * price_cad

        portfolio_value = equity + current_cash
        cash_invested_ts[date] = current_cash_invested
        portfolio_value_ts[date] = portfolio_value
        equity_ts[date] = equity
        cash_ts[date] = current_cash

    # ------------------------------
    # Simulate NASDAQ-equivalent portfolio
    # ------------------------------
    # For the NASDAQ portfolio, assume that whenever additional money is invested in your portfolio,
    # you invest that same cash amount into NASDAQ at that day’s price.
    nasdaq_shares = 0.0
    nasdaq_value_ts = pd.Series(0.0, index=date_range)
    # Calculate the day-to-day increment in cash invested
    cash_invested_diff = cash_invested_ts.diff().fillna(cash_invested_ts.iloc[0])

    for i, date in enumerate(date_range):
        additional_investment = cash_invested_diff[date]
        # If additional cash is invested, buy NASDAQ shares at the closing price for that day.
        if additional_investment > 0 and nasdaq_hist[date] != 0:
            nasdaq_shares += additional_investment / nasdaq_hist[date]
        # The NASDAQ-equivalent portfolio value is the total shares held times the current NASDAQ price.
        nasdaq_value_ts[date] = nasdaq_shares * nasdaq_hist[date]

    nasdaq_pnl = nasdaq_value_ts.diff().fillna(0) - cash_invested_ts.diff().fillna(0)
    n_prev_value = nasdaq_value_ts.shift(1)
    nasdaq_pnl_percentage = (nasdaq_pnl / n_prev_value.replace(0, np.nan)).fillna(
        0
    ) * 100
    nasdaq_pct = pd.Series(nasdaq_pnl_percentage, index=portfolio_value_ts.index)

    daily_pnl = portfolio_value_ts.diff().fillna(0) - cash_invested_ts.diff().fillna(0)
    prev_value = portfolio_value_ts.shift(1)
    daily_pnl_percentage = (daily_pnl / prev_value.replace(0, np.nan)).fillna(0) * 100
    daily_pnl_percentage = pd.Series(
        daily_pnl_percentage, index=portfolio_value_ts.index
    )

    # Final summary text for Section 1
    final_cash_invested = int(cash_invested_ts.iloc[-1])
    final_portfolio_value = int(portfolio_value_ts.iloc[-1])
    final_nasdaq_value = int(nasdaq_value_ts.iloc[-1])
    roi_portfolio = (
        ((final_portfolio_value - final_cash_invested) / final_cash_invested * 100)
        if final_cash_invested != 0
        else 0
    )
    roi_nasdaq = (
        ((final_nasdaq_value - final_cash_invested) / final_cash_invested * 100)
        if final_cash_invested != 0
        else 0
    )
    final_text = f"Portfolio - Invested: {final_cash_invested}CAD, Final Value: {final_portfolio_value}CAD, ROI: {roi_portfolio:.2f}%, NASDAQ: {roi_nasdaq:.2f}%"

    # holdings
    holdings = []
    labels = []
    for ticker in all_tickers:
        quantity = current_holdings[ticker]
        if quantity > 0:
            price = historical_prices[ticker].iloc[-1]
            if ticker in usd_tickers:
                value = quantity * price * USD_TO_CAD
            else:
                value = quantity * price
            holdings.append(value)
            labels.append(f"{ticker}\n({quantity} shares)")
    holdings.append(current_cash)
    labels.append(f"Cash\n({current_cash:.2f} CAD)")
    filtered = [(l, v) for l, v in zip(labels, holdings) if v > 0]
    if filtered:
        pie_labels, pie_sizes = zip(*filtered)
    else:
        pie_labels, pie_sizes = ([], [])

    # Prepare pie chart data

    # Calculate ticker performance from its transactions

    def calculate_ticker_performance(ticker, transactions):
        total_invested = 0
        current_shares = 0
        return_value = 0
        current_price = historical_prices[ticker].iloc[
            -1
        ]  # *USD_TO_CAD if ticker in usd_tickers else historical_prices[ticker].iloc[-1]
        for txn in transactions:  # basic
            if txn["type"] == "buy":
                total_invested += txn["quantity"] * txn["price"]
                current_shares += txn["quantity"]
            elif txn["type"] == "sell":
                return_value += txn["quantity"] * txn["price"]
                current_shares -= txn["quantity"]

        current_value = current_shares * current_price + return_value
        current_value = (
            current_value * USD_TO_CAD if ticker in usd_tickers else current_value
        )

        total_invested = (
            total_invested * USD_TO_CAD if ticker in usd_tickers else total_invested
        )

        growth = ((current_value - total_invested) / total_invested) * 100
        result = f"{ticker} Stock - Total Invested: {total_invested:.1f}CAD, Final Value: {current_value:.1f}CAD, ROI: {growth:.1f}%"
        return result

    def plot_stock_price(ticker, interval, transactions=None, ax=None):
        """
        Downloads historical stock price data and plots it, optionally overlaying buy and sell transactions,
        and the last price directly on the plot.
        """
        data = yf.download(ticker, start_date, end_date, interval=interval)
        # if data.empty:
        #     if ax is not None:
        #         ax.text(0.5, 0.5, f"No data fetched for {ticker}", ha='center', va='center')
        #     else:
        #         print(f"No data fetched for {ticker} at {interval} intervals for the last {period}.")
        #     return

        if data.index.tz is None:
            data.index = data.index.tz_localize("UTC").tz_convert("America/New_York")
        else:
            data.index = data.index.tz_convert("America/New_York")

        business_days_data = data[data.index.dayofweek < 5]
        # if business_days_data.empty:
        #     if ax is not None:
        #         ax.text(0.5, 0.5, "No business day data available", ha='center', va='center')
        #     else:
        #         print("No business day data available within the downloaded period.")
        #     return

        market_open = pd.Timestamp("09:30:00", tz="America/New_York").time()
        market_close = pd.Timestamp("16:00:00", tz="America/New_York").time()
        market_hours_data = business_days_data.between_time(market_open, market_close)
        # if market_hours_data.empty:
        #     if ax is not None:
        #         ax.text(0.5, 0.5, "No market hours data available", ha='center', va='center')
        #     else:
        #         print("No market hours data available within the downloaded period.")
        #     return

        prices = market_hours_data["Close"]
        # if prices.empty:
        #     if ax is not None:
        #         ax.text(0.5, 0.5, "No closing prices available", ha='center', va='center')
        #     else:
        #         print("No closing prices available within the filtered data.")
        #     return
        # if ax is None:
        #     ax = plt.gca()
        x_axis = range(len(prices))
        ax.plot(x_axis, prices, label=f"{ticker} Stock Price", color="blue")
        last_price = float(prices.iloc[-1].iloc[0])
        last_index = len(prices) - 1
        ax.scatter(last_index, last_price, color="magenta", marker="*", s=100)
        ax.annotate(
            f"Last: ${last_price:.2f}",
            (last_index, last_price),
            textcoords="offset points",
            xytext=(5, 5),
            ha="left",
        )
        num_ticks = min(10, len(prices) // 2)
        if len(prices) > 1:
            step = max(len(prices) // num_ticks, 1)
            selected_indices = list(range(0, len(prices), step))
            selected_dates = prices.index[selected_indices]
            date_labels = [date.strftime("%Y-%m-%d %H:%M") for date in selected_dates]
            ax.set_xticks(selected_indices)
            ax.set_xticklabels(date_labels, rotation=45, ha="right")
        elif len(prices) == 1:
            ax.set_xticks([0])
            ax.set_xticklabels(
                [prices.index[0].strftime("%Y-%m-%d %H:%M")], rotation=45, ha="right"
            )

        if transactions:
            aggregated_buys = {}
            aggregated_sells = {}
            et_timezone = pytz.timezone("America/New_York")
            for transaction in transactions:
                try:
                    transaction_time_utc = datetime.strptime(
                        transaction["date"], "%Y-%m-%d %H:%M:%S"
                    )
                    transaction_time_et = pytz.utc.localize(
                        transaction_time_utc
                    ).astimezone(et_timezone)
                except ValueError:
                    try:
                        transaction_time_utc = datetime.strptime(
                            transaction["date"], "%Y-%m-%d %H:%M"
                        )
                        transaction_time_et = pytz.utc.localize(
                            transaction_time_utc
                        ).astimezone(et_timezone)
                    except ValueError as e:
                        print(
                            f"Error parsing date for {ticker} transaction: {transaction['date']}. Error: {e}"
                        )
                        continue

                nearest_index = None
                min_difference = timedelta.max
                for i, ts in enumerate(prices.index):
                    difference = abs(transaction_time_et - ts)
                    if difference < min_difference:
                        min_difference = difference
                        nearest_index = i
                    elif difference > min_difference:
                        break
                if nearest_index is not None:
                    plot_index = nearest_index
                    if transaction["type"] == "buy":
                        if plot_index not in aggregated_buys:
                            aggregated_buys[plot_index] = {
                                "price": transaction["price"],
                                "quantity": 0,
                            }
                        aggregated_buys[plot_index]["quantity"] += transaction[
                            "quantity"
                        ]
                    elif transaction["type"] == "sell":
                        if plot_index not in aggregated_sells:
                            aggregated_sells[plot_index] = {
                                "price": transaction["price"],
                                "quantity": 0,
                            }
                        aggregated_sells[plot_index]["quantity"] += transaction[
                            "quantity"
                        ]
            for index, data_dict in aggregated_buys.items():
                price_at_index = float(prices.iloc[index].iloc[0])
                buy_price = data_dict["price"]
                ax.scatter(index, buy_price, color="lime", marker="o", s=80)
                ax.annotate(
                    f'Buy: ${data_dict["price"]:.2f} ({data_dict["quantity"]})',
                    (index, buy_price),
                    textcoords="offset points",
                    xytext=(5, -10),
                    ha="left",
                    bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
                )

            for index, data_dict in aggregated_sells.items():
                price_at_index = float(prices.iloc[index].iloc[0])
                sell_price = data_dict["price"]
                ax.scatter(index, sell_price, color="orangered", marker="o", s=80)
                ax.annotate(
                    f'Sell: ${data_dict["price"]:.2f} ({data_dict["quantity"]})',
                    (index, sell_price),
                    textcoords="offset points",
                    xytext=(5, 10),
                    ha="left",
                    bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
                )
        ax.set_xlabel("Time (Business Days, Market Hours ET)")
        ax.set_ylabel("Price($)")
        perf = calculate_ticker_performance(ticker, transactions)
        ax.set_title(perf)
        ax.legend()
        ax.grid(True)

    # Main Figure Layout using GridSpec ###################################################

    # Determine dynamic grid rows for portfolio subplots:
    usd_count = len(portfolio["USD"])
    usd_rows = math.ceil(usd_count / 2) if usd_count > 0 else 1
    cad_count = len(portfolio["CAD"])
    cad_rows = math.ceil(cad_count / 2) if cad_count > 0 else 1

    # Total rows = fixed sections 1+ (2 rows for Section 1) + 1 row for Pie Chart + usd_rows + cad_rows
    total_rows = 40 + 10 * (usd_rows + cad_rows)

    fig = plt.figure(constrained_layout=True, figsize=(w, 38))
    gs = gridspec.GridSpec(nrows=total_rows, ncols=12, figure=fig)

    # ax = fig.add_subplot(gs[0, :])
    # ax.axis('off')
    axp = fig.add_subplot(gs[0:7, :])
    axp.axis("off")
    axp.set_title(
        x=0.5, y=0.5, label="Portfolio Analysis", ha="center", va="center", fontsize=40
    )
    abstract = "This report presents an in-depth analysis of the return on investment (ROI) for a the portfolio of equities traded on both American and Canadian stock exchanges. Investment values are standardized in Canadian dollars (CAD) to maintain consistency, with all U.S. dollar figures converted using a fixed conversion fee of 1.43 to account for currency stability."
    wa = textwrap.fill(abstract, width=200)
    axp.text(0.025, 0.1, wa, fontsize=16)
    intro = "Given below are the plots for the variation in total portfolio value with time, and the daily profit and loss generated by the portfolio"
    axp.text(0.025, 0, intro, fontsize=16)

    # Section 1: Portfolio vs Cash Invested and Daily PnL
    ax1 = fig.add_subplot(gs[8:18, 1:6])
    ax1.plot(
        portfolio_value_ts.index, portfolio_value_ts, label="Portfolio Value (CAD)"
    )
    ax1.plot(cash_invested_ts.index, cash_invested_ts, label="Cash Invested (CAD)")
    ax1.plot(nasdaq_value_ts.index, nasdaq_value_ts, label="NASDAQ Value (CAD)")
    ax1.annotate(
        f"${final_cash_invested}", (cash_invested_ts.index[-1], final_cash_invested)
    )
    ax1.annotate(
        f"${final_portfolio_value}",
        (portfolio_value_ts.index[-1], final_portfolio_value),
    )
    ax1.annotate(
        f"${final_nasdaq_value}", (nasdaq_value_ts.index[-1], final_nasdaq_value)
    )
    ax1.set_title(final_text)
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Amount (CAD)")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax1.tick_params(axis="x", rotation=45)
    ax1.grid(True)
    ax1.legend()

    # axq = fig.add_subplot(gs[9:10, :])
    # axq.text(0.5, 0.5, final_text, ha='left', va='top', fontsize=15,
    #         bbox=dict(facecolor='white', alpha=0.5, edgecolor='gray'))

    # ax2 = fig.add_subplot(gs[8:13, 6:11])
    # colors = ['green' if pnl > 0 else 'red' for pnl in daily_pnl]
    # ax2.bar(daily_pnl.index, daily_pnl, color=colors, width=1.0)
    # ax2.set_title('Daily Profit and Loss (PnL) in CAD')
    # ax2.set_xlabel('Date')
    # ax2.set_ylabel('Daily PnL (CAD)')
    # ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    # ax2.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    # ax2.tick_params(axis='x', rotation=45)
    # ax2.grid(True)

    portfolio_colors = ["limegreen" if x >= 0 else "red" for x in daily_pnl_percentage]
    nasdaq_colors = ["darkgreen" if x >= 0 else "darkred" for x in nasdaq_pct]

    # Create percentage PnL comparison plot
    ax5 = fig.add_subplot(gs[8:18, 6:11])  # Adjust grid position as needed
    width = 0.4  # Bar width in days

    # Plot portfolio bars (green/red)
    ax5.bar(
        daily_pnl_percentage.index - pd.Timedelta(days=width / 2),
        daily_pnl_percentage,
        width=width,
        label="Portfolio Daily % PnL",
        color=portfolio_colors,
        edgecolor="grey",
        linewidth=0.05,
    )

    # Plot NASDAQ bars (dark green/dark red)
    ax5.bar(
        nasdaq_pct.index + pd.Timedelta(days=width / 2),
        nasdaq_pct,
        width=width,
        label="NASDAQ Daily % PnL",
        color=nasdaq_colors,
        edgecolor="black",
        linewidth=0.05,
    )

    # Formatting
    ax5.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax5.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax5.tick_params(axis="x", rotation=45)
    ax5.set_ylabel("Daily PnL %")
    ax5.axhline(0, color="black", linewidth=0.8)  # Zero line
    ax5.grid(True, linestyle="--", alpha=0.7)
    ax5.set_title("Daily PnL Comparison (Portfolio vs NASDAQ)")

    # Create custom legend
    legend_elements = [
        plt.Rectangle(
            (0, 0), 1, 1, fc="limegreen", ec="black", label="Portfolio Profit %"
        ),
        plt.Rectangle((0, 0), 1, 1, fc="red", ec="black", label="Portfolio Loss %"),
        plt.Rectangle(
            (0, 0), 1, 1, fc="darkgreen", ec="black", label="NASDAQ Profit %"
        ),
        plt.Rectangle((0, 0), 1, 1, fc="darkred", ec="black", label="NASDAQ Loss %"),
    ]
    ax5.legend(handles=legend_elements, loc="upper left")

    # Section 2: Centered Pie Chart (row 4, columns 1-3)
    ax3 = fig.add_subplot(gs[19:32, 0:6])
    ax3.axis("off")
    i = 0.85
    ax3.text(
        0.05,
        1,
        s="The portfolio's current holding is composed of the following equities:",
        fontsize=16,
    )
    for ticker in all_tickers:
        t = get_stock_details(ticker)
        ax3.text(0.1, i, s=t, fontsize=13)
        i -= 0.12
    ax3.text(
        0.05,
        0,
        s="And Finally, the individual performance of the equities is analysed:",
        fontsize=16,
    )

    ax4 = fig.add_subplot(gs[19:32, 6:12])
    if pie_sizes:
        colors_pie = plt.cm.Paired.colors
        wedges, texts, autotexts = ax4.pie(
            pie_sizes,
            labels=pie_labels,
            colors=colors_pie[: len(pie_labels)],
            explode=[0.05] * len(pie_labels),
            autopct=lambda p: f"${p*sum(pie_sizes)/100:,.2f}",
            startangle=140,
            wedgeprops={"linewidth": 1, "edgecolor": "w"},
            textprops={"fontsize": 10},
        )
        for autotext in autotexts:
            autotext.set_color("black")
            autotext.set_fontsize(10)
        ax4.set_title("Current Portfolio Composition Breakdown (CAD)")
    else:
        ax4.text(
            0.5, 0.5, "No holdings to display in pie chart", ha="center", va="center"
        )
        ax4.set_title("Pie Chart")

    axa = fig.add_subplot(gs[32:35, 1:11])
    axa.axis("off")
    axa.set_title(
        x=0, y=0.5, label="American Equities", ha="center", va="center", fontsize=20
    )

    # Section 3: USD Portfolio plots grid
    if usd_count > 0:
        gs_usd = gridspec.GridSpecFromSubplotSpec(
            usd_rows, 2, subplot_spec=gs[35 : 35 + 10 * usd_rows, 1:11]
        )
        usd_index = 0
        for ticker, txns in portfolio["USD"].items():
            row = usd_index // 2
            col = usd_index % 2
            ax = fig.add_subplot(gs_usd[row, col])
            # perf_text = calculate_ticker_performance(ticker, txns)
            # ax.text(0,0, s = perf_text, ha='center', va='bottom', fontsize=10)
            plot_stock_price(
                ticker, interval="1h", transactions=txns, ax=ax
            )  #### Wrong
            usd_index += 1
    else:
        # If no USD holdings, display a message in the allocated area.
        ax = fig.add_subplot(gs[35, 35 + 10 * usd_rows, 1:11])
        ax.text(0.5, 0.6, "No USD holdings", ha="center", va="center", fontsize=14)
        ax.axis("off")

    axc = fig.add_subplot(gs[35 + 10 * usd_rows : 38 + 10 * usd_rows, 1:11])
    axc.axis("off")
    axc.set_title(
        x=0, y=0.5, label="Canadian Equities", ha="center", va="center", fontsize=20
    )

    # Section 4: CAD Portfolio plots grid
    if cad_count > 0:
        start_row = 38 + 10 * usd_rows
        gs_cad = gridspec.GridSpecFromSubplotSpec(
            cad_rows, 2, subplot_spec=gs[start_row : start_row + 10 * cad_rows, 1:11]
        )
        cad_index = 0
        for ticker, txns in portfolio["CAD"].items():
            row = cad_index // 2
            col = cad_index % 2
            ax = fig.add_subplot(gs_cad[row, col])
            plot_stock_price(ticker, interval="1h", transactions=txns, ax=ax)
            perf_text = calculate_ticker_performance(ticker, txns)
            # ax.text(0.5, -0.15, perf_text, ha='center', va='top', transform=ax.transAxes,
            #         fontsize=10, bbox=dict(facecolor='white', alpha=0.7, edgecolor='gray'))
            cad_index += 1
    else:
        # If no CAD holdings, display a message in the allocated area.
        ax = fig.add_subplot(gs[32 + 10 * usd_rows :, :])
        ax.text(0.5, 0.5, "No CAD holdings", ha="center", va="center", fontsize=14)
        ax.axis("off")

    axc = fig.add_subplot(gs[-2:, 1:11])
    axc.axis("off")

    plt.savefig(f"{file}.pdf", bbox_inches="tight")
    # plt.show()


def truncate_summary(summary, limit=80):
    """
    Truncates the summary at the first whitespace after the given limit and appends an ellipsis.

    Args:
        summary (str): The full business summary.
        limit (int): The minimum number of characters before looking for a whitespace.

    Returns:
        str: The truncated summary ending at the first whitespace after 'limit' characters.
    """
    if len(summary) <= limit:
        return summary
    # Find the first whitespace after 'limit' characters
    space_index = summary.find(" ", limit)
    if space_index == -1:
        return summary  # In case there's no whitespace, return the whole summary
    return summary[:space_index] + "..."


def get_stock_details(ticker_symbol):
    """
    Retrieves and formats stock details for a given ticker symbol, including a truncated business summary.

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        str: A formatted paragraph containing the stock details.
    """
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    company_name = info.get("longName", "N/A")
    exchange = info.get("exchange", "N/A")
    sector = info.get("sector")
    market_cap = info.get("marketCap")
    summary = info.get("longBusinessSummary", None)

    # Format market cap for better readability
    if market_cap is not None:
        if market_cap >= 1_000_000_000_000:
            market_cap_str = f"${market_cap / 1_000_000_000_000:.2f} Trillion"
        elif market_cap >= 1_000_000_000:
            market_cap_str = f"${market_cap / 1_000_000_000:.2f} Billion"
        elif market_cap >= 1_000_000:
            market_cap_str = f"${market_cap / 1_000_000:.2f} Million"
        else:
            market_cap_str = f"${market_cap}"
    else:
        market_cap_str = "N/A"

    # Create the main paragraph
    if sector:
        paragraph = (
            f" - {ticker_symbol} : {company_name}({ticker_symbol}) trades on {exchange} and operates in the {sector} sector. "
            f"Currently, its market capitalization stands at approximately {market_cap_str}."
        )
    else:
        paragraph = f" - {ticker_symbol} : {company_name}({ticker_symbol}) trades on {exchange}."
    paragraph += f" {summary}"
    truncated_paragraph = truncate_summary(paragraph, 300)
    # Append the truncated summary if available

    # Wrap text for readability
    wrapped_paragraph = textwrap.fill(truncated_paragraph, width=105)

    return wrapped_paragraph


if __name__ == "__main__":

    portfolio = {
        "USD": {
            "RGTI": [
                {
                    "type": "buy",
                    "date": "2025-03-10 18:00:00",
                    "quantity": 45,
                    "price": 7.65,
                },
                {
                    "type": "sell",
                    "date": "2025-03-14 10:00:00",
                    "quantity": 45,
                    "price": 10.47,
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
    end_date = "2025-06-09"
    w = 26

    generate_report(portfolio, start_date, end_date, w, "portfolio_report")
