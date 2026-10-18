"""Tests for src/metrics_calculator.py — 26 tests."""

from datetime import datetime, timedelta, timezone

import pytest

from src.metrics_calculator import MetricsCalculator
from src.models import Deployment, Incident, PerformanceBand

NOW = datetime.now(timezone.utc)


def make_dep(
    id: str = "d1",
    deployed_at: datetime = NOW,
    first_commit_at: datetime | None = None,
    is_failure: bool = False,
) -> Deployment:
    return Deployment(
        id=id,
        environment="production",
        deployed_at=deployed_at,
        commit_sha="abc",
        is_failure=is_failure,
        first_commit_at=first_commit_at,
    )


def make_inc(
    id: str = "i1",
    created_at: datetime = NOW,
    resolved_at: datetime | None = None,
) -> Incident:
    return Incident(id=id, title="Test", created_at=created_at, resolved_at=resolved_at)


@pytest.fixture
def calc():
    return MetricsCalculator()


# ── Deployment Frequency ───────────────────────────────────────────────────────

class TestDeploymentFrequency:
    def test_empty_deployments(self, calc):
        m = calc.compute_deployment_frequency([], 30)
        assert m.total_deployments == 0
        assert m.deployments_per_day == 0.0
        assert m.band == PerformanceBand.LOW

    def test_thirty_deploys_in_thirty_days_is_elite(self, calc):
        deps = [make_dep(id=str(i)) for i in range(30)]
        m = calc.compute_deployment_frequency(deps, 30)
        assert m.deployments_per_day == 1.0
        assert m.band == PerformanceBand.ELITE

    def test_total_deployments_count(self, calc):
        deps = [make_dep(id=str(i)) for i in range(7)]
        m = calc.compute_deployment_frequency(deps, 30)
        assert m.total_deployments == 7

    def test_per_week_is_seven_times_per_day(self, calc):
        deps = [make_dep(id=str(i)) for i in range(30)]
        m = calc.compute_deployment_frequency(deps, 30)
        assert round(m.deployments_per_week, 1) == round(m.deployments_per_day * 7, 1)

    def test_zero_window_days_does_not_raise(self, calc):
        m = calc.compute_deployment_frequency([], 0)
        assert m.deployments_per_day == 0.0

    def test_low_frequency_band(self, calc):
        deps = [make_dep()]
        m = calc.compute_deployment_frequency(deps, 365)
        assert m.band == PerformanceBand.LOW


# ── Lead Time ──────────────────────────────────────────────────────────────────

class TestLeadTime:
    def test_no_first_commit_gives_empty_sample(self, calc):
        deps = [make_dep()]
        m = calc.compute_lead_time(deps)
        assert m.sample_size == 0
        assert m.avg_lead_time_hours == 0.0

    def test_single_known_lead_time(self, calc):
        first = NOW - timedelta(hours=10)
        dep = make_dep(deployed_at=NOW, first_commit_at=first)
        m = calc.compute_lead_time([dep])
        assert m.avg_lead_time_hours == 10.0
        assert m.sample_size == 1

    def test_multiple_deployments_avg(self, calc):
        dep1 = make_dep(id="a", deployed_at=NOW,
                        first_commit_at=NOW - timedelta(hours=10))
        dep2 = make_dep(id="b", deployed_at=NOW,
                        first_commit_at=NOW - timedelta(hours=20))
        m = calc.compute_lead_time([dep1, dep2])
        assert m.avg_lead_time_hours == 15.0
        assert m.sample_size == 2

    def test_negative_lead_time_excluded(self, calc):
        # first_commit_at AFTER deployed_at → negative → excluded
        dep = make_dep(
            deployed_at=NOW - timedelta(hours=5),
            first_commit_at=NOW,
        )
        m = calc.compute_lead_time([dep])
        assert m.sample_size == 0

    def test_p95_single_element(self, calc):
        dep = make_dep(deployed_at=NOW, first_commit_at=NOW - timedelta(hours=8))
        m = calc.compute_lead_time([dep])
        assert m.p95_lead_time_hours == 8.0

    def test_p95_multiple_elements(self, calc):
        deps = [
            make_dep(id=str(i), deployed_at=NOW,
                     first_commit_at=NOW - timedelta(hours=float(i + 1)))
            for i in range(20)
        ]
        m = calc.compute_lead_time(deps)
        # p95_idx = int(20 * 0.95) = 19, sorted list is [1,2,...,20], index 19 = 20h
        assert m.p95_lead_time_hours == 20.0

    def test_elite_band_for_sub_hour(self, calc):
        dep = make_dep(deployed_at=NOW, first_commit_at=NOW - timedelta(minutes=30))
        m = calc.compute_lead_time([dep])
        assert m.band == PerformanceBand.ELITE


# ── Change Failure Rate ────────────────────────────────────────────────────────

class TestChangeFailureRate:
    def test_no_failures(self, calc):
        deps = [make_dep(id=str(i)) for i in range(10)]
        m = calc.compute_change_failure_rate(deps)
        assert m.failure_rate_pct == 0.0
        assert m.band == PerformanceBand.ELITE

    def test_all_failures(self, calc):
        deps = [make_dep(id=str(i), is_failure=True) for i in range(5)]
        m = calc.compute_change_failure_rate(deps)
        assert m.failure_rate_pct == 100.0
        assert m.band == PerformanceBand.LOW

    def test_partial_failures(self, calc):
        deps = [
            make_dep(id="a", is_failure=False),
            make_dep(id="b", is_failure=False),
            make_dep(id="c", is_failure=True),
        ]
        m = calc.compute_change_failure_rate(deps)
        assert round(m.failure_rate_pct, 2) == round(100 / 3, 2)

    def test_empty_deployments(self, calc):
        m = calc.compute_change_failure_rate([])
        assert m.failure_rate_pct == 0.0
        assert m.total_deployments == 0

    def test_failed_deployments_count(self, calc):
        deps = [make_dep(id=str(i), is_failure=(i % 2 == 0)) for i in range(10)]
        m = calc.compute_change_failure_rate(deps)
        assert m.failed_deployments == 5


# ── MTTR ───────────────────────────────────────────────────────────────────────

class TestMTTR:
    def test_no_incidents(self, calc):
        m = calc.compute_mttr([])
        assert m.total_incidents == 0
        assert m.avg_mttr_hours == 0.0

    def test_no_resolved_incidents(self, calc):
        inc = make_inc()  # resolved_at=None
        m = calc.compute_mttr([inc])
        assert m.total_incidents == 1
        assert m.avg_mttr_hours == 0.0

    def test_single_resolved_incident(self, calc):
        inc = make_inc(
            created_at=NOW - timedelta(hours=2),
            resolved_at=NOW,
        )
        m = calc.compute_mttr([inc])
        assert m.avg_mttr_hours == 2.0

    def test_multiple_incidents_avg(self, calc):
        inc1 = make_inc(id="i1",
                        created_at=NOW - timedelta(hours=2), resolved_at=NOW)
        inc2 = make_inc(id="i2",
                        created_at=NOW - timedelta(hours=4), resolved_at=NOW)
        m = calc.compute_mttr([inc1, inc2])
        assert m.avg_mttr_hours == 3.0

    def test_unresolved_excluded_from_avg(self, calc):
        resolved = make_inc(id="r",
                            created_at=NOW - timedelta(hours=2), resolved_at=NOW)
        unresolved = make_inc(id="u")  # resolved_at=None
        m = calc.compute_mttr([resolved, unresolved])
        assert m.avg_mttr_hours == 2.0
        assert m.total_incidents == 2


# ── compute_report ─────────────────────────────────────────────────────────────

class TestComputeReport:
    def test_returns_dora_report(self, calc):
        from src.models import DORAReport
        r = calc.compute_report("my-team", [], [], 30)
        assert isinstance(r, DORAReport)

    def test_team_and_window_set(self, calc):
        r = calc.compute_report("my-team", [], [], 14)
        assert r.team == "my-team"
        assert r.window_days == 14

    def test_overall_band_worst_metric(self, calc):
        # 1 deployment in 30 days → MEDIUM; no lead time data → LOW; no failures → ELITE; no incidents → LOW
        deps = [make_dep()]
        r = calc.compute_report("t", deps, [], 30)
        assert r.overall_band == PerformanceBand.LOW  # dragged by lead time (no data) and MTTR

    def test_all_four_metrics_present(self, calc):
        r = calc.compute_report("t", [], [], 30)
        assert r.deployment_frequency is not None
        assert r.lead_time is not None
        assert r.change_failure_rate is not None
        assert r.mttr is not None

    def test_generated_at_is_recent(self, calc):
        from datetime import timezone
        r = calc.compute_report("t", [], [], 30)
        delta = datetime.now(timezone.utc) - r.generated_at
        assert delta.total_seconds() < 5
