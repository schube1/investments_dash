import yfinance as yf
import os
import datetime
import sheet_utils as utils
import configs


last_updated = datetime.date.today()

sheet = utils.create_service()


worth = utils.get_from_sheet(sheet, 'H2')
cash = utils.get_from_sheet(sheet, 'J10')
etf_value = utils.get_from_sheet(sheet, 'P5')
stock_value = utils.get_from_sheet(sheet, 'F10')
etf_invested = utils.get_from_sheet(sheet, 'N5')
stock_invested = utils.get_from_sheet(sheet, "D10")

invested = etf_invested + stock_invested
profit = (stock_value + etf_value) - invested


print(f'ACCOUNT WORTH including cash : {worth:.2f}')
print(f'ACCOUNT INVESTED : {invested:.2f}')
print(f'ACCOUNT PROFITS : {profit:.2f}')



stock_tickers = utils.get_tickers(sheet, configs.stock_tickers_range)
etf_tickers = utils.get_tickers(sheet, configs.etf_tickers_range)
tickers = stock_tickers + etf_tickers


data = yf.download(
    tickers = " ".join(tickers),
    period= '1d',
    interval = '1m',
    group_by = "ticker",
    threads = True,
    progress = False
)

prices = {}

if len(tickers) == 1:
    prices[tickers[0]] = round(float(data["Close"].dropna().iloc[-1]),2)
else:
    for t in tickers:
        series = data[t]["Close"].dropna()
        if not series.empty:
            prices[t] = round(float(series.iloc[-1]),2)
        else:
            prices[t] = None


print(prices)

# create holdings dict

stock_holdings = utils.get_holdings(sheet, configs.stock_holding_range)
etf_holdings = utils.get_holdings(sheet, configs.etf_holding_range)
holdings = {**stock_holdings, **etf_holdings}


print(holdings)
percents = {}

for t in tickers:
    percents[t] = ((prices[t] * holdings[t]["shares"]) - holdings[t]["total_cost"]) / holdings[t]["total_cost"]


print(percents)

###index creation is sample###

from pathlib import Path

def build_html(last_updated, worth, invested, profit, prices, percents, holdings):

    sorted_tickers = sorted(tickers, key=lambda t: percents[t], reverse=True)
    rows = "\n".join(
        f"<tr><td>{t}</td><td>{'' if prices[t] is None else f'${prices[t]:,.2f}'}</td><td>{percents[t]* 100:,.2f}%</td><td>${((holdings[t]["shares"]* prices[t]) - holdings[t]["total_cost"]):,.2f}</td><td></td></tr>"
        for t in sorted_tickers
    )

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Portfolio Snapshot</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Arial; margin: 24px; }}
    .card {{ border: 1px solid #ddd; border-radius: 12px; padding: 16px; max-width: 720px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 12px 0; }}
    .metric {{ border: 1px solid #eee; border-radius: 10px; padding: 12px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ padding: 10px; border-bottom: 1px solid #eee; text-align: left; }}
    .muted {{ color: #666; font-size: 14px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Portfolio Snapshot</h1>
    <div class="muted">Last updated: {last_updated}</div>

    <div class="grid">
      <div class="metric"><div class="muted">Worth</div><div><b>${worth:,.2f}</b></div></div>
      <div class="metric"><div class="muted">Invested</div><div><b>${invested:,.2f}</b></div></div>
      <div class="metric"><div class="muted">Profit</div><div><b>${profit:,.2f}</b></div></div>
      <div class="metric"><div class="muted">Cash</div><div><b>${cash:,.2f}</b></div></div>
    </div>

    <h2>Holdings</h2>
    <table>
      <thead><tr><th>Ticker</th><th>Price</th><th>Total Change</th><th>Gains</th><th>Allocation</th></tr></thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</body>
</html>
"""

html = build_html(last_updated, worth, invested, profit, prices, percents, holdings)
Path("index.html").write_text(html, encoding="utf-8")
print("Wrote index.html")


#index creation is sample###

# write to history csv inclduing timestamp, worth, invested, profit, cash, stock_value, etf_value

import csv
fields = ['timestamp', 'worth', 'invested', 'profit', 'cash', 'stock_value', 'etf_value']
rows = [datetime.datetime.now(), worth, invested, profit, cash, stock_value, etf_value]
with open ('history.csv', mode = 'a', newline = '') as f:
    csvwriter = csv.writer(f)
    #write headers onece
    if f.tell() == 0:
        csvwriter.writerow(fields)
    #always write rows
    csvwriter.writerow(rows)
