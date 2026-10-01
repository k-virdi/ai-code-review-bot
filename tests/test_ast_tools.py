from python_review_bot.tools.ast_tools import summarize_ast, parse_code


def test_parse_valid():
    assert parse_code("x = 1")["ok"] is True


def test_parse_invalid():
    assert parse_code("def f(:")["ok"] is False


def test_summarize():
    code = "import os\n\ndef f(a, b):\n    return a + b\n\nclass C:\n    pass\n"
    s = summarize_ast(code)
    assert s["ok"]
    assert s["functions"][0]["name"] == "f"
    assert s["classes"][0]["name"] == "C"
    assert "os" in s["imports"]
