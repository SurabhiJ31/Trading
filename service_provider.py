# service_provider.py
import streamlit as st
from data_service.companies_service import CompaniesService
from data_service.stock_info_service import StockInfoService

@st.cache_resource
def get_companies_service() -> CompaniesService:
    companies_service = CompaniesService()
    return companies_service

@st.cache_resource
def get_stock_info_service() -> StockInfoService:
    stock_info_service = StockInfoService()
    return stock_info_service

