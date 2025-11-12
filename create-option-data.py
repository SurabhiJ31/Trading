import requests
import pandas as pd
import os
companies = [
                "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
                "ITC", "LT", "SBIN", "BHARTIARTL", "HINDUNILVR",
                "ASIANPAINT", "AXISBANK", "KOTAKBANK", "BAJFINANCE",
                "ADANIENT", "ADANIPORTS", "SUNPHARMA", "HCLTECH",
                "ULTRACEMCO", "TITAN", "WIPRO", "ONGC", "MARUTI",
                "POWERGRID", "NTPC", "TATAMOTORS", "JSWSTEEL",
                "TATASTEEL", "BAJAJFINSV", "NESTLEIND", "TECHM",
                "COALINDIA", "GRASIM", "SBILIFE", "HDFCLIFE",
                "DRREDDY", "BRITANNIA", "CIPLA", "EICHERMOT",
                "HEROMOTOCO", "TATACONSUM", "INDUSINDBK", "APOLLOHOSP",
                "BPCL", "BAJAJ-AUTO", "DIVISLAB", "HINDALCO",
                "ADANIGREEN", "ADANIPOWER", "DABUR", "SHRIRAMFIN"
            ]

def create_session(url):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive",
    })
    session.get(url, timeout=10)
    return session

def get_option_chain_data(symbol):
   
    session = create_session(f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}")
    url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
    response = session.get(url, timeout=10)
    print(f"Status code: {response.status_code}")
    print("Response length:", len(response.text))
    print("Preview:", response.text[:500])
    response.raise_for_status()
    failedComp=[]
    df=pd.DataFrame()
    try:
      data = response.json()
      records=[]
      for row in data['records']['data']:
          ce = row.get('CE')
          pe = row.get('PE')
          underlying = data['records']['underlyingValue']

          if ce:
              records.append({
                  'Company':symbol,
                  'Strike': ce['strikePrice'],
                  'Type': 'CALL',
                  'Expiry Date': ce['expiryDate'],
                  'Last Price': ce['lastPrice'],
                  'Underlying Value': underlying
              })
          if pe:
              records.append({
                 'Company':symbol,
                  'Strike': pe['strikePrice'],
                  'Type': 'PUT',
                  'Expiry Date': pe['expiryDate'],
                  'Last Price': pe['lastPrice'],
                  'Underlying Value': underlying
              })
      df=pd.DataFrame(records)
    except:
      failedComp.append(symbol)
    return df

option_dfs=[]
output_dir = "option-data"
os.makedirs(output_dir, exist_ok=True)
for comp in companies:
  print(f"Fetching data for {comp}:")
  option_data = get_option_chain_data(comp)
  option_dfs.append(option_data)
final_df = pd.concat(option_dfs,ignore_index=True)
file_path = os.path.join(output_dir, "options.xlsx")
final_df.to_excel(file_path, index=False)