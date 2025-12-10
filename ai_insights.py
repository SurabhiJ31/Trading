from datetime import datetime, timedelta
import json
from typing import List,Dict,Any
import os
from openai import OpenAI
import requests
import streamlit as st
from companies import get_nifty50_companies

companies = get_nifty50_companies()
def get_insights():
    company_name =ticker = st.selectbox("Stock",companies)
    lookback_days = st.slider("Days to analyze", min_value=0, max_value=100, value=10)
    proceed = st.button("Get sentiment score", key="sentiment")
    if proceed:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        articles = fetch_company_news(company_name or ticker, start_date, end_date)
        if not articles:
            st.warning(
                "No news articles were fetched. Provide a NEWSAPI_KEY env var for richer context."
            )
        else:
            analysis = generate_market_analysis(ticker, company_name, articles)

            if "error" in analysis:
                st.error(analysis["error"])
            else:
                insights = analysis.get("insights", [])
                render_market_insights(insights)


@st.cache_data(show_spinner=False)
def fetch_company_news(
    query: str,
    from_date: datetime,
    to_date: datetime,
    language: str = "en",
) -> List[Dict[str, Any]]:
    """Fetch company news via NewsAPI (needs NEWSAPI_KEY)."""
    api_key = os.getenv("NEWSAPI_KEY")
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
    
@st.cache_resource(show_spinner=False)
def get_openai_client() -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
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