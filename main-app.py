
import streamlit as st
st.set_page_config(layout="wide")
import yfinance as yf
import pandas as pd
import plotly.express as px
import time
import random
from datetime import datetime, timedelta
from option_data_calculator import get_option_data
from chart_generator import create_heat_map
from chart_generator import create_distribution_view
from companies import get_companies, get_industry,get_nifty50_companies
from concurrent.futures import as_completed, ThreadPoolExecutor
from numerize import numerize
from fno import has_fno
from ai_insights import get_insights
import asyncio
#constants

# 12weeks*5 days=60 (stock market is open for 5 days in a week)
windows = {
    "12W": 60,   
    "26W": 130,  
    "52W": 260  
}

summary_df=pd.DataFrame()



@st.cache_data
def fetch_stock_data(symbol, period="1y"):
    time.sleep(random.uniform(0.5, 1.5))
    df = yf.download(symbol, period=period, progress=False)
    if df.empty:
        st.warning(f"No data returned for {symbol}. Skipping...")
        return None
    if isinstance(df.columns,pd.MultiIndex):
        df.columns=df.columns.get_level_values(0)
    df = df.dropna()
    df['Stock'] = symbol
    return df

def get_ticker(symbol):
    ticker=yf.Ticker((symbol+".NS"))
    return ticker

def get_market_cap(symbol):
    ticker = get_ticker(symbol)
    if ticker is None:
        return ""
    return numerize.numerize(ticker.fast_info['marketCap'])

def get_trend(df,days,current_price):
    day_close=float(df['Close'].iloc[-days].item())
    trend=((current_price-day_close)/day_close)*100
    return trend

def create_summary_metrics(df,company):
    try:
        if df is None or df.empty:
            return None
        # -1 will get the last row which is the latest data. So current price
        current_price = float(df['Close'].iloc[-1].item())
        summary = {"Stock": df['Stock'].iloc[0], "Current Price": current_price}

        summary["Industry"]=get_industry(company)
        summary["Market Cap"] = get_market_cap(company)
        summary["Options Available"]=has_fno(company)

        #7day data
        
        summary["Trend last 1 day"]=get_trend(df,2,current_price)
        summary["Trend last 7 days"]=get_trend(df,6,current_price)

        for label, days in windows.items():
            window_prices = df['Close'][-days:]
            if len(window_prices) == 0:
                continue
            high = float(window_prices.max().item())
            low = float(window_prices.min().item())
            curr_val = float(current_price)
            delta = (high - curr_val) / (high - low) if high != low else 0

            #delta to represent 1 for high and 0 for low
            delta =1-delta
            summary[f"{label} High"] = round(high, 2)
            summary[f"{label} Low"] = round(low, 2)
            summary[f"{label} Delta"] = round(delta, 2)
        return summary
    
    except Exception as e:
        stock = df['Stock'].iloc[0] if df is not None else "UNKNOWN"
        print(f"ERROR FOR STOCK: {stock} → {e}")
        return None
    
def refresh_button_clicked():
    st.cache_data.clear()

def get_summary(stockSymbol):
    df = fetch_stock_data(stockSymbol+".NS")
    return create_summary_metrics(df,stockSymbol)

# --- Sidebar / Tabs ---
st.title("Nifty 50 Analysis App")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary View", "Heat-Map View", "Distribution View", "Risk-Reward Ratio View", "Insights"])


nifty_companies = get_companies()

# --- Tab 1: Summary View ---
with tab1:
    st.header("Summary Metrics for Nifty 500 Stocks")
    st.button("Refresh",on_click = refresh_button_clicked)
    summary_list = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(get_summary, company) for company in nifty_companies]

        for f in as_completed(futures):
            if f.result() is not None:
                summary_list.append(f.result())
    if summary_list:
        summary_df = pd.DataFrame(summary_list)
        st.dataframe(summary_df)
    else:
        st.error("No valid stock data could be retrieved. Please try again later.")
    
    


#heat map of summary
with tab2:
    st.subheader("Heat-Map")
    xaxis_labels=[]
    for label, _ in windows.items():
        xaxis_labels.append(f"{label} Delta")
    create_heat_map(summary_df,"Stock",xaxis_labels)

    st.subheader("Line chart")
    selected_stock = st.selectbox("Select Stock", nifty_companies, key="tab2key")
    df = fetch_stock_data(selected_stock+".NS")
    
    df.reset_index(inplace=True)
    three_months_ago = datetime.now() - timedelta(days=90)
    df_3m = df[df['Date'] >= three_months_ago]

    fig = px.line(df_3m, x='Date', y=f'Close', title="Closing Price - Last 3 Months")
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 3: Distribution View ---
with tab3:

    st.header("Price Distribution")
    selected_stock = st.selectbox("Select Stock", nifty_companies, key="tab3key")
    df = fetch_stock_data(selected_stock+".NS")
    latest_price = float(df['Close'].iloc[-1].item())
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
    option_strategy = get_option_data(nifty_companies)
    st.dataframe(option_strategy)

with tab5:
    st.header("Market Insights")
    get_insights()

