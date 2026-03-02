
from typing import Dict
import re
from repository.companies_repo import CompaniesRepository
from global_logging import logger


class CompaniesService:

    def __init__(self):
        self.repo = CompaniesRepository()
        self._stocks: Dict[str, Dict] = None

    def get_all_stocks(self):
        try:
            if self._stocks is None:
                stock_records=self.repo.get_all("symbol,industry,company")
                self._stocks = {
                row["symbol"]: {
                    "company": row["company"],
                    "industry": row["industry"]
                }
                for row in stock_records
            }
            return self._stocks
        except Exception as e:
            logger.error(e)

    def get_stocks_with_ids(self):
        try:
            company_with_ids= self.repo.get_all("id,symbol")
            updated_data= {row["symbol"]: row["id"] for row in company_with_ids}
            return updated_data
        except Exception as e:
            logger.error(msg="Error while parsing",args=e)

    def get_company_symbols(self):
        stocks=self.get_all_stocks()
        return stocks.keys()
    
    def get_industry(self,company):
        stocks=self.get_all_stocks()
        return stocks[company]['industry']
    
    def get_company_name(self,company):
        stocks=self.get_all_stocks()
        return stocks[company]['company']
    
    def normalize_name(self,name: str) -> str:
        name = name.lower()
        name = re.sub(r'\b(limited|ltd)\b', '', name)
        name = re.sub(r'[^a-z0-9 ]', '', name)
        name = re.sub(r'\s+', ' ', name)
        return name.strip()

    
