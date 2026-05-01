# Competitive Intelligence Agent

A multi-agent AI system that autonomously monitors competitor activity across news and job postings, then synthesizes findings into executive-grade strategic briefs using Claude. Point it at any company and it returns a structured brief — strategic moves, key risks, hiring signals, and actionable recommendations — in seconds.

## Architecture

```
News Agent ──→
              Synthesis Agent ──→ Strategic Brief
Jobs Agent ──↗
```

| Agent | Source | Output |
|---|---|---|
| **News Agent** | NewsAPI | Recent headlines + summaries |
| **Jobs Agent** | HN Who's Hiring, RemoteOK | Categorized hiring data + signals |
| **Synthesis Agent** | Anthropic Claude API | Structured competitive brief (Markdown) |

## Sample Output

```
## Strategic Brief: Salesforce — April 2026

**Top 3 Strategic Moves**
1. Commercialize-and-defend: Salesforce is aggressively monetizing its AI layer
   (Agentforce) while fortifying its CRM moat against Microsoft and HubSpot
   encroachment. Recent pricing changes and partner incentives signal a
   land-and-expand play targeting mid-market accounts.
...

**Hiring Signals**
Heavy investment in AI/ML and Software Engineering roles indicates active
platform build-out — Salesforce is shipping, not planning.
```

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-username/competitive-intel-agent.git
   cd competitive-intel-agent
   ```

2. **Add API keys to `.env`**
   ```
   ANTHROPIC_API_KEY=your_key_here
   NEWSAPI_KEY=your_key_here
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run**
   ```bash
   python main.py
   ```

Briefs are saved to `outputs/briefs/` as Markdown files.

## Tech Stack

- **Python 3.11+**
- **Anthropic Claude API** — `claude-opus-4-7` with streaming and prompt caching
- **NewsAPI** — recent news headlines and summaries
- **RemoteOK API** — remote job postings by company/tag
- **HN Algolia API** — Hacker News "Who is Hiring" thread search
