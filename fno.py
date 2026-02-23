import nsefin
import streamlit as st
from service_provider import get_companies_service

comp_service=get_companies_service()

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
    all_companies = comp_service.get_company_symbols()
    res = list(set(all_fno_list) & set(all_companies))
    return res

@st.cache_data
def get_fno_companies_normalised():
    fno_normalised={}
    for cmp in get_companies_with_fno():
        fno_normalised[comp_service.normalize_name(comp_service.get_company_name(cmp))]=cmp
    return fno_normalised
