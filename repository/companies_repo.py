from infrastructure.supabase_client import SupabaseClient
from global_logging import logger


class CompaniesRepository:

    def __init__(self):
        self.client = SupabaseClient.get_client()

    def get_all(self):
        try:
             response = self.client.table("stocks").select("symbol","industry","company").execute()
             return response.data
        except Exception as e:
            logger.error(e)




   
