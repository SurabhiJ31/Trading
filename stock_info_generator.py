
import yfinance as yf
import streamlit as st
import pandas as pd
from fno import has_fno, get_companies_with_fno
from ta.momentum import RSIIndicator
from service_provider import get_companies_service, get_stock_info_service
from global_logging import logger
from datetime import datetime
import time

comp_service=get_companies_service()
stock_info_service=get_stock_info_service()



symbols=comp_service.get_company_symbols()




def get_moving_average(series, days):
    return round(float(series.tail(days).mean()),2)

def get_rsi(series,days):
    rsi = RSIIndicator(series, window=days).rsi()
    return round(rsi.iloc[-1], 2)

@st.cache_data(ttl=86400)
def get_stock_map():
    return comp_service.get_stocks_with_ids()

def insert_nse_raw_data(timerange):

    ticker_list = [s + ".NS" for s in get_companies_with_fno()]
    stock_map = get_stock_map()
    records = []
    data = None

    try:
        data = yf.download(
            ticker_list,
            period=timerange,
            group_by="ticker",
            threads=True,
            progress=False
        )
    except Exception as e:
        logger.error(e)

    if data is not None:

        if isinstance(data.columns, pd.MultiIndex):
            for s in symbols:
                tkr = s + ".NS"
                try:
                    df = data.xs(tkr, level=0, axis=1)
                except KeyError:
                    continue

                df = df.dropna()
                if df.empty:
                    continue

                

                stock_id = stock_map[s]
                if stock_map[s] is None:
                    logger.info(f"Not exists {s}")

                

                for date, row in df.iterrows():
                    try:
                        records.append({
                            "stock_id": stock_id,
                            "trade_date": str(date.date()),
                            "open": float(row["Open"]),
                            "high": float(row["High"]),
                            "low": float(row["Low"]),
                            "close": float(row["Close"]),
                            "volume": int(row["Volume"])
                        })
                    except Exception as e:
                        logger.error(e)
                        logger.info(f"Problem in record {stock_id} with data {row}")
    
    if records:
        stock_info_service.add_daily_records(records)

def compute_nse_daily_metrics():

    metrics_records=[]
    stock_map = comp_service.get_stocks_with_ids()
    for s in get_companies_with_fno():
        try:
            stock_id = stock_map[s]
            records = stock_info_service.get_previous_records(100, stock_id)
            df=pd.DataFrame(records)
            if df.empty:
                logger.info("empty")
                continue
            if len(df) < 60:
                logger.info(f"length for stock {stock_id} is {len(df)}")
                continue

            latest_trade_date = df["trade_date"].iloc[-1]

            if stock_info_service.does_daily_metrics_exist(stock_id, latest_trade_date):
                logger.info(f"already exists for {stock_id}")
                continue  # already computed

            close_series = df["close"]

            current = float(close_series.iloc[-1])

            ma_14=get_moving_average(close_series,14)
            ma_30=get_moving_average(close_series,30)
            ma_60=get_moving_average(close_series,60)

            rsi_14 = get_rsi(close_series,14)
            rsi_30 = get_rsi(close_series,30)
            rsi_60 = get_rsi(close_series,60)

            metrics_records.append({
                "stock_id": stock_id,
                "trade_date": latest_trade_date,
                "current_price": current,
                "ma_14": ma_14,
                "ma_30": ma_30,
                "ma_60": ma_60,
                "pct_change_14": round((current - ma_14) / current, 4),
                "pct_change_30": round((current - ma_30) / current, 4),
                "pct_change_60": round((current - ma_60) / current, 4),
                "rsi_14": rsi_14,
                "rsi_30": rsi_30,
                "rsi_60": rsi_60
            })
        except Exception as e:
            logger.error(msg=f" Erro for stock {stock_id}", args=e)

    if metrics_records:
        stock_info_service.add_daily_metrics(metrics_records)   

    return metrics_records



def nse_raw_data_updater():
    while True:
        logger.info(f"nse raw data executed at {datetime.now().date()}")
        a = insert_nse_raw_data("1d")
        logger.info(f"records count {len(a)}")
        time.sleep(60) #10 mins

def compute_ma_buckets(date):
    ma_more_than_current=[]
    ma_less_than_current=[]
    logger.info(f"fetching metrics for {date}")
    a=stock_info_service.get_combined_daily_metrics(str(date))
    metrics=a.data
    if len(metrics) !=0:
        for row in metrics:
            current = row["current_price"]

            if current > row["ma_14"] and current > row["ma_30"] and current > row["ma_60"]:
                ma_less_than_current.append(row["symbol"])

            if current < row["ma_14"] and current < row["ma_30"] and current < row["ma_60"]:
                ma_more_than_current.append(row["symbol"])
    return ma_less_than_current,ma_more_than_current




def get_all_nse_kpis(date):
    logger.info(f"fetching metrics for {date}")
    a=stock_info_service.get_combined_daily_metrics(str(date))
    
    if len(a.data)==0:
        logger.info("metrics not available. Inserting data")
        insert_nse_raw_data("1d")
        logger.info("calculating data")
        compute_nse_daily_metrics()

    df = (
    pd.json_normalize(a.data)
      .rename(columns={
          "rsi_14": "RSI - 14D",
          "rsi_30": "RSI - 30D",
          "rsi_60": "RSI - 60D",
          "pct_change_14":"percent change - 14D",
          "pct_change_30":"percent change - 30D",
          "pct_change_60":"percent change - 60D",
      })
)
    
    return df
