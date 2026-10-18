"""Report renderer — outputs DORA reports to terminal (Rich), Markdown, or JSON."""

from __future__ import annotations

from typing import Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.models import DORAReport, PerformanceBand

BAND_COLOR: dict[PerformanceBand, str] = {
    PerformanceBand.ELITE: "green",
    PerformanceBand.HIGH: "cyan",
    PerformanceBand.MEDIUM: "yellow",
    PerformanceBand.LOW: "red",
}

BAND_LABEL: dict[PerformanceBand, str] = {
    PerformanceBand.ELITE: "Elite",
    PerformanceBand.HIGH: "High",
    PerformanceBand.MEDIUM: "Medium",
    PerformanceBand.LOW: "Low",
}


def _colored(band: PerformanceBand, text: str) -> str:
    color = BAND_COLOR[band]
    return f"[{color}]{text}[/{color}]"


class DORAReporter:
    """Renders DORAReport objects in various output formats."""

    def __init__(self, console: Optional[Console] = None) -> None:
        self.console = console or Console()

    def print_report(self, report: DORAReport) -> None:
        """Render the report as a Rich terminal table."""
        overall_label = BAND_LABEL[report.overall_band]
        overall_colored = _colored(report.overall_band, overall_label)

        self.console.print(
            Panel(
                f"[bold]DORA Metrics Report[/bold]\n"
                f"Team: [bold]{report.team}[/bold]  |  "
                f"Window: {report.window_days} days  |  "
                f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"Overall Performance: {overall_colored}",
                box=box.ROUNDED,
                expand=False,
            )
        )

        table = Table(box=box.SIMPLE_HEAD, show_header=True, min_width=70)
        table.add_column("Metric", style="bold", min_width=28)
        table.add_column("Value", min_width=38)
        table.add_column("Band", min_width=8)

        # Deployment Frequency
        df = report.deployment_frequency
        table.add_row(
            "Deployment Frequency",
            f"{df.total_deployments} deploys  "
            f"({df.deployments_per_day:.2f}/day, "
            f"{df.deployments_per_week:.1f}/week)",
            _colored(df.band, BAND_LABEL[df.band]),
        )

        # Lead Time for Changes
        lt = report.lead_time
        if lt.sample_size > 0:
            lt_val = (
                f"{lt.avg_lead_time_hours:.1f}h avg  "
                f"| {lt.median_lead_time_hours:.1f}h median  "
                f"| n={lt.sample_size}"
            )
        else:
            lt_val = "No data (PRs not enriched)"
        table.add_row(
            "Lead Time for Changes",
            lt_val,
            _colored(lt.band, BAND_LABEL[lt.band]),
        )

        # Change Failure Rate
        cfr = report.change_failure_rate
        table.add_row(
            "Change Failure Rate",
            f"{cfr.failure_rate_pct:.1f}%  "
            f"({cfr.failed_deployments}/{cfr.total_deployments} deploys)",
            _colored(cfr.band, BAND_LABEL[cfr.band]),
        )

        # MTTR
        mttr = report.mttr
        if mttr.total_incidents > 0 and mttr.avg_mttr_hours > 0:
            mttr_val = (
                f"{mttr.avg_mttr_hours:.1f}h avg  "
                f"| {mttr.median_mttr_hours:.1f}h median  "
                f"| {mttr.total_incidents} incidents"
            )
        elif mttr.total_incidents > 0:
            mttr_val = f"{mttr.total_incidents} incidents (none resolved)"
        else:
            mttr_val = "No incidents"
        table.add_row(
            "Mean Time to Recovery",
            mttr_val,
            _colored(mttr.band, BAND_LABEL[mttr.band]),
        )

        self.console.print(table)

    def to_markdown(self, report: DORAReport) -> str:
        """Render the report as a Markdown string."""
        df = report.deployment_frequency
        lt = report.lead_time
        cfr = report.change_failure_rate
        mttr = report.mttr

        lt_val = (
            f"{lt.avg_lead_time_hours:.1f}h avg (n={lt.sample_size})"
            if lt.sample_size > 0
            else "No data"
        )
        mttr_val = (
            f"{mttr.avg_mttr_hours:.1f}h avg"
            if mttr.total_incidents > 0 and mttr.avg_mttr_hours > 0
            else "No incidents"
        )

        lines = [
            "# DORA Metrics Report",
            "",
            f"**Team:** {report.team}  ",
            f"**Window:** {report.window_days} days  ",
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}  ",
            f"**Overall Performance:** {BAND_LABEL[report.overall_band]}",
            "",
            "| Metric | Value | Band |",
            "|--------|-------|------|",
            f"| Deployment Frequency | {df.total_deployments} deploys ({df.deployments_per_day:.2f}/day) | {BAND_LABEL[df.band]} |",
            f"| Lead Time for Changes | {lt_val} | {BAND_LABEL[lt.band]} |",
            f"| Change Failure Rate | {cfr.failure_rate_pct:.1f}% ({cfr.failed_deployments}/{cfr.total_deployments}) | {BAND_LABEL[cfr.band]} |",
            f"| Mean Time to Recovery | {mttr_val} | {BAND_LABEL[mttr.band]} |",
        ]
        return "\n".join(lines)

    def to_json(self, report: DORAReport) -> str:
        """Render the report as a JSON string."""
        return report.model_dump_json(indent=2)
