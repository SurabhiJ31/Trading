
from datetime import datetime, timedelta

from repository.stock_info_repo import StockInfoRepository
from global_logging import logger


class StockInfoService:

    def __init__(self):
        self.repo = StockInfoRepository()

    def get_previous_records(self, pastDaysCount,stock_id):
        try:
            cutoff = datetime.today().date() - timedelta(days=pastDaysCount)
            return self.repo.get_limited_time_records(str(cutoff),stock_id)
        except Exception as e:
            logger.error(e)


    def add_daily_records(self,records):
        try:
           return self.repo.add_daily_records(records)
        except Exception as e:
            logger.error(e)

    def does_daily_metrics_exist(self,stock_id,trade_date):
        rec=self.repo.get_daily_metrics(stock_id,trade_date)
        if rec.data:
            return True
        return False
    
    def get_combined_daily_metrics(self,trade_date):
        return self.repo.get_daily_metrics_for_all(trade_date)
    
    
    def add_daily_metrics(self,records):
        try:
           return self.repo.add_daily_metrics(records)
        except Exception as e:
            logger.error(e)

    
    
