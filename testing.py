import currency_converter
from datetime import date

c = currency_converter.CurrencyConverter()

print(c.convert(100, 'INR', 'CAD', date=date(2020, 6, 15)))  
