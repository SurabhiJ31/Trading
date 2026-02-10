from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import feedparser
from datetime import datetime
from companies import normalize_name
from fno import get_fno_companies_normalised
from ai_insights import get_insights_for_nse_announcements
from pdf_extractor import gdf
import streamlit as st

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
recent_datetime = datetime.min


announcement_list=[]


def fetch_nse_corporate_announcements():
    response = requests.get(
        RSS_URL,
        headers=HEADERS,
        timeout=10
    )
    response.raise_for_status()

    feed = feedparser.parse(response.content)
    return feed.entries

def parse_announcements(feed_entries):
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
                companies_norm=get_fno_companies_normalised()
                if norm_title in companies_norm.keys():

                    new_fno_announcements.append({
                    "Symbol":companies_norm[norm_title],
                    "title": norm_title,
                    "link": entry.get('link'),
                    "summary": entry.summary
                    })
            else:
                break
        except:
            pass
    recent_datetime=latest_feed_date
    return new_fno_announcements


def abcfd():
    feed=fetch_nse_corporate_announcements()
    new_fno_announcements = parse_announcements(feed)
    announcement_with_extracted_pdf=get_extracted_pdfs(new_fno_announcements[:2])
    insights = get_insights_for_nse_announcements(announcement_with_extracted_pdf)
    return insights

def get_extracted_pdfs(new_fno_announcements):
    updated_announcements=[]

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(get_extracted_pdf, fno_announcement)
            for fno_announcement in new_fno_announcements
        }

        for future in as_completed(future_to_url):
            updated_announcements.append(future.result())

    return updated_announcements

def get_extracted_pdf(new_fno_announcement):
    text = gdf(new_fno_announcement["link"])
    new_fno_announcement["pdf_text"]=text
    return new_fno_announcement