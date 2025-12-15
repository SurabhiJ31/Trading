import nsefin
import streamlit as st

@st.cache_data
def get_fno_list():
    nse = nsefin.NSEClient()
    fno_stocks = nse.get_fno_list()
    return list(fno_stocks['symbol'])


def has_fno(company):
    return company in get_fno_list()