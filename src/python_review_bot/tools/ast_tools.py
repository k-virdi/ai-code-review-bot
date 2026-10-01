from __future__ import annotations
import ast
from typing import Any


def parse_code(code: str) -> dict[str, Any]:
    """Parse code and return structured AST info. On error, return {'ok': False, 'error': ...}."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"ok": False, "error": f"{e.msg} at line {e.lineno}", "lineno": e.lineno}
    return {"ok": True, "tree": tree}


def summarize_ast(code: str) -> dict[str, Any]:
    parsed = parse_code(code)
    if not parsed["ok"]:
        return {"ok": False, "error": parsed["error"], "functions": [], "classes": [], "imports": []}

    tree: ast.AST = parsed["tree"]
    functions: list[dict] = []
    classes: list[dict] = []
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                "name": node.name,
                "args": [a.arg for a in node.args.args],
                "lineno": node.lineno,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "has_docstring": bool(ast.get_docstring(node)),
            })
        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "bases": [ast.unparse(b) for b in node.bases],
                "lineno": node.lineno,
            })
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return {"ok": True, "functions": functions, "classes": classes, "imports": imports}
