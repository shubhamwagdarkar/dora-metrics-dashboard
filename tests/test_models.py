"""Tests for src/models.py — 20 tests."""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models import (
    ChangeFailureRateMetric,
    DORAReport,
    Deployment,
    DeploymentFrequencyMetric,
    Incident,
    LeadTimeMetric,
    MTTRMetric,
    PerformanceBand,
)

NOW = datetime.now(timezone.utc)


# ── PerformanceBand ────────────────────────────────────────────────────────────

class TestPerformanceBand:
    def test_values(self):
        assert PerformanceBand.ELITE == "Elite"
        assert PerformanceBand.HIGH == "High"
        assert PerformanceBand.MEDIUM == "Medium"
        assert PerformanceBand.LOW == "Low"

    def test_is_str_enum(self):
        assert isinstance(PerformanceBand.ELITE, str)


# ── Deployment ─────────────────────────────────────────────────────────────────

class TestDeployment:
    def test_required_fields(self):
        dep = Deployment(
            id="dep-1",
            environment="production",
            deployed_at=NOW,
            commit_sha="abc123",
        )
        assert dep.id == "dep-1"
        assert dep.environment == "production"
        assert dep.commit_sha == "abc123"

    def test_is_failure_defaults_false(self):
        dep = Deployment(id="d", environment="prod", deployed_at=NOW, commit_sha="x")
        assert dep.is_failure is False

    def test_optional_fields_default_none(self):
        dep = Deployment(id="d", environment="prod", deployed_at=NOW, commit_sha="x")
        assert dep.pr_number is None
        assert dep.pr_merged_at is None
        assert dep.first_commit_at is None

    def test_all_fields_set(self):
        dep = Deployment(
            id="dep-2",
            environment="staging",
            deployed_at=NOW,
            commit_sha="def456",
            is_failure=True,
            pr_number=42,
            pr_merged_at=NOW,
            first_commit_at=NOW,
        )
        assert dep.is_failure is True
        assert dep.pr_number == 42

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            Deployment(environment="prod", deployed_at=NOW, commit_sha="x")  # type: ignore[call-arg]


# ── Incident ───────────────────────────────────────────────────────────────────

class TestIncident:
    def test_resolved_incident(self):
        inc = Incident(id="i-1", title="DB down", created_at=NOW, resolved_at=NOW)
        assert inc.resolved_at == NOW

    def test_unresolved_incident(self):
        inc = Incident(id="i-2", title="Alert", created_at=NOW)
        assert inc.resolved_at is None

    def test_severity_default(self):
        inc = Incident(id="i-3", title="Test", created_at=NOW)
        assert inc.severity == "high"

    def test_triggered_by_deployment_default(self):
        inc = Incident(id="i-4", title="Test", created_at=NOW)
        assert inc.triggered_by_deployment is None


# ── Sub-metrics ────────────────────────────────────────────────────────────────

class TestSubMetrics:
    def test_deployment_frequency_metric(self):
        m = DeploymentFrequencyMetric(
            total_deployments=30,
            days_in_window=30,
            deployments_per_day=1.0,
            deployments_per_week=7.0,
            band=PerformanceBand.ELITE,
        )
        assert m.total_deployments == 30
        assert m.band == PerformanceBand.ELITE

    def test_lead_time_metric_zero_sample(self):
        m = LeadTimeMetric(
            avg_lead_time_hours=0.0,
            median_lead_time_hours=0.0,
            p95_lead_time_hours=0.0,
            sample_size=0,
            band=PerformanceBand.LOW,
        )
        assert m.sample_size == 0

    def test_change_failure_rate_metric(self):
        m = ChangeFailureRateMetric(
            total_deployments=10,
            failed_deployments=1,
            failure_rate_pct=10.0,
            band=PerformanceBand.HIGH,
        )
        assert m.failure_rate_pct == 10.0

    def test_mttr_metric(self):
        m = MTTRMetric(
            total_incidents=5,
            avg_mttr_hours=2.5,
            median_mttr_hours=2.0,
            band=PerformanceBand.HIGH,
        )
        assert m.total_incidents == 5


# ── DORAReport ─────────────────────────────────────────────────────────────────

class TestDORAReport:
    def _make_report(self) -> DORAReport:
        df = DeploymentFrequencyMetric(
            total_deployments=10, days_in_window=30,
            deployments_per_day=0.33, deployments_per_week=2.33,
            band=PerformanceBand.HIGH,
        )
        lt = LeadTimeMetric(
            avg_lead_time_hours=12.0, median_lead_time_hours=10.0,
            p95_lead_time_hours=20.0, sample_size=10,
            band=PerformanceBand.HIGH,
        )
        cfr = ChangeFailureRateMetric(
            total_deployments=10, failed_deployments=1,
            failure_rate_pct=10.0, band=PerformanceBand.HIGH,
        )
        mttr = MTTRMetric(
            total_incidents=3, avg_mttr_hours=3.0,
            median_mttr_hours=2.5, band=PerformanceBand.HIGH,
        )
        return DORAReport(
            team="platform-team",
            window_days=30,
            generated_at=NOW,
            deployment_frequency=df,
            lead_time=lt,
            change_failure_rate=cfr,
            mttr=mttr,
            overall_band=PerformanceBand.HIGH,
        )

    def test_report_creation(self):
        r = self._make_report()
        assert r.team == "platform-team"
        assert r.window_days == 30

    def test_generated_at_is_datetime(self):
        r = self._make_report()
        assert isinstance(r.generated_at, datetime)

    def test_report_serializes_to_dict(self):
        r = self._make_report()
        d = r.model_dump()
        assert d["team"] == "platform-team"
        assert "deployment_frequency" in d

    def test_report_serializes_to_json(self):
        r = self._make_report()
        raw = r.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["team"] == "platform-team"
