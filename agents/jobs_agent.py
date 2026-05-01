import re
from datetime import datetime, timezone
from urllib.parse import quote

import requests

HN_URL = (
    "https://hn.algolia.com/api/v1/search"
    "?query={query}&tags=ask_hn_who_is_hiring&hitsPerPage=20"
)
REMOTEOK_URL = "https://remoteok.com/api?tag={query}"

_CATEGORIES: dict[str, list[str]] = {
    "AI / Machine Learning": [
        "ai ", "artificial intelligence", "machine learning", "ml engineer",
        "data science", "data scientist", "nlp", "deep learning", "llm",
        "computer vision", "generative", "prompt engineer", "ai engineer",
    ],
    "Software Engineering": [
        "software engineer", "software developer", "backend", "frontend",
        "full stack", "fullstack", "sre", "devops", "platform engineer",
        "infrastructure", "cloud engineer", "mobile engineer", "ios", "android",
    ],
    "Data & Analytics": [
        "data analyst", "analytics engineer", "business intelligence", "bi analyst",
        "data engineer", "etl", "tableau", "looker",
    ],
    "Sales & Business Development": [
        "sales", "account executive", "account manager", "business development",
        "revenue", "bdr", "sdr", "inside sales", "field sales",
    ],
    "Marketing": [
        "marketing", "brand manager", "growth marketing", "seo", "content strategist",
        "demand generation", "product marketing", "communications manager",
    ],
    "Product Management": [
        "product manager", "product owner", "product lead", "head of product",
    ],
    "M&A / Corporate Finance": [
        "m&a", "mergers", "acquisition", "corporate development",
        "investment analyst", "financial analyst", "treasury", "accounting",
    ],
    "Security & Trust": [
        "security engineer", "cybersecurity", "infosec", "soc analyst",
        "penetration", "compliance", "risk analyst", "privacy engineer",
    ],
    "Customer Success & Support": [
        "customer success", "customer support", "customer service",
        "technical support", "solutions engineer", "implementation",
    ],
    "People & HR": [
        "recruiter", "recruiting", "human resources", "people operations",
        "talent acquisition", "hrbp",
    ],
    "Operations": [
        "operations manager", "supply chain", "logistics", "program manager",
        "project manager",
    ],
}

# (category, min_count_threshold, signal_text)
_SIGNAL_RULES: list[tuple[str, int, str]] = [
    ("AI / Machine Learning",        3, "Heavy AI/ML investment — building or scaling intelligent product capabilities"),
    ("Software Engineering",         5, "Significant platform build-out — product or infrastructure expansion underway"),
    ("Sales & Business Development", 4, "Aggressive go-to-market push — growth and market-expansion mode"),
    ("M&A / Corporate Finance",      2, "Elevated M&A or corporate-finance activity — deal-making or fundraising likely"),
    ("Security & Trust",             3, "Heightened security posture investment — regulatory or incident-driven"),
    ("Data & Analytics",             3, "Building data infrastructure or analytical capabilities"),
    ("Customer Success & Support",   4, "Customer retention and expansion focus — defending existing base"),
    ("Marketing",                    3, "Demand-generation or brand investment — market-share push"),
    ("Product Management",           3, "Product-led growth or new product lines in development"),
]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def _categorize(title: str) -> str | None:
    t = title.lower()
    for category, keywords in _CATEGORIES.items():
        if any(kw in t for kw in keywords):
            return category
    return None


def _fetch_hn_titles(company: str) -> list[str]:
    url = HN_URL.format(query=quote(company))
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    titles = []
    for hit in resp.json().get("hits", []):
        title = (hit.get("title") or "").strip()
        story_text = _strip_html(hit.get("story_text") or "")
        if title:
            titles.append(title)
        elif story_text:
            # Use the first non-empty line of the post body as a fallback title
            first_line = next((l.strip() for l in story_text.splitlines() if l.strip()), "")
            if first_line:
                titles.append(first_line[:120])
    return titles


def _fetch_remoteok_titles(company: str) -> list[str]:
    url = REMOTEOK_URL.format(query=quote(company))
    headers = {"User-Agent": "competitive-intel-agent/1.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    titles = []
    for item in resp.json():
        if not isinstance(item, dict):
            continue
        position = (item.get("position") or "").strip()
        if position:
            titles.append(position)
    return titles


def fetch_jobs(company: str) -> dict:
    raw_titles: list[str] = []

    for fetcher in (_fetch_hn_titles, _fetch_remoteok_titles):
        try:
            raw_titles.extend(fetcher(company))
        except Exception:
            pass  # one source failing should not break the other

    category_counts: dict[str, int] = {}
    for title in raw_titles:
        cat = _categorize(title)
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1

    top_hiring_areas = sorted(
        [{"category": k, "count": v} for k, v in category_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    strategic_signals = [
        signal
        for category, threshold, signal in _SIGNAL_RULES
        if category_counts.get(category, 0) >= threshold
    ]

    return {
        "company": company,
        "total_jobs_found": len(raw_titles),
        "top_hiring_areas": top_hiring_areas,
        "strategic_signals": strategic_signals,
        "raw_titles": raw_titles,
        "date_collected": datetime.now(timezone.utc).isoformat(),
    }
