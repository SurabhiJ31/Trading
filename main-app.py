
import streamlit as st
st.set_page_config(
    page_title="Nifty Analysis Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
import pandas as pd
from companies import get_company_symbols, get_nifty50_companies
from ai_insights import get_insights
from stock_info_generator import get_summary, get_distribution, get_heat_map, get_mohit_data
from option_data_calculator import get_option_data



summary_df=pd.DataFrame()
symbols=get_company_symbols()

def refresh_button_clicked():
    st.cache_data.clear()

# --- Global Style ---
st.markdown(
    """
    <style>
        .app-title {font-size:32px; font-weight:700; margin-bottom:4px;}
        .app-subtitle {color:#6c757d; margin-bottom:24px;}
        .stTabs [role="tab"] {padding: 10px 16px; font-weight:600;}
        .card {
            padding: 16px;
            border-radius: 12px;
            background: #0e1117;
            border: 1px solid #1f2937;
            box-shadow: 0 4px 12px rgba(0,0,0,0.35);
        }
        .muted {color:#9ca3af;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Sidebar ---
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    st.button("Refresh data", on_click=refresh_button_clicked, use_container_width=True)
    st.markdown("---")
    st.markdown("**Universe:** Nifty 500")
    st.markdown("**Data source:** Yahoo Finance")
    st.markdown("**Updated:** Cached (1d)")

# --- Header ---
st.markdown('<div class="app-title">Nifty Analysis Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Multi-view market snapshot for Nifty 500</div>', unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5,tab6 = st.tabs(
    ["📈 Summary", "🌡️ Heat-Map", "📊 Distribution", "⚖️ Risk-Reward", "🧠 Insights","TEST"]
)


def get_moving_average(series, days):
    return series.rolling(window=days).mean()

# --- Tab 1: Summary View ---
with tab1:
    
    with st.container():
        data,df =get_summary()
        st.dataframe(df)


#heat map of summary
with tab2:
    st.subheader("Heat-Map")
    get_heat_map()

# --- Tab 3: Distribution View ---
with tab3:

    st.header("Price Distribution")
    selected_stock = st.selectbox("Select Stock", symbols, key="tab3key")
    get_distribution(selected_stock)
    

with tab4:
    st.header("Risk - Reward Ratio")
    nifty_companies = get_nifty50_companies()
    option_strategy = get_option_data(nifty_companies)
    if option_strategy is None:
        st.text("No data")
    else:    
     st.dataframe(option_strategy)

with tab5:
    st.header("Market Insights")
    get_insights()

with tab6:
    comp_df = get_mohit_data()

    # rsi_cols = ["RSI - 14D", "RSI - 30D", "RSI - 60D"]
    # rsi_ranges = {}
    # rsi_cols_layout = st.columns(3)
    # for i, col in enumerate(rsi_cols):
    #     rsi_min, rsi_max = rsi_cols_layout[i].slider(
    #         f"{col} range",
    #         min_value=0,
    #         max_value=100,
    #         value=(30, 70)
    #     )
    #     rsi_ranges[col] = (rsi_min, rsi_max)

    # pct_cols = ["percent change - 14D", "percent change - 30D", "percent change - 60D"]
    # pct_ranges = {}
    # pct_cols_layout = st.columns(3)
    # for i, col in enumerate(pct_cols):
    #     pct_min, pct_max = pct_cols_layout[i].slider(
    #         f"{col} range",
    #         min_value=-1.0,
    #         max_value=1.0,
    #         value=(-0.05, 0.05),
    #         step=0.01,
    #         format="%.2f"
    #     )
    #     pct_ranges[col] = (pct_min, pct_max)

    # # --- Apply Filters ---
    # df_filtered = comp_df.copy()

    # for col, (min_v, max_v) in rsi_ranges.items():
    #     if col in df_filtered.columns:
    #         df_filtered = df_filtered[df_filtered[col].between(min_v, max_v)]

    # for col, (min_v, max_v) in pct_ranges.items():
    #     if col in df_filtered.columns:
    #         df_filtered = df_filtered[df_filtered[col].between(min_v, max_v)]

    
    st.dataframe(comp_df)



