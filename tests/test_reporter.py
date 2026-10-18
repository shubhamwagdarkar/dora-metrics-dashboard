"""Tests for src/reporter.py — 16 tests."""

import json
from datetime import datetime, timezone
from io import StringIO

import pytest
from rich.console import Console

from src.models import (
    ChangeFailureRateMetric,
    DORAReport,
    DeploymentFrequencyMetric,
    LeadTimeMetric,
    MTTRMetric,
    PerformanceBand,
)
from src.reporter import DORAReporter

NOW = datetime.now(timezone.utc)


def _make_report(
    team: str = "platform-team",
    window_days: int = 30,
    df_band: PerformanceBand = PerformanceBand.HIGH,
    lt_band: PerformanceBand = PerformanceBand.HIGH,
    cfr_band: PerformanceBand = PerformanceBand.ELITE,
    mttr_band: PerformanceBand = PerformanceBand.HIGH,
    overall_band: PerformanceBand = PerformanceBand.HIGH,
    lt_sample_size: int = 10,
    lt_avg: float = 12.0,
    total_incidents: int = 3,
    mttr_avg: float = 2.0,
    total_deployments: int = 12,
    failed_deployments: int = 1,
) -> DORAReport:
    return DORAReport(
        team=team,
        window_days=window_days,
        generated_at=NOW,
        deployment_frequency=DeploymentFrequencyMetric(
            total_deployments=total_deployments,
            days_in_window=window_days,
            deployments_per_day=round(total_deployments / window_days, 2),
            deployments_per_week=round(total_deployments / window_days * 7, 2),
            band=df_band,
        ),
        lead_time=LeadTimeMetric(
            avg_lead_time_hours=lt_avg,
            median_lead_time_hours=lt_avg * 0.9,
            p95_lead_time_hours=lt_avg * 1.5,
            sample_size=lt_sample_size,
            band=lt_band,
        ),
        change_failure_rate=ChangeFailureRateMetric(
            total_deployments=total_deployments,
            failed_deployments=failed_deployments,
            failure_rate_pct=round(failed_deployments / total_deployments * 100, 2),
            band=cfr_band,
        ),
        mttr=MTTRMetric(
            total_incidents=total_incidents,
            avg_mttr_hours=mttr_avg,
            median_mttr_hours=mttr_avg * 0.8,
            band=mttr_band,
        ),
        overall_band=overall_band,
    )


@pytest.fixture
def reporter() -> DORAReporter:
    buffer = StringIO()
    console = Console(file=buffer, highlight=False, markup=False)
    return DORAReporter(console=console)


class TestPrintReport:
    def test_prints_without_error(self, reporter):
        report = _make_report()
        reporter.print_report(report)  # should not raise

    def test_default_console_created_if_none(self):
        reporter = DORAReporter()  # no console arg
        assert reporter.console is not None

    def test_overall_band_in_output(self):
        buf = StringIO()
        console = Console(file=buf, highlight=False, markup=False)
        reporter = DORAReporter(console=console)
        report = _make_report(overall_band=PerformanceBand.ELITE)
        reporter.print_report(report)
        assert "Elite" in buf.getvalue()

    def test_team_name_in_output(self):
        buf = StringIO()
        console = Console(file=buf, highlight=False, markup=False)
        reporter = DORAReporter(console=console)
        report = _make_report(team="my-squad")
        reporter.print_report(report)
        assert "my-squad" in buf.getvalue()


class TestToMarkdown:
    def test_contains_team_name(self):
        r = _make_report(team="sre-team")
        md = DORAReporter().to_markdown(r)
        assert "sre-team" in md

    def test_contains_overall_band(self):
        r = _make_report(overall_band=PerformanceBand.MEDIUM)
        md = DORAReporter().to_markdown(r)
        assert "Medium" in md

    def test_contains_table_headers(self):
        r = _make_report()
        md = DORAReporter().to_markdown(r)
        assert "| Metric |" in md

    def test_contains_all_four_metrics(self):
        r = _make_report()
        md = DORAReporter().to_markdown(r)
        assert "Deployment Frequency" in md
        assert "Lead Time" in md
        assert "Change Failure Rate" in md
        assert "Mean Time to Recovery" in md

    def test_no_lead_time_data_shows_no_data(self):
        r = _make_report(lt_sample_size=0, lt_avg=0.0, lt_band=PerformanceBand.LOW)
        md = DORAReporter().to_markdown(r)
        assert "No data" in md

    def test_no_incidents_shows_no_incidents(self):
        r = _make_report(total_incidents=0, mttr_avg=0.0)
        md = DORAReporter().to_markdown(r)
        assert "No incidents" in md

    def test_contains_deployment_count(self):
        r = _make_report(total_deployments=25)
        md = DORAReporter().to_markdown(r)
        assert "25" in md

    def test_window_days_in_output(self):
        r = _make_report(window_days=14)
        md = DORAReporter().to_markdown(r)
        assert "14" in md


class TestToJson:
    def test_valid_json(self):
        r = _make_report()
        raw = DORAReporter().to_json(r)
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_json_contains_team(self):
        r = _make_report(team="json-team")
        raw = DORAReporter().to_json(r)
        parsed = json.loads(raw)
        assert parsed["team"] == "json-team"

    def test_json_contains_all_metric_keys(self):
        r = _make_report()
        parsed = json.loads(DORAReporter().to_json(r))
        assert "deployment_frequency" in parsed
        assert "lead_time" in parsed
        assert "change_failure_rate" in parsed
        assert "mttr" in parsed

    def test_json_roundtrip_preserves_window_days(self):
        r = _make_report(window_days=7)
        parsed = json.loads(DORAReporter().to_json(r))
        assert parsed["window_days"] == 7
