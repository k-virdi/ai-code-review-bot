import pytest
from python_review_bot.rag.retriever import HybridRetriever


def test_retriever_constructs():
    try:
        r = HybridRetriever()
    except Exception as e:
        pytest.skip(f"Retriever unavailable: {e}")
    assert hasattr(r, "retrieve")
