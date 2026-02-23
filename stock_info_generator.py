from datetime import datetime, timedelta
import yfinance as yf
import streamlit as st
import pandas as pd
from fno import has_fno
from ta.momentum import RSIIndicator
from service_provider import get_companies_service

comp_service=get_companies_service()

windows = {
    "12W": 60,   
    "26W": 130,  
    "52W": 260  
}

BILLION = 1000000000

symbols=comp_service.get_company_symbols()


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


def get_moving_average(series, days):
    return round(float(series.tail(days).mean()),2)

def get_rsi(series,days):
    rsi = RSIIndicator(series, window=days).rsi()
    return round(rsi.iloc[-1], 2)




def get_computed_date(all_data):
    infos=[]
    for s, df in all_data.items():
        if has_fno(s):
            close_series = df["Close"]
            if isinstance(close_series, pd.DataFrame):
                close_series = close_series.iloc[:, 0]
            current = float(close_series.iloc[-1])
            ma_14=get_moving_average(close_series,14)
            ma_30=get_moving_average(close_series,30)
            ma_60=get_moving_average(close_series,60)
            info = {"Stock": s,
                   "Current Price": current,
                   "Industry": comp_service.get_industry(s),
                   "MA - 14D": ma_14,
                   "MA - 30D": ma_30,
                   "MA - 60D": ma_60,
                   "percent change - 14D": round(((current-ma_14)/current),2),
                   "percent change - 30D": round(((current-ma_30)/current),2),
                   "percent change - 60D": round(((current-ma_60)/current),2),
                   "RSI - 14D": get_rsi(close_series,14),
                   "RSI - 30D": get_rsi(close_series,30),
                   "RSI - 60D": get_rsi(close_series,60)}
            infos.append(info)
    return pd.DataFrame(infos)
            









@st.cache_data(show_spinner=False, ttl=900)
def get_mohit_data():
    all_data = get_stock_data()
    return get_computed_date(all_data)

    
