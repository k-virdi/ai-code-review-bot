import streamlit as st
from python_review_bot.agents import run_review

st.set_page_config(page_title="PythonReviewBot", page_icon="🐍", layout="wide")
st.title("🐍 PythonReviewBot — AI Code Review Copilot")
st.caption("RAG + agent workflow that fixes Python code to match your intent.")

col1, col2 = st.columns(2)
with col1:
    code = st.text_area("Paste your Python code", height=360, value="def f(x):\n    return x.sort()\n")
with col2:
    intent = st.text_area("What should it do?", height=140,
                          value="Return a new list of unique items sorted ascending, without mutating input.")
    py = st.selectbox("Python version", ["3.11", "3.12", "3.10"])

if st.button("Review & Fix", type="primary"):
    with st.spinner("Running agent workflow..."):
        report = run_review(code, intent, py)
    st.subheader("Diagnosis")
    st.write(report.summary)
    for c in report.diagnosis.root_causes:
        st.markdown(f"- {c}")
    st.subheader("Diff")
    st.code(report.diff or "(no changes)", language="diff")
    st.subheader("Fixed code")
    st.code(report.fixed_code, language="python")
    st.subheader("Explanation")
    st.write(report.explanation)
    if report.validation:
        st.subheader("Validation")
        st.write({"passed": report.validation.passed, "lint": report.validation.lint_ok,
                  "types": report.validation.types_ok, "tests": report.validation.tests_ok})
    st.subheader("Trace")
    st.json(report.trace)
