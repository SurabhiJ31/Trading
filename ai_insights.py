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
        #render_batch_insights()
        st.write("Disabled for now to avoid rate limit. buy me a coffee to enable this")


@st.cache_data(show_spinner=False)
def fetch_company_news(
    query: str,
    from_date: datetime,
    to_date: datetime,
    language: str = "en",
) -> List[Dict[str, Any]]:
    """Fetch company news via NewsAPI (needs NEWSAPI_KEY)."""
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
        "Your goal is to assign a market sentiment score using the provided news articles."
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


def render_batch_insights() -> None:

    
    if not selected_companies:
        st.info("No F&O companies available for batch analysis.")
        return

    total = len(selected_companies)
    page_size = st.selectbox(
        "Companies per page",
        options=[2,10, 25, 50, 100],
        index=1 if total >= 50 else 0,
        key="insights_batch_page_size",
    )

    total_pages = max(1, (total + page_size - 1) // page_size)
    if "insights_batch_page" not in st.session_state:
        st.session_state["insights_batch_page"] = 1

    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("◀ Previous"):
            st.session_state["insights_batch_page"] = max(
                1, st.session_state["insights_batch_page"] - 1
            )
    with col_next:
        if st.button("Next ▶"):
            st.session_state["insights_batch_page"] = min(
                total_pages, st.session_state["insights_batch_page"] + 1
            )
    with col_info:
        st.markdown(
            f"<div style='text-align:center;'>Page {st.session_state['insights_batch_page']} of {total_pages}</div>",
            unsafe_allow_html=True,
        )

    page = st.session_state["insights_batch_page"]

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)
    companies_to_analyze = selected_companies[start_idx:end_idx]

    st.caption(f"Showing companies {start_idx + 1}–{end_idx} of {total}.")

    lookback_days = 10
    proceed = st.button("Run batch sentiment analysis", key="sentiment_batch")

    # Prepare meta to detect when we need to recompute
    current_meta = {
        "anchor_date": str(datetime.now().date()),
        "lookback_days": lookback_days,
        "page_size": page_size,
        "companies": tuple(selected_companies),
    }

    # Initialize cache structure
    cache = st.session_state.get("insights_batch_cache", {"meta": None, "rows": {}})
    cached_meta = cache.get("meta")

    # If user hit Run or inputs changed, reset cache meta (rows kept but considered stale)
    if proceed or cached_meta != current_meta:
        cache = {"meta": current_meta, "rows": {}}

    # Fetch only for companies on the current page that are missing in cache
    missing = [c for c in companies_to_analyze if c not in cache["rows"]]
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

    page_rows = [cache["rows"][c] for c in companies_to_analyze if c in cache["rows"]]
    if not page_rows:
        st.info("No insights for this page. Run batch or check data availability.")
        return

    df_page = pd.DataFrame(page_rows)
    st.dataframe(
            df_page.sort_values("Sentiment Score (0-1)", ascending=False)
        )
        