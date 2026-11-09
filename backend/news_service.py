import os
import re
import requests

from dotenv import load_dotenv

from database import get_connection


load_dotenv()


NEWS_API_KEY = os.getenv("NEWS_API_KEY")

BASE_URL = "https://newsapi.org/v2/top-headlines"


def get_top_news(interests=None, category=None):

    params = {
        "country": "us",
        "pageSize": 20,
        "apiKey": NEWS_API_KEY
    }

    # Add NewsAPI category when provided
    if category:
        params["category"] = category

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":

            return {
                "error": data.get(
                    "message",
                    "Failed to fetch news"
                )
            }

        articles = []

        if interests is None:
            interests = []

        interests = [
            interest.lower()
            for interest in interests
        ]

        for article in data.get("articles", []):

            title = article.get("title") or ""

            description = (
                article.get("description") or ""
            )

            text = (
                title + " " + description
            ).lower()

            score = 0

            # Calculate relevance score
            for interest in interests:

                pattern = (
                    r"\b"
                    + re.escape(interest.lower())
                    + r"\b"
                )

                if re.search(pattern, text):

                    score += 1

            cleaned_article = {

                "title": title,

                "description": description,

                "content": article.get("content"),

                "source": article.get(
                    "source", {}
                ).get("name"),

                "url": article.get("url"),

                "image": article.get("urlToImage"),

                "published_at": article.get(
                    "publishedAt"
                ),

                "relevance_score": score

            }

            # Save article to SQLite database
            connection = get_connection()

            connection.execute(
                """
                INSERT INTO news
                (
                    title,
                    description,
                    content,
                    source,
                    url,
                    image,
                    published_at,
                    relevance_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(url) DO UPDATE SET

                    title = excluded.title,

                    description = excluded.description,

                    content = excluded.content,

                    source = excluded.source,

                    image = excluded.image,

                    published_at = excluded.published_at,

                    relevance_score = excluded.relevance_score
                """,
                (
                    cleaned_article["title"],
                    cleaned_article["description"],
                    cleaned_article["content"],
                    cleaned_article["source"],
                    cleaned_article["url"],
                    cleaned_article["image"],
                    cleaned_article["published_at"],
                    cleaned_article["relevance_score"]
                )
            )

            connection.commit()

            connection.close()

            articles.append(cleaned_article)

        # Sort articles by relevance
        articles.sort(
            key=lambda article: article[
                "relevance_score"
            ],
            reverse=True
        )

        return articles

    except requests.exceptions.Timeout:

        return {
            "error": "News API request timed out"
        }

    except requests.exceptions.RequestException as e:

        return {
            "error": str(e)
        }





def search_live_news(query, limit=10):

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
        "apiKey": NEWS_API_KEY
    }

    try:

        response = requests.get(
            "https://newsapi.org/v2/everything",
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":

            return {
                "error": data.get(
                    "message",
                    "Failed to search news"
                )
            }

        articles = []

        for article in data.get("articles", []):

            articles.append({

                "title": article.get("title") or "",

                "description": (
                    article.get("description") or ""
                ),

                "content": (
                    article.get("content") or ""
                ),

                "source": article.get(
                    "source", {}
                ).get("name"),

                "url": article.get("url"),

                "image": article.get("urlToImage"),

                "published_at": article.get(
                    "publishedAt"
                )

            })

        return articles

    except requests.exceptions.RequestException as e:

        return {
            "error": str(e)
        }


if __name__ == "__main__":

    interests = [
        "AI",
        "Technology",
        "Startups"
    ]

    result = get_top_news(
        interests=interests
    )

    print(result)