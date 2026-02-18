from infrastructure.supabase_client import SupabaseClient
from global_logging import logger


class DummyRepository:

    def __init__(self):
        self.client = SupabaseClient.get_client()

    def get_all(self):
        try:
             response = self.client.table("test_table").select("*").execute()
             return response.data
        except Exception as e:
            logger.error(e)

    def create(self, user_data: dict):
        try:
            response = self.client.table("users").insert(user_data).execute()
            return response.data
        except Exception as e:
            pass
