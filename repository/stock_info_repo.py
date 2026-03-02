from infrastructure.supabase_client import SupabaseClient
from global_logging import logger


class StockInfoRepository:

    def __init__(self):
        self.client = SupabaseClient.get_client()


    def get_limited_time_records(self,cutoff_date,stock_id):
        try:
            response = self.client.table("daily_prices").select("stock_id,trade_date,close").eq("stock_id", stock_id).gte("trade_date", cutoff_date).order("trade_date").limit(100000).execute()
            return response.data
        except Exception as e:
            logger.error(e)
    
    

    def add_daily_records(self,records):
        try:
             self.client.table("daily_prices").upsert(records,on_conflict="stock_id,trade_date").execute()
             return True
        except Exception as e:
            logger.error(e)
            return False
        
    def get_daily_metrics(self,stock_id,trade_date):
        try:
            response=self.client.table("daily_metrics").select("stock_id").eq("stock_id", stock_id).eq("trade_date", trade_date).execute()
            
            return response
        except Exception as e:
            logger.error(e)

    def get_daily_metrics_for_all(self,trade_date):
        try:
            response=self.client.table("stock_latest_metrics").select("stock_id,symbol,industry,current_price,ma_14,ma_30,ma_60,pct_change_14,pct_change_30,pct_change_60,rsi_14,rsi_30,rsi_60").eq("trade_date", trade_date).execute()
            
            return response
        except Exception as e:
            logger.error(e)

    def add_daily_metrics(self, records):
        try:
            self.client.table("daily_metrics").insert(records).execute()
            return True
        except Exception as e:
            logger.error(e)
            return False
