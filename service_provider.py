# service_provider.py
import streamlit as st
from data_service.companies_service import CompaniesService

@st.cache_resource
def get_companies_service() -> CompaniesService:
    companies_service = CompaniesService()
    return companies_service
