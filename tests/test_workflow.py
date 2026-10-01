import pytest
from python_review_bot.agents.workflow import build_graph


def test_graph_compiles():
    g = build_graph()
    assert g is not None


def test_nodes_present():
    g = build_graph()
    assert "diagnose" in g.get_graph().nodes
