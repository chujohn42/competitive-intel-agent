import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWSAPI_URL = "https://newsapi.org/v2/everything"


def fetch_news(company: str) -> dict:
    if not NEWSAPI_KEY:
        raise ValueError("NEWSAPI_KEY not found in environment")

    params = {
        "q": company,
        "sortBy": "publishedAt",
        "pageSize": 10,
        "language": "en",
        "apiKey": NEWSAPI_KEY,
    }

    response = requests.get(NEWSAPI_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    articles = data.get("articles", [])

    headlines = []
    summaries = []
    sources = []

    for article in articles:
        headlines.append(article.get("title") or "")
        summaries.append(article.get("description") or "")
        source_name = (article.get("source") or {}).get("name") or ""
        if source_name and source_name not in sources:
            sources.append(source_name)

    return {
        "company": company,
        "source": sources,
        "headlines": headlines,
        "summaries": summaries,
        "date_collected": datetime.now(timezone.utc).isoformat(),
    }
