from datetime import datetime, timedelta
from repository.announcement_repo import AnnouncementRepository
from global_logging import logger


class AnnouncementService:

    def __init__(self):
        self.repo = AnnouncementRepository()

    def list_announcements(self):
        try:
            return self.repo.get_all()
        except Exception as e:
            logger.error(e)

    def list_announcements_for_given_date(self,start_date, end_date):
        try:
            return self.repo.get_for_date(str(start_date), str(end_date))
        except Exception as e:
            logger.error(e)

    def save_insight(self, announcem_insight: dict):
        if announcem_insight is None:
            return None

        try:
            return self.repo.create(announcem_insight)
        except Exception as e:
            logger.error(e)

    def get_latest_nse_announcement_time(self):
        try:
           latest_time = self.repo.get_latest_announcement_time()
           if latest_time is None:
               latest_time = datetime.now()-timedelta(hours=3)
           return latest_time
        except Exception as e:
            logger.error(e)
