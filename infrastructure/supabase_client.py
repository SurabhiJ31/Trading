from supabase import create_client, Client
from infrastructure.settings import Settings
import streamlit as st


class SupabaseClient:
    _instance: Client = None

    @classmethod
    @st.cache_resource
    def get_client(cls) -> Client:
        if cls._instance is None:
            settings = Settings()
            cls._instance = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return cls._instance
