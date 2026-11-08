"""LangGraph flow for the Amazon shopping assistant.

✍️ Claude wrote this file (2026-11-08, trial at Yamato's request). Not reviewed yet.
Built from RAG Explorer's graph_router (contextualize, critic, record_history, SQLite checkpointer).

The router looks at the input, not at the meaning of the question:
    image      -> describe_image -> (contextualize if there is history) -> search
    follow-up  -> contextualize -> search
    text       -> search
then search -> generate -> critic -> record_history.
"""
import operator
import sqlite3
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from src.amazon.image_query import describe_image
from src.amazon.pipeline import generate_answer, search, text_of
from src.query_rewriting import contextualize_query


class ShopState(TypedDict, total=False):
    query: str
    image: bytes | None
    image_mime: str
    image_query: str
    resolved_query: str
    route: str
    results: list[dict]
    answer: str
    history: Annotated[list[str], operator.add]


def decide_route(state: ShopState) -> Literal["image", "follow_up", "text"]:
    if state.get("image"):
        return "image"
    if state.get("history"):
        return "follow_up"
    return "text"


def after_image(state: ShopState) -> Literal["contextualize", "search"]:
    return "contextualize" if state.get("history") else "search"


def build_shop_graph(collection, embeddings, llm, top_k: int = 10, db_path: str = "checkpoints.sqlite"):
    def router(state: ShopState) -> dict:
        return {"route": decide_route(state), "resolved_query": state["query"]}

    def describe(state: ShopState) -> dict:
        text = describe_image(state["image"], llm, state.get("image_mime", "image/jpeg"), note=state["query"])
        return {"image_query": text, "resolved_query": text}

    def contextualize(state: ShopState) -> dict:
        return {"resolved_query": contextualize_query(state["resolved_query"], state["history"], llm)}

    def retrieve(state: ShopState) -> dict:
        return {"results": search(state["resolved_query"], collection, embeddings, top_k)}

    def generate(state: ShopState) -> dict:
        return {"answer": generate_answer(state["resolved_query"], state["results"], llm)}

    def critic(state: ShopState) -> dict:
        context = "\n".join(f"[{r['product_id']}] {r['document']}" for r in state["results"])
        response = llm.invoke(
            f"Request: {state['resolved_query']}\nAnswer: {state['answer']}\nEvidence:\n{context}\n\n"
            "If the answer is not supported by the evidence, put '⚠️ Check: ' and the reason first, "
            "then return the answer. Otherwise return the answer unchanged."
        )
        return {"answer": text_of(response)}

    def record_history(state: ShopState) -> dict:
        # The image itself is not kept: the next turn only needs what was searched.
        return {"history": [f"Q: {state['resolved_query']}\nA: {state['answer']}"], "image": None}

    graph = StateGraph(ShopState)
    for name, node in [("router", router), ("describe_image", describe), ("contextualize", contextualize),
                       ("search", retrieve), ("generate", generate), ("critic", critic),
                       ("record_history", record_history)]:
        graph.add_node(name, node)
    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", lambda s: s["route"],
                                {"image": "describe_image", "follow_up": "contextualize", "text": "search"})
    graph.add_conditional_edges("describe_image", after_image, {"contextualize": "contextualize", "search": "search"})
    graph.add_edge("contextualize", "search")
    graph.add_edge("search", "generate")
    graph.add_edge("generate", "critic")
    graph.add_edge("critic", "record_history")
    graph.add_edge("record_history", END)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return graph.compile(checkpointer=SqliteSaver(conn))
