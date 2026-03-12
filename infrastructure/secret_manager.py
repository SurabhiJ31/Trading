import os

def get_secret(key, default=None):
    # 1. Try environment variables (Azure)
    value = os.environ.get(key)
    if value:
        return value

    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return default