from datetime import datetime, timedelta
import json
from typing import List, Dict, Any
import os
from fno import get_companies_with_fno
import pandas as pd
from openai import OpenAI
import requests
import streamlit as st
from companies import get_company_name

selected_companies = get_companies_with_fno()


def get_insights():
    single_tab, batch_tab = st.tabs(["Single stock", "Batch (list)"])

    with single_tab:
        ticker = st.selectbox("Stock", selected_companies, key="insights_single_ticker")
        company_name = get_company_name(ticker)
        lookback_days = st.slider(
            "Days to analyze", min_value=1, max_value=100, value=10, key="insights_single_lookback"
        )
        proceed = st.button("Get sentiment score", key="sentiment_single")
        if proceed:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            articles = fetch_company_news(company_name or ticker, start_date, end_date)
            if not articles:
                st.warning(
                    "No news articles were fetched. Provide a NEWSAPI_KEY secret for richer context."
                )
            else:
                analysis = generate_market_analysis(ticker, company_name, articles)

                if "error" in analysis:
                    st.error(analysis["error"])
                else:
                    insights = analysis.get("insights", [])
                    render_market_insights(insights)

    with batch_tab:
        uploaded_file = st.file_uploader("Upload CSV file",type=["csv"])
        if uploaded_file is not None:
            ip_file = pd.read_csv(uploaded_file)

            if "Stock" not in ip_file.columns:
                st.error("CSV must contain a column named 'Stock'")
            else:
                stock_list = ip_file["Stock"].dropna().astype(str).tolist()
                render_batch_insights(stock_list)
        #st.write("Disabled for now to avoid rate limit. buy me a coffee to enable this")


@st.cache_data(show_spinner=False)
def fetch_company_news(
    query: str,
    from_date: datetime,
    to_date: datetime,
    language: str = "en",
) -> List[Dict[str, Any]]:
    api_key = st.secrets["NEWSAPI_KEY"]
    if not api_key:
        return []
    params = {
        "q": query,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
        "language": language,
        "sortBy": "relevancy",
        "pageSize": 20,
        "apiKey": api_key,
    }
    try:
        response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return []

    payload = response.json()
    articles = payload.get("articles", []) or []
    normalized: List[Dict[str, Any]] = []
    for article in articles:
        normalized.append(
            {
                "title": article.get("title"),
                "url": article.get("url"),
                "publisher": (article.get("source") or {}).get("name"),
                "published_at": article.get("publishedAt"),
                "description": article.get("description"),
            }
        )
    return normalized


def build_market_context(
    ticker: str,
    company_name: str,
    articles: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "ticker": ticker,
        "company_name": company_name,
        "articles": articles,
    }


def generate_announcement_analysis(announcement):
    formatted_context=json.dumps(announcement)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "return_insights",
                "description": "Return confidence score with reasoning",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "insights": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "sentiment_score": {"type": "string"},
                                    "reason": {"type": "string"}
                                },
                                "required": ["sentiment_score", "reason",],
                            },
                        }
                    },
                    "required": ["insights"],
                },
            },
        }
    ]

    system_prompt = (
    "You are a meticulous financial analyst. "
    "You are given a corporate announcement from NSE consisting of a short summary "
    "and detailed disclosure text extracted from an official PDF filing. "
    "You must prioritize factual information from the PDF over the summary. "
    "Ignore boilerplate legal language unless it indicates risk. "
    "Assign a market sentiment score between 0 and 1 "
    "(0 = negative, 0.5 = neutral, 1 = positive). "
    "Explain clearly what factors influenced the score."
)
    config = get_openai_client_with_mohit_key()
    client: OpenAI = config["client"]
    model: str = config["model"]

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Analyse the sentiment for this NSE company based on the announcement. "
                    "Call the return_insights tool with JSON describing the sentiment_score and reason"
                    f"Context:\n{formatted_context}"
                ),
            },
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "return_insights"}},
    )

    tool_call = completion.choices[0].message.tool_calls
    if not tool_call:
        return {"error": "The analysis did not return structured insights."}

    arguments = tool_call[0].function.arguments
    try:
        parsed = json.loads(arguments)
        return parsed
    except json.JSONDecodeError:
        return {"error": "Unable to parse analysis output."}
    



def generate_market_analysis(
    ticker: str,
    company_name: str,
    articles: List[Dict[str, Any]],
) -> Dict[str, Any]:
    
    context = build_market_context(ticker, company_name, articles)
    formatted_context = json.dumps(context)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "return_insights",
                "description": "Return confidence score with reasoning and sources",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "insights": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "sentiment_score": {"type": "string"},
                                    "reason": {"type": "string"},
                                    "sources": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "title": {"type": "string"},
                                                "url": {"type": "string"}
                                            },
                                            "required": ["title", "url"],
                                        },
                                    },
                                },
                                "required": ["sentiment_score", "reason","sources"],
                            },
                        }
                    },
                    "required": ["insights"],
                },
            },
        }
    ]

    system_prompt = (
        "You are a meticulous financial analyst. "
        "Your goal is to assign a market sentiment score using the provided news articles. There will be company related news articles as well as domain related."
        "The score should be on a scale of 0 to 1 where 0.5 means neutral, 1 means positive, 0 means negative."
        "There must be an explanation for arriving at that score."
        "The explanation must cite the relevant sources. "
        "Set score to high only if you have multiple aligned reputable sources."
    )
    config = get_openai_client()
    client: OpenAI = config["client"]
    model: str = config["model"]

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Analyse the market sentiment for this NSE company. "
                    "Call the return_insights tool with JSON describing the sentiment_score, reasons and sources"
                    f"Context:\n{formatted_context}"
                ),
            },
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "return_insights"}},
    )

    tool_call = completion.choices[0].message.tool_calls
    if not tool_call:
        return {"error": "The analysis did not return structured insights."}

    arguments = tool_call[0].function.arguments
    try:
        parsed = json.loads(arguments)
        return parsed
    except json.JSONDecodeError:
        return {"error": "Unable to parse analysis output."}


@st.cache_data(show_spinner=False)
def get_company_sentiment_cached(
    ticker: str,
    company_name: str,
    anchor_date: datetime.date,
    lookback_days: int,
) -> Dict[str, Any]:
    end_date = datetime.combine(anchor_date, datetime.max.time())
    start_date = end_date - timedelta(days=lookback_days)
    articles = fetch_company_news(company_name or ticker, start_date, end_date)
    if not articles:
        return {}

    return generate_market_analysis(ticker, company_name, articles)

#TODO: Update with mohit's api key after testing
@st.cache_resource(show_spinner=False)
def get_openai_client_with_mohit_key() -> Dict[str, Any]:
    api_key = st.secrets["OPENAI_API_KEY"].replace("\n", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required.")

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return {"client": client, "model": model}

@st.cache_resource(show_spinner=False)
def get_openai_client() -> Dict[str, Any]:
    api_key = st.secrets["OPENAI_API_KEY"].replace("\n", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required.")

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return {"client": client, "model": model}


def render_market_insights(insights: List[Dict[str, Any]]) -> None:
    if not insights:
        st.info("No insights were generated for the selected period.")
        return

    for entry in insights:
        sentiment_score = entry.get("sentiment_score", "No score")
        reason = entry.get("reason", "No explanation provided.")
        sources = entry.get("sources", [])

        
        st.write(sentiment_score)
        st.write(reason)

        if sources:
            st.markdown("**Sources**")
            for source in sources:
                title = source.get("title") or source.get("url")
                url = source.get("url")
                if title and url:
                    st.markdown(f"- [{title}]({url}))")
        st.divider()


def render_batch_insights(input_companies) -> None:

    
    if not input_companies:
        st.info("No F&O companies available for batch analysis.")
        return

    
    lookback_days = 10

    # Prepare meta to detect when we need to recompute
    current_meta = {
        "anchor_date": str(datetime.now().date()),
        "lookback_days": lookback_days,
        "companies": tuple(input_companies),
    }

    # Initialize cache structure
    cache = st.session_state.get("insights_batch_cache", {"meta": None, "rows": {}})
    cached_meta = cache.get("meta")

    # If user hit Run or inputs changed, reset cache meta (rows kept but considered stale)
    if cached_meta != current_meta:
        cache = {"meta": current_meta, "rows": {}}

    # Fetch only for companies on the current page that are missing in cache
    missing = [c for c in input_companies if c not in cache["rows"]]
    if missing:
        anchor_date = datetime.now().date()
        with st.spinner("Analyzing sentiment for selected companies..."):
            for ticker in missing:
                company_name = get_company_name(ticker)
                analysis = get_company_sentiment_cached(
                    ticker, company_name, anchor_date, lookback_days
                )
                if "error" in analysis or not analysis:
                    cache["rows"][ticker] = {
                        "Ticker": ticker,
                        "Company": company_name or ticker,
                        "Sentiment Score (0-1)": "N/A",
                        "Reason": "No recent news or analysis available for this period.",
                    }
                    continue

                insights = analysis.get("insights", [])
                if not insights:
                    cache["rows"][ticker] = {
                        "Ticker": ticker,
                        "Company": company_name or ticker,
                        "Sentiment Score (0-1)": "N/A",
                        "Reason": "No insights returned by the analysis.",
                    }
                    continue

                top = insights[0]
                cache["rows"][ticker] = {
                    "Ticker": ticker,
                    "Company": company_name or ticker,
                    "Sentiment Score (0-1)": top.get("sentiment_score"),
                    "Reason": top.get("reason"),
                }
        cache["meta"] = current_meta
        st.session_state["insights_batch_cache"] = cache

    page_rows = [cache["rows"][c] for c in input_companies if c in cache["rows"]]
    if not page_rows:
        st.info("No insights for this page. Run batch or check data availability.")
        return

    df_page = pd.DataFrame(page_rows)
    st.dataframe(
            df_page.sort_values("Sentiment Score (0-1)", ascending=False)
        )
    

def get_insights_for_nse_announcements(announcements) -> None:

    
    if not announcements:
        return
    all_insights=[]
    for announcement in announcements:
        analysis = generate_announcement_analysis(announcement)
        if "error" in analysis or not analysis:
            return
        insights = analysis.get("insights", [])
        if not insights:
            return
        top = insights[0]
        insight = {
            "Symbol":announcement.get("Symbol"),
            "Title":announcement.get("title"),
            "Sentiment Score (0-1)": top.get("sentiment_score"),
            "Reason": top.get("reason"),
            "Link":announcement.get("link"),
            }
        st.toast(insight)
        all_insights.append(insight)
    return all_insights
        