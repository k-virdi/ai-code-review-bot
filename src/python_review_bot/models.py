from __future__ import annotations
from typing import Any, Literal, TypedDict
from pydantic import BaseModel, Field


Strategy = Literal["patch", "rewrite", "alternative", "unknown"]


class ReviewRequest(BaseModel):
    code: str = Field(..., description="The user's Python code")
    intent: str = Field(..., description="What the code is supposed to do")
    python_version: str = "3.11"
    constraints: list[str] = Field(default_factory=list)


class RetrievedDoc(BaseModel):
    source: str
    title: str
    content: str
    score: float = 0.0
    url: str | None = None


class Diagnosis(BaseModel):
    summary: str
    root_causes: list[str] = Field(default_factory=list)
    severity: Literal["info", "minor", "major", "critical"] = "minor"
    strategy: Strategy = "patch"


class ValidationResult(BaseModel):
    passed: bool
    lint_ok: bool = True
    types_ok: bool = True
    tests_ok: bool = True
    stdout: str = ""
    stderr: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class ReviewReport(BaseModel):
    summary: str
    diagnosis: Diagnosis
    diff: str = ""
    fixed_code: str = ""
    explanation: str = ""
    tests: str = ""
    validation: ValidationResult | None = None
    citations: list[RetrievedDoc] = Field(default_factory=list)
    confidence: float = 0.0
    alternatives: list[str] = Field(default_factory=list)
    attempts: int = 0
    trace: list[str] = Field(default_factory=list)


class AgentState(TypedDict, total=False):
    """Shared state passed between LangGraph nodes."""
    request: dict
    parsed: dict
    static_issues: list[str]
    retrieved: list[dict]
    diagnosis: dict
    fix_plan: str
    patch: str
    fixed_code: str
    generated_tests: str
    validation: dict
    critique: str
    attempts: int
    report: dict
    trace: list[str]
