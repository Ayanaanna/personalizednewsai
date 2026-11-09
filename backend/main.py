from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from news_graph import news_app

from rag_service import (
    get_personalized_news,
    rank_personalized_news,
    ask_news,
    generate_article_summaries
)

from news_service import get_top_news


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():

    return {
        "message": "Personalized News AI API is running"
    }


@app.get("/news")
def get_news():

    result = news_app.invoke({
        "results": [],
        "ranked_results": [],
        "context": "",
        "summary": ""
    })

    articles = []

    for item in result["ranked_results"]:

        metadata = item["metadata"]

        articles.append({
            "title": metadata["title"],
            "source": metadata["source"],
            "url": metadata["url"],
            "published_at": metadata["published_at"],
            "relevance_score": item["distance"],
            "image": metadata["image"]
        })

    return {
        "summary": result["summary"],
        "articles": articles
    }

@app.get("/articles")
def get_articles(
    interests: str = "AI,Technology,Startups"
):

    selected_interests = [
        interest.strip()
        for interest in interests.split(",")
        if interest.strip()
    ]

    # ALL NEWS
    if len(selected_interests) == 0:

        result = get_top_news()

        if isinstance(result, dict) and "error" in result:

            return {
                "interests": [],
                "articles": [],
                "error": result["error"]
            }

        articles = result[:10]

        summaries = generate_article_summaries(
            articles
        )

        for index, article in enumerate(articles):

            article["ai_summary"] = (
                summaries[index]
                if index < len(summaries)
                else ""
            )

        return {
            "interests": [],
            "articles": articles
        }

    # NEWS API CATEGORIES
    category_map = {
        "Technology": "technology",
        "Business": "business",
        "Science": "science",
        "Sports": "sports",
        "Movies": "entertainment",
        "World": "general"
    }

    if len(selected_interests) == 1:

        selected = selected_interests[0]

        if selected in category_map:

            category = category_map[selected]

            result = get_top_news(
                category=category
            )

            if isinstance(result, dict) and "error" in result:

                return {
                    "interests": selected_interests,
                    "articles": [],
                    "error": result["error"]
                }

            articles = result[:10]

            summaries = generate_article_summaries(
                articles
            )

            for index, article in enumerate(articles):

                article["ai_summary"] = (
                    summaries[index]
                    if index < len(summaries)
                    else ""
                )

            return {
                "interests": selected_interests,
                "articles": articles
            }

    # RAG PERSONALIZED NEWS
    results = get_personalized_news(
        selected_interests
    )

    ranked_results = rank_personalized_news(
        results
    )

    articles = []

    for item in ranked_results[:10]:

        metadata = item["metadata"]

        articles.append({

            "title": metadata["title"],
            "source": metadata["source"],
            "url": metadata["url"],
            "published_at": metadata["published_at"],
            "distance": item["distance"],
            "image": metadata["image"]

        })

    # Generate AI summaries
    summaries = generate_article_summaries(
        articles
    )

    for index, article in enumerate(articles):

        article["ai_summary"] = (
            summaries[index]
            if index < len(summaries)
            else ""
        )

    return {
        "interests": selected_interests,
        "articles": articles
    }

@app.get("/ask")
def ask_question(question: str):

    result = ask_news(question)

    return result