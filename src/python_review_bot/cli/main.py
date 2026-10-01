from __future__ import annotations
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

from ..agents import run_review

app = typer.Typer(help="PythonReviewBot — AI code review copilot.")
console = Console()


@app.command()
def review(
    path: Path = typer.Argument(..., exists=True, readable=True),
    intent: str = typer.Option(..., "--intent", "-i", help="What the code should do"),
    python_version: str = typer.Option("3.11", "--py"),
) -> None:
    code = path.read_text(encoding="utf-8")
    console.print(Panel.fit(f"[bold]Reviewing[/bold] {path}\n[dim]Intent:[/dim] {intent}"))

    report = run_review(code, intent, python_version)

    console.rule("[bold]Diagnosis")
    console.print(Markdown(report.summary))
    for cause in report.diagnosis.root_causes:
        console.print(f"  • {cause}")

    if report.diff:
        console.rule("[bold]Diff")
        console.print(Syntax(report.diff, "diff", theme="monokai"))

    console.rule("[bold]Explanation")
    console.print(Markdown(report.explanation))

    if report.validation:
        status = "[green]PASSED[/green]" if report.validation.passed else "[red]FAILED[/red]"
        console.print(f"\nValidation: {status}  attempts={report.attempts}  confidence={report.confidence:.2f}")
        if not report.validation.passed:
            console.print(report.validation.stderr[:800])

    if report.citations:
        console.rule("[bold]Citations")
        for c in report.citations[:5]:
            console.print(f"  • [cyan]{c.source}[/cyan] — {c.title}")


if __name__ == "__main__":
    app()
