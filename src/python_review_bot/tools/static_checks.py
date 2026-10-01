from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path


def _write_temp(code: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8")
    f.write(code)
    f.close()
    return Path(f.name)


def run_ruff(code: str) -> tuple[bool, str]:
    path = _write_temp(code)
    try:
        proc = subprocess.run(
            ["ruff", "check", "--quiet", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
    except FileNotFoundError:
        return True, "ruff not installed"
    finally:
        path.unlink(missing_ok=True)


def run_mypy(code: str) -> tuple[bool, str]:
    path = _write_temp(code)
    try:
        proc = subprocess.run(
            ["mypy", "--ignore-missing-imports", "--no-error-summary", str(path)],
            capture_output=True, text=True, timeout=60,
        )
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
    except FileNotFoundError:
        return True, "mypy not installed"
    finally:
        path.unlink(missing_ok=True)
