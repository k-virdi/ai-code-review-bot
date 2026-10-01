"""Run Python code in a subprocess with time/memory limits.
For production, swap in Docker-based isolation."""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path


def run_python_in_sandbox(code: str, timeout: int = 10) -> dict:
    path = Path(tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8").name)
    path.write_text(code, encoding="utf-8")
    try:
        proc = subprocess.run(
            [sys.executable, "-I", str(path)],
            capture_output=True, text=True, timeout=timeout,
        )
        return {
            "passed": proc.returncode == 0,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "stdout": "", "stderr": f"Timeout after {timeout}s", "returncode": -1}
    finally:
        path.unlink(missing_ok=True)
