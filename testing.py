import yfinance as yf
from currency_converter import CurrencyConverter
from datetime import date

c = CurrencyConverter()

print(c.convert(1, 'INR', 'CAD', date=date(2020, 2, 6)))