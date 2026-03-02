
import streamlit as st
st.set_page_config(
    page_title="Nifty Analysis Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
import pandas as pd
from ai_insights import get_insights, render_batch_insights
from stock_info_generator import insert_nse_raw_data,get_all_nse_kpis,compute_nse_daily_metrics
from nse_announcement_parser import nse_feed_updater
import threading
from datetime import date, timedelta
from notification_manager import notification_fragment
from data_service.announcement_service import AnnouncementService
from service_provider import get_companies_service,get_stock_info_service
from global_logging import logger

if "notifications" not in st.session_state:
    st.session_state.notifications = []

if "thread_started" not in st.session_state:
    thread = threading.Thread(
        target=nse_feed_updater,
        daemon=True
    )
    thread.start()
    st.session_state.thread_started = True




summary_df=pd.DataFrame()
ann_service=AnnouncementService()
comp_service=get_companies_service()
stock_info_service=get_stock_info_service()
symbols=comp_service.get_company_symbols()
    
if "filtered_df" not in st.session_state:
    st.session_state.filtered_df = get_all_nse_kpis(date.today())

if "edited_df" not in st.session_state:
    st.session_state.edited_df = None

if "editor_key" not in st.session_state:
    st.session_state.editor_key = 0


if "date_filter_type" not in st.session_state:
    st.session_state.date_filter_type = "Today"

if "custom_start_date" not in st.session_state:
    st.session_state.custom_start_date = date.today()

if "custom_end_date" not in st.session_state:
    st.session_state.custom_end_date = date.today()


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
    st.button("Refresh data", on_click=refresh_button_clicked, width="content")
    st.markdown("---")
    st.markdown("**Universe:** Nifty 500")
    st.markdown("**Data source:** Yahoo Finance")
    st.markdown("**Updated:** Cached (1d)")




notification_fragment()

# --- Header ---
st.markdown('<div class="app-title">Nifty Analysis Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Multi-view market snapshot for Nifty 500</div>', unsafe_allow_html=True)


# --- Tabs ---
tab1, tab2, tab3,tab4 = st.tabs(
    ["📈 Summary", "🧠 Insights","nse announcements","TEST2"]
)


with tab1:
    with st.form("filter_form"):
        rsi_cols = ["RSI - 14D", "RSI - 30D", "RSI - 60D"]
        rsi_ranges = {}
        rsi_cols_layout = st.columns(3)
        for i, col in enumerate(rsi_cols):
            rsi_min, rsi_max = rsi_cols_layout[i].slider(
                f"{col} range",
                min_value=0,
                max_value=100,
                value=(30, 70)
            )
            rsi_ranges[col] = (rsi_min, rsi_max)

        pct_cols = ["percent change - 14D", "percent change - 30D", "percent change - 60D"]
        pct_ranges = {}
        pct_cols_layout = st.columns(3)
        for i, col in enumerate(pct_cols):
            pct_min, pct_max = pct_cols_layout[i].slider(
                f"{col} range",
                min_value=-1.0,
                max_value=1.0,
                value=(-0.05, 0.05),
                step=0.01,
                format="%.2f"
            )
            pct_ranges[col] = (pct_min, pct_max)
        
        submitted = st.form_submit_button("Run")
        if submitted:
            comp_df = get_all_nse_kpis(date.today())
            df_filtered = comp_df.copy()

            for col, (min_v, max_v) in rsi_ranges.items():
                if col in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[col].between(min_v, max_v)]

            for col, (min_v, max_v) in pct_ranges.items():
                if col in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[col].between(min_v, max_v)]
            
            st.session_state.filtered_df=df_filtered

    if st.session_state.filtered_df is not None:
        filtered_df_copy = st.session_state.filtered_df.copy()
        if "Select" not in filtered_df_copy.columns:
            filtered_df_copy.insert(0, "Select", False)
        st.session_state.edited_df = filtered_df_copy
        
        if st.session_state.edited_df is not None:

            edited_df = st.data_editor(
                st.session_state.edited_df,
                key=f"company_selector_{st.session_state.editor_key}",
                hide_index=True,
                width="content",
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select companies to run operation"
                    )
                }
            )
            st.session_state.edited_df = edited_df
            selected_df = st.session_state.edited_df[
                    st.session_state.edited_df["Select"]
                ]
            selected_companies = selected_df["symbol"].tolist()
            if selected_companies:
                st.markdown(
                    f"**Selected Companies ({len(selected_companies)}):** "
                    + ", ".join(selected_companies)
                )
            else:
                st.caption("No companies selected")

            col1, col2 = st.columns([1, 3])

            with col1:
                proceed = st.button("Get insights for selected companies",disabled=len(selected_companies)==0)

            with col2:
                clear = st.button("Clear selection",disabled=len(selected_companies)==0)
            if proceed:
                if selected_df.empty:
                    st.warning("Please select at least one company.")
                else:
                    render_batch_insights(selected_companies)
            
            if clear and st.session_state.edited_df is not None:
                st.session_state.edited_df["Select"]=False
                st.session_state.editor_key += 1
                st.rerun()

            





with tab2:
     st.header("Market Insights")
     get_insights()


def render_filters():
    try:
        col1, col2 = st.columns([2, 3])

        with col1:
            filter_option = st.selectbox(
                "Select Date Filter",
                ["Today", "Yesterday", "Custom"],
                index=["Today", "Yesterday", "Custom"].index(
                    st.session_state.date_filter_type
                ),
                key="date_filter_type"
            )

        if st.session_state.date_filter_type == "Custom":
            with col2:
                start_date, end_date = st.date_input(
                    "Select Date Range",
                    value=(
                        st.session_state.custom_start_date,
                        st.session_state.custom_end_date,
                    ),
                )
                st.session_state.custom_start_date = start_date
                st.session_state.custom_end_date = end_date
    except:
        pass

with tab3:
    @st.fragment(run_every="1m")
    def show_nse_insights():
        today_dt=date.today()
        if st.session_state.date_filter_type == "Today":
            start_date=end_date = today_dt
        elif st.session_state.date_filter_type == "Yesterday":
            start_date=end_date = today_dt - timedelta(days=1)
        else:
            start_date =st.session_state.custom_start_date
            end_date=st.session_state.custom_end_date
        
        today_insights=ann_service.list_announcements_for_given_date(start_date,end_date)
        df=pd.DataFrame(today_insights)
        st.dataframe(df)
    render_filters()
    show_nse_insights()



    
    



    
    


