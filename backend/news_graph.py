from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from rag_service import (
    get_personalized_news,
    rank_personalized_news,
    build_context,
    generate_summary
)


class NewsState(TypedDict):

    results: list
    ranked_results: list
    context: str
    summary: str


def retrieve_news(state: NewsState):

    results = get_personalized_news()

    return {
        "results": results
    }


def rank_news(state: NewsState):

    ranked_results = rank_personalized_news(
        state["results"]
    )

    return {
        "ranked_results": ranked_results
    }


def create_context(state: NewsState):

    context = build_context(
        state["ranked_results"]
    )

    return {
        "context": context
    }


def summarize_news(state: NewsState):

    summary = generate_summary(
        state["context"]
    )

    return {
        "summary": summary
    }


# Create graph
graph = StateGraph(NewsState)


# Add nodes
graph.add_node(
    "retrieve_news",
    retrieve_news
)

graph.add_node(
    "rank_news",
    rank_news
)

graph.add_node(
    "create_context",
    create_context
)

graph.add_node(
    "summarize_news",
    summarize_news
)


# Connect nodes
graph.add_edge(
    START,
    "retrieve_news"
)

graph.add_edge(
    "retrieve_news",
    "rank_news"
)

graph.add_edge(
    "rank_news",
    "create_context"
)

graph.add_edge(
    "create_context",
    "summarize_news"
)

graph.add_edge(
    "summarize_news",
    END
)


# Compile graph
news_app = graph.compile()


if __name__ == "__main__":

    result = news_app.invoke({
        "results": [],
        "ranked_results": [],
        "context": "",
        "summary": ""
    })

    print("\n===== PERSONALIZED AI NEWS =====\n")
    print(result["summary"])