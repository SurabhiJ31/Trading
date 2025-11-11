import streamlit as st
st.set_page_config(layout="wide")
import yfinance as yf
import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

#constants

# 12weeks*5 days=60 (stock market is open for 5 days in a week)
windows = {
    "12W": 60,   
    "26W": 130,  
    "52W": 260  
}

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

@st.cache_data
def get_nifty50_companies():
    session = create_session("https://www.nseindia.com")
    url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
    response = session.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    companies = []
    for item in data["data"][1:]:
        companies.append(item["symbol"])
    return companies

@st.cache_data
def fetch_stock_data(symbol, period="1y"):
    df = yf.download(symbol, period=period)
    df = df.dropna()
    df['Stock'] = symbol
    return df

def compute_summary_metrics(symbol, period="1y"):
    
    # -1 will get the last row which is the latest data. So current price
    current_price = float(df['Close'].iloc[-1])

    
    summary = {"Stock": df['Stock'].iloc[0], "Current Price": current_price}

    for label, days in windows.items():
        window_prices = df['Close'][-days:]
        high = float(window_prices.max())
        low = float(window_prices.min())
        curr_val = float(current_price)
        delta = (high - curr_val) / (high - low) if high != low else 0
        summary[f"{label} High"] = round(high, 2)
        summary[f"{label} Low"] = round(low, 2)
        summary[f"{label} Delta"] = round(delta, 2)
    return summary

def get_option_chain_data(symbol):
    """
    month_year example: 'Oct 2025'
    """
    session = create_session(f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}")
    url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
    response = session.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data

def get_option_records(data, option_type, expiry_date):
    records=[]
    # Filter data for selected expiry
    for item in data["records"]["data"]:
        if item.get("expiryDate") != expiry_date:
            continue

        if option_type.upper() == "CALL" and "CE" in item:
            opt = item["CE"]
        elif option_type.upper() == "PUT" and "PE" in item:
            opt = item["PE"]
        else:
            continue

        records.append({
        "Strike": opt.get("strikePrice"),
        "Type": option_type.upper(),
        "Expiry Date": expiry_date,
        "Last Price": opt.get("lastPrice"),
        "Underlying Value": opt.get("underlyingValue")
        })
    df_op_data = pd.DataFrame(records)
    return df_op_data

def get_option_spread(df, option_type):
    if option_type=="PUT":
        return get_bull_put_spread(df)
    else :
        return get_bear_call_spread(df)
    

def get_bull_put_spread(df):
    results=[]
    for i in range(len(df)):
        for j in range(len(df)):
            higher = df.iloc[i]
            lower = df.iloc[j]

      # We only want spreads where we SELL higher strike and BUY lower strike
            if higher["Strike"] > lower["Strike"]:
                premium_received = higher["Last Price"] - lower["Last Price"]
                strike_diff = higher["Strike"] - lower["Strike"]

                max_profit = premium_received
                max_loss = strike_diff - premium_received
                rr_ratio = round(max_loss / max_profit, 2) if max_profit != 0 else None
                breakeven = higher["Strike"] - premium_received

                results.append({
              "Short Strike": higher["Strike"],
              "Short Strike Price":higher["Last Price"],
              "Long Strike": lower["Strike"],
              "Long Strike Price":lower["Last Price"],
              "Max Profit": round(max_profit, 2),
              "Max Loss": round(max_loss, 2),
              "Risk-Reward Ratio": rr_ratio,
              "Breakeven Point": round(breakeven, 2),
              "Underlying Value":higher["Underlying Value"]
                })
    return pd.DataFrame(results)

def get_bear_call_spread(df):
    results = []

    # Compare each lower-strike call with each higher-strike call
    for i in range(len(df)):
        for j in range(len(df)):
            lower = df.iloc[i]
            higher = df.iloc[j]

            # We only want spreads where we SELL lower strike and BUY higher strike
            if lower["Strike"] < higher["Strike"]:
                premium_received = lower["Last Price"] - higher["Last Price"]
                strike_diff = higher["Strike"] - lower["Strike"]

                max_profit = premium_received
                max_loss = strike_diff - premium_received
                rr_ratio = round(max_loss / max_profit, 2) if max_profit != 0 else None
                breakeven = lower["Strike"] + premium_received

                results.append({
                    "Short Strike": lower["Strike"],
                    "Short Strike Price":lower["Last Price"],
                    "Long Strike": higher["Strike"],
                    "Long Strike Price":higher["Last Price"],
                    "Max Profit": round(max_profit, 2),
                    "Max Loss": round(max_loss, 2),
                    "Risk-Reward Ratio": rr_ratio,
                    "Breakeven Point": round(breakeven, 2),
                    "Underlying Value":lower["Underlying Value"]
                })

    return pd.DataFrame(results)

# --- Sidebar / Tabs ---
st.title("Nifty 50 Analysis App")
tab1, tab2, tab3 = st.tabs(["Summary View", "Distribution View", "Risk-Reward Ratio View"])

nifty50_companies = get_nifty50_companies()

# --- Tab 1: Summary View ---
with tab1:
    st.header("Summary Metrics for Nifty 50 Stocks")
    summary_list = []
    for company in nifty50_companies:
        df = fetch_stock_data(company+".NS")
        summary = compute_summary_metrics(df)
        summary_list.append(summary)

    
    summary_df = pd.DataFrame(summary_list)
    st.dataframe(summary_df)

# --- Tab 2: Distribution View ---
with tab2:

    st.header("Price Distribution")
    selected_stock = st.selectbox("Select Stock", nifty50_companies, key="tab2")
    df = fetch_stock_data(selected_stock+".NS")
    latest_price = float(df['Close'].iloc[-1])

    for label, days in windows.items():
        prices = df['Close'][-days:]

        # PDF
        plt.figure(figsize=(10, 4))
        sns.kdeplot(prices, fill=True, color="royalblue", alpha=0.6)
        plt.axvline(latest_price, color="red", linestyle="--", label=f"Latest Price: {latest_price:.2f}")
        plt.title(f"{selected_stock} PDF - Last {label}")
        plt.xlabel("Price")
        plt.ylabel("Density")
        plt.legend()
        st.pyplot(plt.gcf())
        plt.clf()

        # CDF
        plt.figure(figsize=(10, 4))
        sns.kdeplot(prices, cumulative=True, fill=True, color="green", alpha=0.5)
        plt.axvline(latest_price, color="red", linestyle="--", label=f"Latest Price: {latest_price:.2f}")
        plt.title(f"{selected_stock} CDF - Last {label}")
        plt.xlabel("Price")
        plt.ylabel("Cumulative Probability")
        plt.legend()
        st.pyplot(plt.gcf())
        plt.clf()

with tab3:
    st.header("Risk - Reward Ratio")
    selected_stock = st.selectbox("Select Stock", nifty50_companies, key="tab3")
    option_type = st.selectbox("Option Type", ["PUT", "CALL"])
    option_data=get_option_chain_data(selected_stock)

    expiryDates = option_data["records"].get('expiryDates')
    selected_expiry_Date = st.selectbox("Select Expiry Date", expiryDates)

    filteredData= get_option_records(option_data, option_type, selected_expiry_Date)
    option_strategy = get_option_spread(filteredData,option_type)

    st.dataframe(option_strategy)