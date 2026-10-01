from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import json

from ..models import ReviewRequest, ReviewReport
from ..agents import run_review

app = FastAPI(title="PythonReviewBot", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/review", response_model=ReviewReport)
def review(req: ReviewRequest) -> ReviewReport:
    try:
        return run_review(req.code, req.intent, req.python_version, req.constraints)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/review/stream")
def review_stream(req: ReviewRequest):
    def gen():
        report = run_review(req.code, req.intent, req.python_version, req.constraints)
        for step in report.trace:
            yield f"data: {json.dumps({'step': step})}\n\n"
        yield f"data: {json.dumps({'report': report.model_dump()})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")
