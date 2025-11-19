import streamlit as st
st.set_page_config(layout="wide")
import yfinance as yf
import pandas as pd
from option_data_calculator import get_option_data
from chart_generator import create_heat_map
from chart_generator import create_distribution_view

#constants

# 12weeks*5 days=60 (stock market is open for 5 days in a week)
windows = {
    "12W": 60,   
    "26W": 130,  
    "52W": 260  
}

summary_df=pd.DataFrame()

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

def create_summary_metrics(df,windows):
    # -1 will get the last row which is the latest data. So current price
    current_price = float(df['Close'].iloc[-1])
    summary = {"Stock": df['Stock'].iloc[0], "Current Price": current_price}

    #7day data
    day_close_7=float(df['Close'].iloc[-6])
    trend_7=((current_price-day_close_7)/day_close_7)*100
    summary["Trend last 7 days"]=trend_7

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
        summary = create_summary_metrics(df, windows)
        summary_list.append(summary)
    
    if summary_list:
        summary_df = pd.DataFrame(summary_list)
        st.dataframe(summary_df)
    else:
        st.error("No valid stock data could be retrieved. Please try again later.")


#heat map of summary

with tab2:
    st.header("Heat-Map")
    xaxis_labels=[]
    for label, _ in windows.items():
        xaxis_labels.append(f"{label} Delta")
    create_heat_map(summary_df,"Stock",xaxis_labels)

# --- Tab 3: Distribution View ---
with tab3:

    st.header("Price Distribution")
    selected_stock = st.selectbox("Select Stock", nifty50_companies, key="tab2")
    df = fetch_stock_data(selected_stock+".NS")
    latest_price = float(df['Close'].iloc[-1])
    latest_price_label=f"Latest Price: {latest_price:.2f}"

    for label, days in windows.items():
        prices = df['Close'][-days:]

        # PDF
        create_distribution_view(prices, latest_price, latest_price_label, 
                                 f"{selected_stock} PDF - Last {label}", "Price", "Density")

        # CDF
        create_distribution_view(prices, latest_price, latest_price_label, 
                                 f"{selected_stock} CDF - Last {label}", "Price", "Cumulative Probability", showCumulative=True)

with tab4:
    st.header("Risk - Reward Ratio")
    option_strategy = get_option_data(nifty50_companies)
    st.dataframe(option_strategy)