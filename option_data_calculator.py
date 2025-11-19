import os
import pandas as pd
import streamlit as st

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


def get_option_data(companies):
    file_path = os.path.join("option-data", "options.xlsx")
    all_options_df = pd.read_excel(file_path)
    selected_stock = st.selectbox("Select Stock", companies, key="tab3")
    option_type = st.selectbox("Option Type", ["PUT", "CALL"])
    
    stock_options_df = all_options_df[(all_options_df['Company']==selected_stock) & (all_options_df['Type']==option_type)]
    expiryDates = stock_options_df['Expiry Date'].unique()
    selected_expiry_Date = st.selectbox("Select Expiry Date", expiryDates) 
    stock_options_df = stock_options_df[stock_options_df["Expiry Date"]==selected_expiry_Date]
    option_strategy = get_option_spread(stock_options_df,option_type)
    return option_strategy