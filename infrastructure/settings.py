import os
import streamlit as st
from dotenv import load_dotenv


class Settings:
    def __init__(self):
        if "SUPABASE_URL" in st.secrets:
            self.SUPABASE_URL = st.secrets["SUPABASE_URL"]
            self.SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
            self.ENV = st.secrets.get("ENV", "prod")
        else:
            env = os.getenv("ENV", "dev")

            if env == "prod":
                load_dotenv("conf.env.prod")
            else:
                load_dotenv("conf.env.dev")

            self.SUPABASE_URL = os.getenv("SUPABASE_URL")
            self.SUPABASE_KEY = os.getenv("SUPABASE_KEY")
            self.ENV = os.getenv("ENV", "dev")
