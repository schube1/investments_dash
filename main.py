import yfinance as yf
import os
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = "gcp.json"
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes = SCOPES)
service = build('sheets', 'v4', credentials = credentials)
sheet = service.spreadsheets()
sheet_id = '1gm5tL_4mEqldSFhD14PaPOkO_o-ojWbBBJ4Tw863gug'

last_updated = datetime.date.today()

def get_from_sheet(range):
    sheet_read = sheet.values().get(spreadsheetId = sheet_id, range = range).execute()
    val = float(sheet_read.get('values')[0][0])
    return val

## consolidate redundancies## consolidate redundancies## consolidate redundancies
##created funcs to address redundancies

worth = get_from_sheet('H2')
cash = get_from_sheet('J10')
etf_value = get_from_sheet('P5')
stock_value = get_from_sheet('F10')
etf_invested = get_from_sheet('N5')
stock_invested = get_from_sheet("D10")

invested = etf_invested + stock_invested
profit = (stock_value + etf_value) - invested

print(f'ACCOUNT WORTH including cash : {worth:.2f}')
print(f'ACCOUNT INVESTED : {invested:.2f}')
print(f'ACCOUNT PROFITS : {profit:.2f}')



# in this part we get the ticker names from the sheet and then download all the info for all the tickers at once
sheet_read = sheet.values().get(spreadsheetId = sheet_id, range = 'A2:A9').execute()
sheet_read_etf = sheet.values().get(spreadsheetId = sheet_id, range = 'K2:K3').execute()

stock_tickers = [row[0].strip() for row in sheet_read.get('values', []) if row and row[0].strip()]
etf_tickers = [row[0].strip() for row in sheet_read_etf.get('values', []) if row and row[0].strip()]

tickers = stock_tickers + etf_tickers

print(tickers)


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

holdings = {}

## consolidate redundancies## consolidate redundancies## consolidate redundancies

sheet_read_rect = sheet.values().get(spreadsheetId = sheet_id, range = 'A2:D9').execute()
rect_values = sheet_read_rect.get('values', [])



for item in rect_values:
    holdings[item[0]] = {
        "shares" : float(item[1]),
        "total_cost" : float(item[3])
    }

sheet_read_rect = sheet.values().get(spreadsheetId = sheet_id, range = 'K2:N3').execute()
rect_values = sheet_read_rect.get('values', [])


for item in rect_values:
    holdings[item[0]] = {
        "shares" : float(item[1]),
        "total_cost" : float(item[3])
    }

print(holdings)

print("\n -- test --\n")

percents = {}

for t in tickers:
    percents[t] = ((prices[t] * holdings[t]["shares"]) - holdings[t]["total_cost"]) / holdings[t]["total_cost"]

print(percents)


###index creation is sample###

from pathlib import Path

def build_html(last_updated, worth, invested, profit, prices, percents):


    rows = "\n".join(
        f"<tr><td>{t}</td><td>{'' if p is None else f'${p:,.2f}'}</td><td>{percents[t]* 100:,.2f}</td></tr>"
        for t, p in prices.items()
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
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 12px 0; }}
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
    </div>

    <h2>Live Prices</h2>
    <table>
      <thead><tr><th>Ticker</th><th>Price</th><th>Total Change</th></tr></thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</body>
</html>
"""

html = build_html(last_updated, worth, invested, profit, prices, percents)
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