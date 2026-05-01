from agents.jobs_agent import fetch_jobs
from agents.news_agent import fetch_news
from agents.synthesis_agent import synthesize


def main():
    company = "Salesforce"

    print(f"Fetching news for: {company}...")
    news_data = fetch_news(company)
    print(f"  {len(news_data['headlines'])} articles fetched.\n")

    print(f"Fetching job postings for: {company}...")
    jobs_data = fetch_jobs(company)
    print(f"  {jobs_data['total_jobs_found']} job postings found.\n")

    print("Synthesizing competitive brief...\n")
    brief = synthesize(news_data, jobs_data)
    print(brief)


if __name__ == "__main__":
    main()
