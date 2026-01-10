from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import configs

#redundant funcs removed from main.py to its own util page 

def create_service():
    """Start a google sheet service"""
    credentials = Credentials.from_service_account_file(configs.SERVICE_ACCOUNT_FILE, scopes = configs.SCOPES)
    service = build('sheets', 'v4', credentials = credentials)
    return service.spreadsheets()



def get_from_sheet(sheet, sp_range):
    """get a single value from sheet specifc range"""
    sheet_read = sheet.values().get(spreadsheetId = configs.SHEET_ID, range = sp_range).execute()
    val = float(sheet_read.get('values')[0][0])
    return val



def get_tickers(sheet, sp_range):
    """gets  a list of tickers from a range"""
    sheet_read = sheet.values().get(spreadsheetId = configs.SHEET_ID, range = sp_range).execute()
    tickers = [row[0].strip() for row in sheet_read.get('values', []) if row and row[0].strip()]
    return tickers



def get_holdings(sheet, sp_range):
    """get the static values from sheet ..shares of given total cost"""
    sheet_read = sheet.values().get(spreadsheetId = configs.SHEET_ID, range = sp_range).execute()
    vals = sheet_read.get('values', [])

    holdings = {}
    for item in vals:
        holdings[item[0]] = {"shares" : float(item[1]), "total_cost" : float(item[3])}
    return holdings
