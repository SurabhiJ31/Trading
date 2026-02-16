from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import feedparser
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from companies import normalize_name
from fno import get_fno_companies_normalised
from ai_insights import get_insight_for_nse_announcement
from pdf_extractor import gdf
from collections import defaultdict
import threading
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to INFO in production
    format='%(asctime)s [%(levelname)s] %(message)s',
)

logger = logging.getLogger(__name__)

RSS_URL = "https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml"

HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
date_format = '%d-%b-%Y %H:%M:%S'
recent_datetime = datetime.now()-timedelta(hours=3)
lock = threading.Lock()

ags=[]

announcement_list=[]
nse_announcements_insights=defaultdict(list)

def get_nse_session():
    session = requests.Session()

    # Retry strategy
    retry_strategy = Retry(
        total=3,                     # Retry up to 5 times
        backoff_factor=1,            # 1s, 2s, 4s, 8s...
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    # Important headers (NSE blocks default python agent)
    session.headers.update(HEADERS)

    return session


def fetch_nse_corporate_announcements():
    try:
        session=get_nse_session()
        response=session.get(RSS_URL,timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        return feed.entries
    except requests.exceptions.RequestException as e:
        #TODO: Log error
        return None

def parse_announcements(feed_entries):
    if feed_entries is None:
        return None
    
    try:
        global recent_datetime
        latest_feed_date = datetime.strptime(feed_entries[0].get('published'), date_format)
        new_fno_announcements=[] 
        for entry in feed_entries:
            try:
                feed_date=datetime.strptime(entry.get('published'), date_format)
                if feed_date > recent_datetime :
                    announcement_list.append({
                        "title": entry.title,
                        "link": entry.get('link'),
                        "published": feed_date,
                        "summary": entry.summary
                    })

                    norm_title=normalize_name(entry.title)
                    #logger.info(f"nse announcement fetched for {norm_title}")
                    companies_norm=get_fno_companies_normalised()
                    if norm_title in companies_norm.keys():

                        new_fno_announcements.append({
                        "Symbol":companies_norm[norm_title],
                        "title": norm_title,
                        "link": entry.get('link'),
                        "summary": entry.summary,
                        "published":entry.get('published')
                        })
                else:
                    break
            except:
                pass
        recent_datetime=latest_feed_date
        return new_fno_announcements
    except:
        #TODO: Log error
        return None




def get_extracted_pdfs(new_fno_announcements):
    updated_announcements=[]

    if new_fno_announcements is None:
        return None

    try:

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {
                executor.submit(get_extracted_pdf, fno_announcement)
                for fno_announcement in new_fno_announcements
            }

            for future in as_completed(future_to_url):
                updated_announcements.append(future.result())
    except:
        pass

    return updated_announcements

def get_extracted_pdf(new_fno_announcement):
    text = gdf(new_fno_announcement["link"])
    new_fno_announcement["pdf_text"]=text
    return new_fno_announcement

def update_nse_announcement_insights():
    feed=fetch_nse_corporate_announcements()
    new_fno_announcements = parse_announcements(feed)
    announcements_with_extracted_pdf=get_extracted_pdfs(new_fno_announcements)

    with lock:

        for announcement in announcements_with_extracted_pdf:
            insight = get_insight_for_nse_announcement(announcement)
            if insight is not None:
                dt_object = datetime.strptime(insight.get('Published_Date'), date_format)
                only_date = str(dt_object.date())
                nse_announcements_insights[only_date].append(insight)



def get_nse_announcements():
    return nse_announcements_insights


def nse_feed_updater():
    while True:
        logger.info("nse announcement collecter executed")
        update_nse_announcement_insights()
        time.sleep(600) #10 mins


