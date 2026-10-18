"""DORA Metrics Dashboard — CLI entry point."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

app = typer.Typer(
    name="dora",
    help="DORA Metrics Dashboard — measure your team's delivery performance.",
    add_completion=False,
)
console = Console()
logging.basicConfig(level=logging.WARNING)


@app.command()
def report(
    owner: str = typer.Option(..., envvar="GITHUB_OWNER", help="GitHub owner/org"),
    repo: str = typer.Option(..., envvar="GITHUB_REPO", help="GitHub repo name"),
    team: str = typer.Option("platform-team", help="Team name for the report"),
    environment: str = typer.Option(
        "production", help="Deployment environment to analyse"
    ),
    days: int = typer.Option(30, help="Analysis window in days"),
    format: str = typer.Option(
        "terminal", help="Output format: terminal | markdown | json"
    ),
    output: Optional[Path] = typer.Option(None, help="Save report to file"),
) -> None:
    """Generate a DORA metrics report from live GitHub + PagerDuty data."""
    from src.github_client import GitHubClient
    from src.metrics_calculator import MetricsCalculator
    from src.pagerduty_client import PagerDutyClient
    from src.reporter import DORAReporter

    github_token = os.getenv("GITHUB_TOKEN")
    pd_key = os.getenv("PAGERDUTY_API_KEY")

    if not github_token:
        console.print("[red]Error:[/red] GITHUB_TOKEN environment variable not set.")
        raise typer.Exit(1)

    console.print(
        f"[dim]Fetching deployments from GitHub "
        f"({owner}/{repo}, env={environment}, last {days} days)...[/dim]"
    )
    gh = GitHubClient(github_token, owner, repo)
    deployments = gh.get_deployments(environment=environment, since_days=days)
    console.print(
        f"[dim]Enriching {len(deployments)} deployments with PR lead time data...[/dim]"
    )
    deployments = gh.enrich_with_pr_data(deployments)

    incidents = []
    if pd_key:
        console.print("[dim]Fetching incidents from PagerDuty...[/dim]")
        pd_client = PagerDutyClient(pd_key)
        incidents = pd_client.get_incidents(since_days=days)
    else:
        console.print(
            "[yellow]PAGERDUTY_API_KEY not set — MTTR will show no data.[/yellow]"
        )

    calc = MetricsCalculator()
    report_data = calc.compute_report(
        team=team,
        deployments=deployments,
        incidents=incidents,
        window_days=days,
    )

    reporter = DORAReporter(console)
    _render(reporter, report_data, format, output)


@app.command()
def demo(
    days: int = typer.Option(30, help="Window in days"),
    format: str = typer.Option(
        "terminal", help="Output format: terminal | markdown | json"
    ),
    output: Optional[Path] = typer.Option(None, help="Save report to file"),
) -> None:
    """Run a demo report using built-in sample data (no API keys required)."""
    from src.metrics_calculator import MetricsCalculator
    from src.reporter import DORAReporter
    from src.sample_loader import load_sample_data

    console.print("[dim]Loading sample data for demo...[/dim]")
    deployments, incidents = load_sample_data()

    calc = MetricsCalculator()
    report_data = calc.compute_report(
        team="demo-team",
        deployments=deployments,
        incidents=incidents,
        window_days=days,
    )

    reporter = DORAReporter(console)
    _render(reporter, report_data, format, output)


def _render(reporter, report_data, format: str, output: Optional[Path]) -> None:  # type: ignore[no-untyped-def]
    from src.reporter import DORAReporter

    if format == "terminal":
        reporter.print_report(report_data)
    elif format == "markdown":
        content = reporter.to_markdown(report_data)
        if output:
            output.write_text(content)
            console.print(f"[green]Markdown report saved to {output}[/green]")
        else:
            console.print(content)
    elif format == "json":
        content = reporter.to_json(report_data)
        if output:
            output.write_text(content)
            console.print(f"[green]JSON report saved to {output}[/green]")
        else:
            console.print(content)
    else:
        console.print(f"[red]Unknown format:[/red] {format}. Use terminal|markdown|json.")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
