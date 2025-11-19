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