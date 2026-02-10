import nsefin
from companies import get_company_symbols, normalize_name, get_company_name
import streamlit as st

@st.cache_data
def get_fno_list():
    nse = nsefin.NSEClient()
    fno_stocks = nse.get_fno_list()
    return list(fno_stocks['symbol'])

#company is symbol
def has_fno(company):
    return company in get_fno_list()

@st.cache_data
def get_companies_with_fno():
    all_fno_list = get_fno_list()
    all_companies = get_company_symbols()
    res = list(set(all_fno_list) & set(all_companies))
    return res

@st.cache_data
def get_fno_companies_normalised():
    fno_normalised={}
    for cmp in get_companies_with_fno():
        fno_normalised[normalize_name(get_company_name(cmp))]=cmp
    return fno_normalised
