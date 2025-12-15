from datetime import datetime, timedelta
import yfinance as yf
import streamlit as st
import pandas as pd
from companies import get_company_symbols, get_industry
from fno import has_fno
from concurrent.futures import ThreadPoolExecutor, as_completed
from chart_generator import create_distribution_view, create_heat_map, create_line_chart

windows = {
    "12W": 60,   
    "26W": 130,  
    "52W": 260  
}

BILLION = 1000000000

symbols=get_company_symbols()


@st.cache_data(ttl="1d")
def get_stock_data():
    """
    Batched download to ensure data stays aligned per ticker and avoid
    per-symbol inconsistencies seen with many concurrent calls.
    Returns a dict: symbol -> DataFrame with columns (Open, High, Low, Close, Adj Close, Volume, Stock)
    """
    ticker_list = [s + ".NS" for s in symbols]
    data = yf.download(
        ticker_list,
        period="1y",
        progress=False,
        group_by="ticker",
        threads=True,
        auto_adjust=False,
    )

    out = {}
    if isinstance(data.columns, pd.MultiIndex):
        # MultiIndex columns: level 0 = ticker
        for s in symbols:
            tkr = s + ".NS"
            try:
                df = data.xs(tkr, level=0, axis=1)
            except KeyError:
                continue
            df = df.dropna()
            if df.empty:
                continue
            df = df.copy()
            df["Stock"] = s
            out[s] = df
    else:
        # Single symbol case fallback
        df = data.dropna()
        if not df.empty:
            df = df.copy()
            df["Stock"] = symbols[0] if symbols else ""
            out[df["Stock"].iloc[0]] = df

    return out

def get_trend(df,days,current_price):
    close_series = df["Close"]
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.iloc[:, 0]
    day_close=float(close_series.iloc[-days])
    trend=((current_price-day_close)/day_close)*100
    return trend

def build_summaries(all_data, fundamentals=None):
    summaries = []
    fundamentals = fundamentals or {}
    for s, df in all_data.items():
        close_series = df["Close"]
        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.iloc[:, 0]
        current = float(close_series.iloc[-1])
        summary = {"Stock": s,
                   "Current Price": current,
                   "Market Cap (Billion)": fundamentals.get(s, ""),
                   "Industry": get_industry(s),
                   "Options Available": has_fno(s),
                   "Trend last 1 day": get_trend(df, 2, current),
                   "Trend last 7 days": get_trend(df, 6, current)}
        for label, days in windows.items():
            prices = close_series[-days:]
            if prices.empty:
                continue
            high, low = float(prices.max()), float(prices.min())
            denom = high - low
            delta = 1 - ((high - current) / denom) if denom != 0 else 0
            summary[f"{label} High"] = round(high, 2)
            summary[f"{label} Low"] = round(low, 2)
            summary[f"{label} Delta"] = round(delta, 2)
        summaries.append(summary)
    return pd.DataFrame(summaries)


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_fundamentals():
    
    m_caps = {}
    def fetch_one(sym: str):
        try:
            cap = yf.Ticker(sym + ".NS").fast_info.get("marketCap")
            return sym, round(float(cap)/BILLION,2) if cap else 0
        except Exception:
            return sym, ""

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch_one, s) for s in symbols]
        for fut in as_completed(futures):
            sym, val = fut.result()
            if val:
                m_caps[sym] = val
    

    return m_caps

@st.cache_data(show_spinner=False, ttl=900)
def get_summary():
    all_data = get_stock_data()
    fundamentals = fetch_fundamentals()
    summaries_df = build_summaries(all_data, fundamentals)
    return all_data, summaries_df


def get_distribution(stock):
    alldata = get_stock_data()
    df=alldata[stock]
    latest_price = float(df['Close'].iloc[-1].item())
    latest_price_label=f"Latest Price: {latest_price:.2f}"

    for label, days in windows.items():
        prices = df['Close'][-days:]

        # PDF
        create_distribution_view(prices, latest_price, latest_price_label, 
                                 f"{stock} PDF - Last {label}", "Price", "Density")

        # CDF
        create_distribution_view(prices, latest_price, latest_price_label, 
                                 f"{stock} CDF - Last {label}", "Price", "Cumulative Probability", showCumulative=True)


def get_heat_map():
    alldata,df=get_summary()
    xaxis_labels=[]
    for label, _ in windows.items():
        xaxis_labels.append(f"{label} Delta")
    create_heat_map(df,"Stock",xaxis_labels)

    st.subheader("Line chart")
    selected_stock = st.selectbox("Select Stock", symbols, key="tab2key")
    
    stock_df = alldata[selected_stock]
    stock_df.reset_index(inplace=True)
    three_months_ago = datetime.now() - timedelta(days=90)
    df_3m = stock_df[stock_df['Date'] >= three_months_ago]
    create_line_chart(df_3m)

    
