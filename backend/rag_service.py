import os
import time
from datetime import datetime, timezone

import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from dotenv import load_dotenv
from google import genai

from preferences import get_preferences
from database import get_latest_news


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# Load embedding model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


# Create ChromaDB client
chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)


# Create or get news collection
news_collection = chroma_client.get_or_create_collection(
    name="news"
)


def add_news_to_rag():

    articles = get_latest_news(50)

    if not articles:
        print("No news articles found in database.")
        return

    documents = []
    ids = []
    metadatas = []

    for article in articles:

        text = (
            f"Title: {article['title']}\n"
            f"Description: {article['description'] or ''}\n"
            f"Content: {article['content'] or ''}"
        )

        documents.append(text)

        ids.append(
            f"news_{article['id']}"
        )

        metadatas.append({
            "title": article["title"],
            "source": article["source"] or "",
            "url": article["url"] or "",
            "published_at": article["published_at"] or "",
            "image": article["image"] or ""
        })

    embeddings = embedding_model.encode(
        documents
    ).tolist()

    news_collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(
        f"{len(documents)} news articles added to RAG."
    )


def search_news(query, top_k=5, max_distance=1.6):

    # Retrieve more candidates from ChromaDB first
    candidate_count = max(top_k * 2, 8)

    query_embedding = embedding_model.encode(
        [query]
    ).tolist()

    results = news_collection.query(
        query_embeddings=query_embedding,
        n_results=candidate_count,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    candidates = []

    for document, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        candidates.append({
            "document": document,
            "metadata": metadata,
            "distance": distance
        })

    if not candidates:
        return []

    # Prepare question-document pairs for CrossEncoder
    pairs = []

    for candidate in candidates:

        article_text = (
            candidate["metadata"]["title"]
            + " "
            + candidate["document"]
        )

        pairs.append(
            [query, article_text]
        )

    # Calculate reranking scores
    rerank_scores = reranker.predict(
        pairs
    )

    # Add reranking score to each candidate
    for candidate, score in zip(
        candidates,
        rerank_scores
    ):
        candidate["rerank_score"] = float(score)

    # Sort by CrossEncoder relevance
    candidates.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    # Remove duplicate articles
    unique_candidates = []
    seen_urls = set()

    for candidate in candidates:

        url = candidate["metadata"].get("url")

        if url in seen_urls:
            continue

        seen_urls.add(url)
        unique_candidates.append(candidate)

        if len(unique_candidates) == top_k:
            break

    # Return the best unique results
    return unique_candidates


def get_personalized_news(selected_interests=None):

    if selected_interests is None:
        preferences = get_preferences()
        interests = preferences["interests"]
    else:
        interests = selected_interests

    interest_queries = {
        "ai": (
            "artificial intelligence, machine learning, "
            "generative AI, LLMs, AI tools and AI technology"
        ),

        "technology": (
            "technology news, smartphones, software, hardware, "
            "gadgets, computers, digital products and technology companies"
        ),

        "startups": (
            "startup companies, founders, venture capital, "
            "funding, entrepreneurship and new technology businesses"
        ),

        "space": (
            "space exploration, NASA, SpaceX, rockets, satellites, "
            "astronauts and astronomy"
        ),

        "business": (
            "business news, companies, markets, finance, "
            "economy, investments and corporate news"
        ),

        "science": (
            "scientific research, discoveries, scientists, climate, "
            "medicine, biology and scientific studies"
        )
    }

    all_results = []

    for interest in interests:

        interest_lower = interest.lower()

        query = interest_queries.get(
            interest_lower,
            interest
        )

        results = search_news(
            query,
            top_k=5,
            max_distance=1.6
        )

        for result in results:

            result["interest"] = interest

            all_results.append(result)

    return all_results


def rank_personalized_news(results):

    unique_articles = {}

    for result in results:

        url = result["metadata"]["url"]

        if url not in unique_articles:

            unique_articles[url] = result

        else:

            if result["distance"] < unique_articles[url]["distance"]:

                unique_articles[url] = result


    ranked_results = list(
        unique_articles.values()
    )


    for result in ranked_results:

        distance = result["distance"]

        # 1. Semantic relevance
        semantic_score = max(
            0,
            2.0 - distance
        )


        # 2. Small title bonus
        interest = result.get(
            "interest",
            ""
        ).lower()

        title = result["metadata"]["title"].lower()

        title_bonus = 0

        if interest in title:

            title_bonus = 0.2


        # 3. Recency score
        published_at = result["metadata"]["published_at"]

        recency_score = 0

        try:

            published_time = datetime.fromisoformat(
                published_at.replace("Z", "+00:00")
            )

            now = datetime.now(timezone.utc)

            hours_old = (
                now - published_time
            ).total_seconds() / 3600

            if hours_old <= 6:
                recency_score = 1.0

            elif hours_old <= 24:
                recency_score = 0.8

            elif hours_old <= 48:
                recency_score = 0.5

            elif hours_old <= 72:
                recency_score = 0.3

        except Exception:

            recency_score = 0


        # Final ranking score
        result["ranking_score"] = (
            semantic_score * 0.7
            + recency_score * 0.2
            + title_bonus
        )


    ranked_results.sort(
        key=lambda result: result["ranking_score"],
        reverse=True
    )


    return ranked_results



def build_context(results):

    context_parts = []

    for result in results:

        article = result["metadata"]

        context = (
            f"Title: {article['title']}\n"
            f"Source: {article['source']}\n"
            f"Published: {article['published_at']}\n"
            f"Content: {result['document']}\n"
            f"URL: {article['url']}"
        )

        context_parts.append(context)

    return "\n\n---\n\n".join(context_parts)


def generate_summary(context):

    prompt = f"""
You are an AI news assistant.

Summarize the following news information clearly and briefly.

Rules:
- Use only the information provided in the context.
- Do not invent facts.
- Mention the important points.
- Keep the summary easy to understand.
- If there are multiple articles, summarize them separately.
- Include the source for each article.

News context:

{context}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        print("Gemini error:", e)

        return (
            "Gemini is temporarily unavailable. "
            "The relevant news articles were successfully "
            "retrieved from the RAG system."
        )






def ask_news(question):

    # Search ChromaDB using semantic similarity
    rag_results = search_news(
        question,
        top_k=8,
        max_distance=1.6
    )

    # No relevant articles found
    if not rag_results:

        return {
            "answer": (
                "I couldn't find relevant news in my "
                "knowledge base for that question."
            ),
            "sources": []
        }

    # Build context from retrieved articles
    context_parts = []

    for result in rag_results:

        document = result["document"]
        metadata = result["metadata"]

        context = (
            f"Title: {metadata['title']}\n"
            f"Source: {metadata['source']}\n"
            f"Published: {metadata['published_at']}\n"
            f"Content: {document}\n"
            f"URL: {metadata['url']}"
        )

        context_parts.append(context)

    context = "\n\n---\n\n".join(context_parts)

    # Gemini prompt
    prompt = f"""
You are an AI news assistant.

Answer the user's question using ONLY the news
articles retrieved from the knowledge base below.

User question:
{question}

Rules:
- Give a clear and useful answer.
- Use only information from the retrieved articles.
- Do not invent facts.
- If the retrieved articles do not contain enough
  information, clearly say so.
- Combine information from multiple articles when useful.
- Mention important dates when relevant.
- Mention the news source when appropriate.
- Do NOT include URLs in the answer.
- Do NOT create a separate Sources section.
- Keep the answer concise and easy to understand.

Retrieved news articles:

{context}
"""

    # Try Gemini models in order
    models = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash"
    ]

    answer = None

    for model_name in models:

        try:

            print(
                f"Trying Gemini model: {model_name}"
            )

            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            answer = response.text

            print(
                f"Gemini response generated using "
                f"{model_name}"
            )

            break

        except Exception as e:

            print(
                f"{model_name} failed: {e}"
            )

    # If all models failed
    if answer is None:

        answer = (
            "I found relevant news articles, "
            "but the AI response is temporarily "
            "unavailable. Please try again later."
        )

    # Prepare sources
    sources = []

    seen_urls = set()

    for result in rag_results:

        metadata = result["metadata"]

        url = metadata["url"]

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)

        sources.append({
            "title": metadata["title"],
            "source": metadata["source"],
            "url": url
        })

    return {
        "answer": answer,
        "sources": sources
    }




def generate_article_summaries(articles):

    if not articles:
        return []

    articles_text = []

    for index, article in enumerate(articles):

        text = (
            f"ARTICLE {index + 1}\n"
            f"Title: {article.get('title', '')}\n"
            f"Description: {article.get('description', '')}\n"
            f"Content: {article.get('content', '')}\n"
        )

        articles_text.append(text)

    combined_text = "\n\n---\n\n".join(articles_text)

    prompt = f"""
You are an AI news summarization assistant.

Create a detailed summary for EACH news article.

For every article:
- Write a detailed summary of 5 to 7 sentences.
- The summary should be approximately 80 to 120 words.
- Do not stop after 1 or 2 sentences.
- Explain what happened, who is involved, where it happened, and why it matters when the article provides that information.
- Include important dates, numbers, organizations, and locations when available.
- Use information from both the description and content.
- Do not simply copy the description.
- Do not invent or assume any information.

IMPORTANT:

Return exactly one block for every article.

Use this format:

ARTICLE 1:
Your summary here.

ARTICLE 2:
Your summary here.

Continue until all articles are summarized.

News articles:

{combined_text}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        result = response.text or ""

        print("\n===== GEMINI ARTICLE SUMMARY RESPONSE =====")
        print(result)
        print("===========================================\n")

        summaries = []

        for index in range(len(articles)):

            current_marker = f"ARTICLE {index + 1}:"

            start = result.upper().find(
                current_marker.upper()
            )

            if start == -1:
                summaries.append("")
                continue

            start += len(current_marker)

            if index + 1 < len(articles):

                next_marker = (
                    f"ARTICLE {index + 2}:"
                )

                end = result.upper().find(
                    next_marker.upper(),
                    start
                )

                if end == -1:
                    summary = result[start:]
                else:
                    summary = result[start:end]

            else:

                summary = result[start:]

            summaries.append(
                summary.strip()
            )

        return summaries

    except Exception as e:

        print(
            "Gemini unavailable. Using fallback summary."
        )
        print("Gemini error:", e)

        fallback_summaries = []

        for article in articles:

            description = (
                article.get("description")
                or ""
            ).strip()

            content = (
                article.get("content")
                or ""
            ).strip()

            title = (
                article.get("title")
                or ""
            ).strip()

            if description:
                summary = description

            elif content:
                summary = content

            elif title:
                summary = title

            else:
                summary = (
                    "A news article is available, "
                    "but a summary could not be generated."
                )

            fallback_summaries.append(summary)

        return fallback_summaries



    
if __name__ == "__main__":

    add_news_to_rag()

    results = get_personalized_news()

    ranked_results = rank_personalized_news(
        results
    )

    context = build_context(
        ranked_results
    )

    summary = generate_summary(
        context
    )

    print("\nAI News Summary:\n")
    print(summary)