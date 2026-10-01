from __future__ import annotations
import difflib


def unified_diff(original: str, revised: str, fromfile: str = "before.py", tofile: str = "after.py") -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            revised.splitlines(keepends=True),
            fromfile=fromfile,
            tofile=tofile,
        )
    )
