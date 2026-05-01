import re
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = (
    "You are a strategy consultant. Given news and job-posting data about a company, "
    "produce a structured competitive brief with:\n"
    "1. Top 3 strategic moves or signals observed\n"
    "2. Key risks or challenges facing the company\n"
    "3. One strategic recommendation for a competitor or investor\n"
    "4. Hiring Signals: what the company's current hiring patterns reveal about "
    "their near-term strategic priorities\n"
    "Keep it concise and executive-ready."
)

_STRATEGY_TERMS = [
    "acquisition", "merger", "partnership", "deal", "launch",
    "expand", "invest", "revenue", "earnings", "strategy",
    "ceo", "executive", "market", "product", "service",
    "growth", "layoff", "hire", "restructur", "quarter",
    "forecast", "guidance", "competitor", "industry",
]


def _is_relevant(headline: str, summary: str, company: str) -> bool:
    text = (headline + " " + summary).lower()
    if company.lower() in text:
        return True
    return any(term in text for term in _STRATEGY_TERMS)


def synthesize(news_data: dict, jobs_data: dict | None = None) -> str:
    company = news_data["company"]
    headlines = news_data.get("headlines", [])
    summaries = news_data.get("summaries", [])
    date_collected = news_data.get(
        "date_collected", datetime.now(timezone.utc).isoformat()
    )

    relevant = [
        {"headline": h, "summary": s}
        for h, s in zip(headlines, summaries)
        if _is_relevant(h, s, company)
    ]

    # Fall back to all articles if nothing passes the filter
    if not relevant:
        relevant = [
            {"headline": h, "summary": s} for h, s in zip(headlines, summaries)
        ]

    articles_text = "\n\n".join(
        f"Headline: {a['headline']}\nSummary: {a['summary']}" for a in relevant
    )
    user_message = f"Company: {company}\n\nRecent news:\n\n{articles_text}"

    if jobs_data:
        total = jobs_data.get("total_jobs_found", 0)
        hiring_areas = jobs_data.get("top_hiring_areas", [])
        signals = jobs_data.get("strategic_signals", [])
        raw_titles = jobs_data.get("raw_titles", [])

        areas_text = "\n".join(
            f"  - {a['category']}: {a['count']} role(s)" for a in hiring_areas
        )
        signals_text = (
            "\n".join(f"  - {s}" for s in signals) if signals else "  - No strong signals detected"
        )
        sample_titles = raw_titles[:15]
        titles_text = "\n".join(f"  - {t}" for t in sample_titles)

        user_message += (
            f"\n\n--- HIRING DATA ({total} open roles found) ---"
            f"\n\nTop hiring areas:\n{areas_text}"
            f"\n\nInferred strategic signals from hiring:\n{signals_text}"
            f"\n\nSample job titles:\n{titles_text}"
        )

    client = anthropic.Anthropic()

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        final = stream.get_final_message()

    brief = next(
        (block.text for block in final.content if block.type == "text"), ""
    )

    date_str = date_collected[:10]
    safe_company = re.sub(r"[^\w]", "_", company)
    output_dir = Path(__file__).parent.parent / "outputs" / "briefs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_company}_{date_str}.md"
    output_path.write_text(brief, encoding="utf-8")

    return brief
