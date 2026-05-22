import httpx
import duckdb
import json
from dotenv import load_dotenv
import os
from datetime import date

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def already_fetched_today(con) -> bool:
    result = con.execute("""
        SELECT count(*) FROM raw_repositories
        WHERE fetched_date = ?
    """, [date.today()]).fetchone()
    return result[0] > 0

def fetch_trending(language: str = "", keyword: str = "") -> list:
    query = "stars:>500"
    if language:
        query += f" language:{language}"
    if keyword:
        query += f" {keyword} in:name,description"

    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 30
    }

    response = httpx.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()["items"]

def save_to_duckdb(repos: list):
    con = duckdb.connect("github_trends.duckdb")

    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_repositories (
            id INTEGER,
            name VARCHAR,
            full_name VARCHAR,
            description VARCHAR,
            language VARCHAR,
            stargazers_count INTEGER,
            forks_count INTEGER,
            html_url VARCHAR,
            fetched_date DATE
        )
    """)

    today = date.today()
    for repo in repos:
        existing = con.execute(
            "SELECT id FROM raw_repositories WHERE id = ? AND fetched_date = ?",
            [repo["id"], today]
        ).fetchone()

        if not existing:
            con.execute("""
                INSERT INTO raw_repositories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                repo["id"],
                repo["name"],
                repo["full_name"],
                repo.get("description", ""),
                repo.get("language", ""),
                repo["stargazers_count"],
                repo["forks_count"],
                repo["html_url"],
                today
            ])

    con.close()
    print(f"Saved {len(repos)} repositories")

if __name__ == "__main__":
    con = duckdb.connect("github_trends.duckdb")

    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_repositories (
            id INTEGER,
            name VARCHAR,
            full_name VARCHAR,
            description VARCHAR,
            language VARCHAR,
            stargazers_count INTEGER,
            forks_count INTEGER,
            html_url VARCHAR,
            fetched_date DATE
        )
    """)

    if already_fetched_today(con):
        print("今日はすでにデータ取得済みです")
        con.close()
        exit()

    con.close()

    with open("keywords.json", "r") as f:
        keywords = json.load(f)

    languages = keywords.get("languages", [])
    techs = keywords.get("techs", [])

    all_repos = []

    for lang in languages:
        print(f"Fetching: language={lang}")
        repos = fetch_trending(language=lang)
        all_repos.extend(repos)

    for tech in techs:
        print(f"Fetching: keyword={tech}")
        repos = fetch_trending(keyword=tech)
        all_repos.extend(repos)

    unique_repos = list({r["id"]: r for r in all_repos}.values())
    print(f"Total after dedup: {len(unique_repos)}")

    save_to_duckdb(unique_repos)
