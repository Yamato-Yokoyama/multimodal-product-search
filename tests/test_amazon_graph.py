"""Routing and image-message tests. No model, network or index is used.

✍️ Claude wrote this file (2026-11-08).
"""
from src.amazon.graph import decide_route
from src.amazon.image_query import image_message


def test_image_wins_over_history():
    assert decide_route({"query": "this in black", "image": b"x", "history": ["Q: a\nA: b"]}) == "image"


def test_follow_up_when_history_exists():
    assert decide_route({"query": "the cheaper one?", "image": None, "history": ["Q: a\nA: b"]}) == "follow_up"


def test_plain_text_first_turn():
    assert decide_route({"query": "bose earbuds", "image": None, "history": []}) == "text"


def test_image_message_has_text_and_image_parts():
    message = image_message(b"\xff\xd8", "image/jpeg", note="for kids")
    kinds = [part["type"] for part in message.content]
    assert kinds == ["text", "image_url"]
    assert message.content[1]["image_url"].startswith("data:image/jpeg;base64,")
    assert "for kids" in message.content[0]["text"]
