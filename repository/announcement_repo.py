from infrastructure.supabase_client import SupabaseClient
from global_logging import logger


class AnnouncementRepository:

    def __init__(self):
        self.client = SupabaseClient.get_client()

    def get_all(self):
        try:
             response = self.client.table("nse_announcement_insights").select("*").execute()
             return response.data
        except Exception as e:
            logger.error(e)

    def get_for_date(self, start_date, end_date):
        try:
            response = self.client.table("nse_announcement_insights").select("*").gte("Date",start_date).lte("Date",end_date).execute()
            return response.data
        except Exception as e:
            logger.error(e)

    def get_latest_announcement_time(self):
        try:
            response = self.client.table("nse_announcement_insights").select("Published_Time").order("Published_Time",desc=True).limit(1).maybe_single().execute()
            if response is None:
                return None
            return response.data
        except Exception as e:
            logger.error(e)


    def create(self, announcem_insight: dict):
        try:
            response = self.client.table("nse_announcement_insights").insert(announcem_insight).execute()
            return response.data
        except Exception as e:
            logger.error(e)
