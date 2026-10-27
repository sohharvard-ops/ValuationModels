#Kukubird Main components
#Ticker: single ticker data
#Tickers: multiple tickers' data
#download: download market data for multiple tickers
#Market: get information about a market
#WebSocket and AsyncWebSocket: live streaming data
#Search: quotes and news from search
#Sector and Industry: sector and industry information
#EquityQuery and Screener: build query to screen market
import yfinance as yf

ticker = yf.Ticker("AAPL")  


cash_flow = ticker.cashflow
balance_sheet = ticker.balance_sheet
income_statement = ticker.income_stmt

#---------------------------Prints EOY Data-----------------------------------------------
#print("Cash flow statement:")
#print(cash_flow)

#print("Balance sheet:")
#print(balance_sheet)

#print("Income statement:")
#print(income_statement)
##---------------------------Prints Per Year-----------------------------------------------

year = 2024
column = next(col for col in cash_flow.columns if col.year == year)

value = cash_flow.loc["Free Cash Flow", column]
print(f"${value:,.2f}")
print(cash_flow[column].to_string(
    float_format=lambda amount: f"-${-amount:,.2f}" if amount < 0 else f"${amount:,.2f}"
))
