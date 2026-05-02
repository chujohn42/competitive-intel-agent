import re
import sys
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.news_agent import fetch_news
from agents.jobs_agent import fetch_jobs
from agents.synthesis_agent import synthesize

st.set_page_config(
    page_title="Competitive Intel Agent",
    layout="wide",
    page_icon="🔍",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* Dark navy sidebar */
[data-testid="stSidebar"] {
    background-color: #0d1b2a !important;
}
[data-testid="stSidebar"] > div {
    background-color: #0d1b2a;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] .stCaption {
    color: #c9d6df !important;
}
[data-testid="stSidebar"] input {
    background-color: #1a2d42 !important;
    color: #e8edf2 !important;
    border: 1px solid #2a4a6a !important;
    border-radius: 4px !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1a3a5c;
}

/* Sidebar buttons (previously analyzed) */
[data-testid="stSidebar"] .stButton > button {
    background-color: #162d45 !important;
    color: #c9d6df !important;
    border: 1px solid #1e3d5c !important;
    border-radius: 4px !important;
    text-align: left !important;
    width: 100% !important;
    font-size: 0.78rem !important;
    padding: 0.4rem 0.75rem !important;
    margin: 0.1rem 0 !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: background 0.15s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #1a5f8a !important;
    border-color: #3a8abf !important;
    color: #ffffff !important;
}

/* Main area */
.main .block-container {
    background-color: #ffffff;
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
}

/* Page title */
.page-title {
    font-size: 2rem;
    font-weight: 700;
    color: #0d1b2a;
    margin-bottom: 0.25rem;
}

/* Subtitle */
.subtitle {
    font-size: 0.95rem;
    color: #6b7280;
    margin-bottom: 1.5rem;
}

/* Recommendation callout box */
.callout-box {
    background: linear-gradient(135deg, #e8f4f8 0%, #daeef7 100%);
    border-left: 5px solid #1a5f8a;
    border-radius: 6px;
    padding: 1.5rem 2rem;
    color: #0d1b2a;
    line-height: 1.8;
    margin: 1rem 0;
    font-size: 0.97rem;
}

/* Bullet cards */
.bullet-list {
    list-style: none;
    padding: 0;
    margin: 0;
}
.bullet-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    margin: 0.4rem 0;
    background: #f8fafc;
    border-radius: 6px;
    border-left: 3px solid #1a5f8a;
    color: #1f2937;
    line-height: 1.6;
    font-size: 0.95rem;
}
.bullet-list li::before {
    content: "▸";
    color: #1a5f8a;
    font-size: 0.85rem;
    margin-top: 0.15rem;
    flex-shrink: 0;
}
</style>
""", unsafe_allow_html=True)

BRIEFS_DIR = Path("outputs/briefs")


# ── Helpers ───────────────────────────────────────────────────────────────────

def list_briefs() -> list[Path]:
    if not BRIEFS_DIR.exists():
        return []
    return sorted(BRIEFS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)


def _split_sections(brief: str) -> dict[str, str]:
    """Split brief into {header_line: body_text} by '## ' boundaries."""
    sections: dict[str, str] = {}
    current_header: str | None = None
    current_lines: list[str] = []
    for line in brief.splitlines():
        if line.startswith("## "):
            if current_header is not None:
                sections[current_header] = "\n".join(current_lines).strip()
            current_header = line
            current_lines = []
        elif current_header is not None:
            current_lines.append(line)
    if current_header is not None:
        sections[current_header] = "\n".join(current_lines).strip()
    return sections


def _find_section_by_keyword(brief: str, keyword: str) -> str:
    """Return body of the first section whose header contains keyword (case-insensitive)."""
    for header, body in _split_sections(brief).items():
        if keyword.lower() in header.lower():
            return body
    return ""


def _extract_bullets(text: str) -> list[str]:
    """Return bullet content lines with ** markers stripped."""
    bullets = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            content = stripped[2:].strip()
            content = re.sub(r"\*\*(.*?)\*\*", r"\1", content)
            bullets.append(content)
    return bullets


def render_bullets(section_text: str):
    bullets = _extract_bullets(section_text)
    if bullets:
        html = "<ul class='bullet-list'>" + "".join(f"<li>{item}</li>" for item in bullets) + "</ul>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        # No bullets found — show raw section text with bold stripped
        st.markdown(re.sub(r"\*\*(.*?)\*\*", r"\1", section_text))


def render_callout(text: str):
    if not text:
        st.info("No recommendation found in this brief.")
        return
    safe = text.replace("\n\n", "<br><br>").replace("\n", "<br>")
    safe = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe)
    st.markdown(f'<div class="callout-box">{safe}</div>', unsafe_allow_html=True)


def display_brief(brief: str, company: str, ts: str):
    st.markdown(
        f'<p class="subtitle">Analysis for <strong>{company}</strong>'
        f'&nbsp;·&nbsp;{ts}</p>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Strategic Moves", "Risks", "Recommendation", "Hiring Signals"]
    )

    with tab1:
        st.markdown(brief)

    with tab2:
        render_bullets(_find_section_by_keyword(brief, "Strategic Moves"))

    with tab3:
        render_bullets(_find_section_by_keyword(brief, "Risks"))

    with tab4:
        render_callout(_find_section_by_keyword(brief, "Recommendation"))

    with tab5:
        render_bullets(_find_section_by_keyword(brief, "Hiring Signals"))

    st.download_button(
        label="Download Brief (.md)",
        data=brief,
        file_name=f"{company.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown",
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Competitive Intel")
    st.markdown("---")

    company_input = st.text_input("Company name", value="Salesforce")
    st.markdown("")
    run_clicked = st.button("Run Agent", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("**Previously analyzed**")

    briefs = list_briefs()
    if briefs:
        for bp in briefs:
            if st.button(bp.stem, key=f"brief_{bp.stem}"):
                parts = bp.stem.split("_", 1)
                st.session_state.update(
                    brief_text=bp.read_text(encoding="utf-8"),
                    brief_company=parts[0],
                    brief_ts=parts[1] if len(parts) > 1 else bp.stem,
                )
    else:
        st.caption("No briefs yet.")

# ── Main panel ────────────────────────────────────────────────────────────────

st.markdown('<h1 class="page-title">Competitive Intelligence Agent</h1>', unsafe_allow_html=True)

if run_clicked and company_input:
    with st.status("Running intelligence gathering...", expanded=True) as status:
        status.update(label="Fetching news...")
        news_data = fetch_news(company_input)

        status.update(label="Analyzing job postings...")
        jobs_data = fetch_jobs(company_input)

        status.update(label="Synthesizing brief with Claude...")
        brief_text = synthesize(news_data, jobs_data)

        status.update(label="Brief ready.", state="complete", expanded=False)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.session_state.update(
        brief_text=brief_text,
        brief_company=company_input,
        brief_ts=ts,
    )
    st.rerun()

elif st.session_state.get("brief_text"):
    display_brief(
        st.session_state["brief_text"],
        st.session_state.get("brief_company", "Unknown"),
        st.session_state.get("brief_ts", ""),
    )

else:
    st.markdown(
        '<p class="subtitle">Enter a company name in the sidebar and click'
        " <strong>Run Agent</strong> to generate a strategic brief.</p>",
        unsafe_allow_html=True,
    )
    st.info("Briefs are automatically saved to `outputs/briefs/` and can be reloaded from the sidebar.")
