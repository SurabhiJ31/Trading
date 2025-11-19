import streamlit as st
st.set_page_config(layout="wide")
import yfinance as yf
import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np

#constants

# 12weeks*5 days=60 (stock market is open for 5 days in a week)
windows = {
    "12W": 60,   
    "26W": 130,  
    "52W": 260  
}

summary_df=pd.DataFrame()

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

#@st.cache_data
def get_nifty50_companies():
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
        
    return companies

@st.cache_data
def fetch_stock_data(symbol, period="1y"):
    df = yf.download(symbol, period=period, progress=False)
    if df.empty:
        st.warning(f"No data returned for {symbol}. Skipping...")
        return None
    df = df.dropna()
    df['Stock'] = symbol
    return df

def compute_summary_metrics(symbol, period="1y"):
    
    # -1 will get the last row which is the latest data. So current price
    current_price = float(df['Close'].iloc[-1])

    
    summary = {"Stock": df['Stock'].iloc[0], "Current Price": current_price}

    #7day data
    day_close_7=float(df['Close'].iloc[-6])
    trend_7=(current_price-day_close_7)/day_close_7
    summary["Trend last 7 days"]=round(trend_7,2)

    for label, days in windows.items():
        window_prices = df['Close'][-days:]
        if len(window_prices) == 0:
            continue
        high = float(window_prices.max())
        low = float(window_prices.min())
        curr_val = float(current_price)
        delta = (high - curr_val) / (high - low) if high != low else 0

        #delta to represent 1 for high and 0 for low
        delta =1-delta
        summary[f"{label} High"] = round(high, 2)
        summary[f"{label} Low"] = round(low, 2)
        summary[f"{label} Delta"] = round(delta, 2)
    return summary

    

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

def refresh_button_clicked():
    st.cache_data.clear()

# --- Sidebar / Tabs ---
st.title("Nifty 50 Analysis App")
tab1, tab2, tab3, tab4 = st.tabs(["Summary View", "Heat-Map View", "Distribution View", "Risk-Reward Ratio View"])

nifty50_companies = get_nifty50_companies()

# --- Tab 1: Summary View ---
with tab1:
    st.header("Summary Metrics for Nifty 50 Stocks")

    st.button("Refresh",on_click = refresh_button_clicked)
    summary_list = []
    for company in nifty50_companies:
        df = fetch_stock_data(company+".NS")
        if df is None or df.empty:
            continue
        summary = compute_summary_metrics(df)
        summary_list.append(summary)

    
    if summary_list:
        summary_df = pd.DataFrame(summary_list)
        st.dataframe(summary_df)
    else:
        st.error("No valid stock data could be retrieved. Please try again later.")


#heat map of summary

with tab2:
    st.header("Heat-Map")
    cols_for_map=[]
    for label, days in windows.items():
        cols_for_map.append(f"{label} Delta")
    cols_for_map.append("Stock")

    filtered_df = summary_df[cols_for_map]
    df_heat = filtered_df.set_index("Stock")

    # Numeric matrix
    matrix = df_heat.values.astype(float)
    num_rows = len(df_heat)
    row_height = 0.25 
    fig_height = num_rows * row_height

    fig, ax = plt.subplots(figsize=(6, fig_height))
    heatmap = ax.imshow(matrix, cmap=plt.cm.get_cmap("Blues"), aspect='auto')

    ax.set_xticks(np.arange(len(df_heat.columns)))
    ax.set_yticks(np.arange(len(df_heat.index)))

    ax.set_xticklabels(df_heat.columns)
    ax.set_yticklabels(df_heat.index)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    # Annotate each cell with its value
    for i in range(len(df_heat.index)):
        for j in range(len(df_heat.columns)):
            ax.text(j, i, matrix[i, j], ha='center', va='center', color="black")
    
    plt.tight_layout()
    st.pyplot(fig)

# --- Tab 3: Distribution View ---
with tab3:

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

with tab4:
    st.header("Risk - Reward Ratio")
    file_path = os.path.join("option-data", "options.xlsx")
    all_options_df = pd.read_excel(file_path)

    selected_stock = st.selectbox("Select Stock", nifty50_companies, key="tab3")
    option_type = st.selectbox("Option Type", ["PUT", "CALL"])
    stock_options_df = all_options_df[(all_options_df['Company']==selected_stock) & (all_options_df['Type']==option_type)]
    expiryDates = stock_options_df['Expiry Date'].unique()
    selected_expiry_Date = st.selectbox("Select Expiry Date", expiryDates) 
    stock_options_df = stock_options_df[stock_options_df["Expiry Date"]==selected_expiry_Date]
    option_strategy = get_option_spread(stock_options_df,option_type)
    st.dataframe(option_strategy)