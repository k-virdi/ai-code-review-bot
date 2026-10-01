"""LangGraph agent workflow for Python code review."""
from __future__ import annotations
import json
import re
from typing import Any

from langgraph.graph import StateGraph, END

from ..models import AgentState, ReviewReport, Diagnosis, ValidationResult, RetrievedDoc
from ..tools import summarize_ast, unified_diff, run_ruff, run_mypy, run_python_in_sandbox
from ..rag.retriever import HybridRetriever
from .llm import chat
from . import prompts as P


_CODE_BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def _extract_code(text: str) -> str:
    m = _CODE_BLOCK.search(text)
    return m.group(1).strip() if m else text.strip()


def _add_trace(state: AgentState, msg: str) -> list[str]:
    trace = list(state.get("trace", []))
    trace.append(msg)
    return trace


# ---------- Nodes ----------

def node_intake(state: AgentState) -> dict:
    req = state["request"]
    raw = chat(P.INTAKE_SYSTEM, f"CODE:\n{req['code']}\n\nINTENT:\n{req['intent']}", json_mode=True)
    try:
        data = json.loads(raw)
    except Exception:
        data = {"complete": True, "questions": [], "normalized_intent": req["intent"]}
    return {
        "request": {**req, "intent": data.get("normalized_intent") or req["intent"]},
        "trace": _add_trace(state, f"intake: complete={data.get('complete')}"),
    }


def node_parse(state: AgentState) -> dict:
    code = state["request"]["code"]
    summary = summarize_ast(code)
    return {"parsed": summary, "trace": _add_trace(state, "parse: ok")}


def node_static(state: AgentState) -> dict:
    code = state["request"]["code"]
    issues: list[str] = []
    ok_ruff, out_ruff = run_ruff(code)
    if not ok_ruff:
        issues.append(f"ruff: {out_ruff.splitlines()[0] if out_ruff else 'issues'}")
    ok_mypy, out_mypy = run_mypy(code)
    if not ok_mypy:
        issues.append(f"mypy: {out_mypy.splitlines()[0] if out_mypy else 'issues'}")
    return {"static_issues": issues, "trace": _add_trace(state, f"static: {len(issues)} issues")}


def node_retrieve(state: AgentState) -> dict:
    req = state["request"]
    parsed = state.get("parsed", {})
    fns = [f["name"] for f in parsed.get("functions", [])]
    queries = [
        req["intent"],
        f"python best practices for: {req['intent']}",
        " ".join(fns) if fns else "python function",
        *state.get("static_issues", []),
    ]
    try:
        docs = HybridRetriever().retrieve(queries)
    except Exception as e:
        docs = []
        print(f"[warn] retriever failed: {e}")
    return {
        "retrieved": [d.model_dump() for d in docs],
        "trace": _add_trace(state, f"retrieve: {len(docs)} docs"),
    }


def node_diagnose(state: AgentState) -> dict:
    req = state["request"]
    ctx = "\n---\n".join(d["content"][:1200] for d in state.get("retrieved", [])[:4])
    user = (
        f"CODE:\n{req['code']}\n\nINTENT:\n{req['intent']}\n\n"
        f"AST SUMMARY:\n{json.dumps(state.get('parsed', {}))}\n\n"
        f"STATIC ISSUES:\n{state.get('static_issues', [])}\n\n"
        f"RETRIEVED CONTEXT:\n{ctx}"
    )
    raw = chat(P.DIAGNOSIS_SYSTEM, user, json_mode=True)
    try:
        diag = json.loads(raw)
    except Exception:
        diag = {"summary": raw[:400], "root_causes": [], "severity": "minor", "strategy": "patch"}
    return {"diagnosis": diag, "trace": _add_trace(state, f"diagnose: {diag.get('strategy')}")}


def node_plan(state: AgentState) -> dict:
    user = f"DIAGNOSIS:\n{json.dumps(state.get('diagnosis', {}))}\n\nINTENT:\n{state['request']['intent']}"
    plan = chat(P.PLAN_SYSTEM, user)
    return {"fix_plan": plan, "trace": _add_trace(state, "plan: ok")}


def node_generate(state: AgentState) -> dict:
    req = state["request"]
    user = (
        f"INTENT:\n{req['intent']}\n\nORIGINAL CODE:\n{req['code']}\n\n"
        f"PLAN:\n{state.get('fix_plan', '')}\n\n"
        f"DIAGNOSIS:\n{json.dumps(state.get('diagnosis', {}))}"
    )
    raw = chat(P.GENERATE_SYSTEM, user, temperature=0.0)
    fixed = _extract_code(raw)
    diff = unified_diff(req["code"], fixed)
    return {
        "fixed_code": fixed,
        "patch": diff,
        "trace": _add_trace(state, "generate: ok"),
    }


def node_tests(state: AgentState) -> dict:
    req = state["request"]
    user = f"INTENT:\n{req['intent']}\n\nFIXED CODE:\n{state.get('fixed_code', '')}"
    raw = chat(P.TESTS_SYSTEM, user, temperature=0.0)
    return {"generated_tests": _extract_code(raw), "trace": _add_trace(state, "tests: ok")}


def node_validate(state: AgentState) -> dict:
    fixed = state.get("fixed_code", "")
    tests = state.get("generated_tests", "")
    lint_ok, lint_out = run_ruff(fixed)
    types_ok, types_out = run_mypy(fixed)
    combined = f"{fixed}\n\n# --- tests ---\n{tests}" if tests else fixed
    run = run_python_in_sandbox(combined, timeout=15)
    passed = lint_ok and run["passed"]
    validation = ValidationResult(
        passed=passed,
        lint_ok=lint_ok,
        types_ok=types_ok,
        tests_ok=run["passed"],
        stdout=run["stdout"],
        stderr=(run["stderr"] + "\n" + lint_out + "\n" + types_out).strip(),
    )
    return {"validation": validation.model_dump(), "trace": _add_trace(state, f"validate: passed={passed}")}


def node_critique(state: AgentState) -> dict:
    req = state["request"]
    user = (
        f"INTENT:\n{req['intent']}\n\nORIGINAL:\n{req['code']}\n\n"
        f"FIXED:\n{state.get('fixed_code', '')}\n\n"
        f"VALIDATION:\n{json.dumps(state.get('validation', {}))}"
    )
    raw = chat(P.CRITIC_SYSTEM, user, json_mode=True)
    try:
        data = json.loads(raw)
    except Exception:
        data = {"ok": True, "feedback": "unparsed"}
    return {
        "critique": data.get("feedback", ""),
        "attempts": state.get("attempts", 0) + 1,
        "trace": _add_trace(state, f"critique: ok={data.get('ok')}"),
    }


def node_finalize(state: AgentState) -> dict:
    req = state["request"]
    val = state.get("validation", {})
    diag = state.get("diagnosis", {})
    diff = state.get("patch", "")
    raw_expl = chat(P.FINAL_SYSTEM, f"DIFF:\n{diff}\n\nDIAGNOSIS:\n{json.dumps(diag)}")

    report = ReviewReport(
        summary=diag.get("summary", "Review complete."),
        diagnosis=Diagnosis(
            summary=diag.get("summary", ""),
            root_causes=diag.get("root_causes", []),
            severity=diag.get("severity", "minor"),
            strategy=diag.get("strategy", "patch"),
        ),
        diff=diff,
        fixed_code=state.get("fixed_code", ""),
        explanation=raw_expl,
        tests=state.get("generated_tests", ""),
        validation=ValidationResult(**val) if val else None,
        citations=[RetrievedDoc(**d) for d in state.get("retrieved", [])],
        confidence=0.85 if val.get("passed") else 0.45,
        attempts=state.get("attempts", 0),
        trace=state.get("trace", []),
    )
    return {"report": report.model_dump(), "trace": _add_trace(state, "finalize: ok")}


# ---------- Routing ----------

def _route_after_critique(state: AgentState) -> str:
    from ..config import get_settings
    val = state.get("validation", {})
    if val.get("passed"):
        return "finalize"
    if state.get("attempts", 0) >= get_settings().max_attempts:
        return "finalize"
    return "generate"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("intake", node_intake)
    g.add_node("parse", node_parse)
    g.add_node("static", node_static)
    g.add_node("retrieve", node_retrieve)
    g.add_node("diagnose", node_diagnose)
    g.add_node("plan", node_plan)
    g.add_node("generate", node_generate)
    g.add_node("tests", node_tests)
    g.add_node("validate", node_validate)
    g.add_node("critique", node_critique)
    g.add_node("finalize", node_finalize)

    g.set_entry_point("intake")
    g.add_edge("intake", "parse")
    g.add_edge("parse", "static")
    g.add_edge("static", "retrieve")
    g.add_edge("retrieve", "diagnose")
    g.add_edge("diagnose", "plan")
    g.add_edge("plan", "generate")
    g.add_edge("generate", "tests")
    g.add_edge("tests", "validate")
    g.add_edge("validate", "critique")
    g.add_conditional_edges("critique", _route_after_critique,
                            {"finalize": "finalize", "generate": "generate"})
    g.add_edge("finalize", END)
    return g.compile()


def run_review(code: str, intent: str, python_version: str = "3.11",
               constraints: list[str] | None = None) -> ReviewReport:
    graph = build_graph()
    init: AgentState = {
        "request": {"code": code, "intent": intent,
                    "python_version": python_version,
                    "constraints": constraints or []},
        "attempts": 0,
        "trace": [],
    }
    final: dict[str, Any] = graph.invoke(init)
    return ReviewReport(**final["report"])
