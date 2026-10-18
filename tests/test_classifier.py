"""Tests for src/classifier.py — 24 tests."""

import pytest

from src.classifier import DORAClassifier
from src.models import PerformanceBand


@pytest.fixture
def clf():
    return DORAClassifier()


# ── Deployment Frequency ───────────────────────────────────────────────────────

class TestDeploymentFrequency:
    def test_multiple_per_day_is_elite(self, clf):
        assert clf.classify_deployment_frequency(3.0) == PerformanceBand.ELITE

    def test_exactly_one_per_day_is_elite(self, clf):
        assert clf.classify_deployment_frequency(1.0) == PerformanceBand.ELITE

    def test_one_per_week_is_high(self, clf):
        # 1/7 ≈ 0.142857 per day
        assert clf.classify_deployment_frequency(1 / 7) == PerformanceBand.HIGH

    def test_between_week_and_day_is_high(self, clf):
        assert clf.classify_deployment_frequency(0.5) == PerformanceBand.HIGH

    def test_one_per_month_is_medium(self, clf):
        # 1/30 per day
        assert clf.classify_deployment_frequency(1 / 30) == PerformanceBand.MEDIUM

    def test_less_than_monthly_is_low(self, clf):
        assert clf.classify_deployment_frequency(0.01) == PerformanceBand.LOW

    def test_zero_is_low(self, clf):
        assert clf.classify_deployment_frequency(0.0) == PerformanceBand.LOW


# ── Lead Time ──────────────────────────────────────────────────────────────────

class TestLeadTime:
    def test_under_one_hour_is_elite(self, clf):
        assert clf.classify_lead_time(0.5) == PerformanceBand.ELITE

    def test_exactly_one_hour_is_high(self, clf):
        assert clf.classify_lead_time(1.0) == PerformanceBand.HIGH

    def test_twelve_hours_is_high(self, clf):
        assert clf.classify_lead_time(12.0) == PerformanceBand.HIGH

    def test_exactly_one_day_is_medium(self, clf):
        assert clf.classify_lead_time(24.0) == PerformanceBand.MEDIUM

    def test_three_days_is_medium(self, clf):
        assert clf.classify_lead_time(72.0) == PerformanceBand.MEDIUM

    def test_exactly_one_week_is_low(self, clf):
        assert clf.classify_lead_time(168.0) == PerformanceBand.LOW

    def test_ten_days_is_low(self, clf):
        assert clf.classify_lead_time(240.0) == PerformanceBand.LOW


# ── Change Failure Rate ────────────────────────────────────────────────────────

class TestChangeFailureRate:
    def test_zero_pct_is_elite(self, clf):
        assert clf.classify_change_failure_rate(0.0) == PerformanceBand.ELITE

    def test_under_5_pct_is_elite(self, clf):
        assert clf.classify_change_failure_rate(4.9) == PerformanceBand.ELITE

    def test_exactly_5_pct_is_high(self, clf):
        assert clf.classify_change_failure_rate(5.0) == PerformanceBand.HIGH

    def test_7_pct_is_high(self, clf):
        assert clf.classify_change_failure_rate(7.0) == PerformanceBand.HIGH

    def test_exactly_10_pct_is_medium(self, clf):
        assert clf.classify_change_failure_rate(10.0) == PerformanceBand.MEDIUM

    def test_exactly_15_pct_is_low(self, clf):
        assert clf.classify_change_failure_rate(15.0) == PerformanceBand.LOW

    def test_20_pct_is_low(self, clf):
        assert clf.classify_change_failure_rate(20.0) == PerformanceBand.LOW


# ── MTTR ───────────────────────────────────────────────────────────────────────

class TestMTTR:
    def test_under_one_hour_is_elite(self, clf):
        assert clf.classify_mttr(0.5) == PerformanceBand.ELITE

    def test_exactly_one_hour_is_high(self, clf):
        assert clf.classify_mttr(1.0) == PerformanceBand.HIGH

    def test_twelve_hours_is_high(self, clf):
        assert clf.classify_mttr(12.0) == PerformanceBand.HIGH

    def test_one_week_is_low(self, clf):
        assert clf.classify_mttr(168.0) == PerformanceBand.LOW


# ── Overall ────────────────────────────────────────────────────────────────────

class TestOverallClassification:
    def test_all_elite_gives_elite(self, clf):
        result = clf.classify_overall(
            PerformanceBand.ELITE,
            PerformanceBand.ELITE,
            PerformanceBand.ELITE,
            PerformanceBand.ELITE,
        )
        assert result == PerformanceBand.ELITE

    def test_one_low_drags_down_to_low(self, clf):
        result = clf.classify_overall(
            PerformanceBand.ELITE,
            PerformanceBand.HIGH,
            PerformanceBand.MEDIUM,
            PerformanceBand.LOW,
        )
        assert result == PerformanceBand.LOW

    def test_all_low_gives_low(self, clf):
        result = clf.classify_overall(
            PerformanceBand.LOW,
            PerformanceBand.LOW,
            PerformanceBand.LOW,
            PerformanceBand.LOW,
        )
        assert result == PerformanceBand.LOW

    def test_high_medium_mix_gives_medium(self, clf):
        result = clf.classify_overall(
            PerformanceBand.HIGH,
            PerformanceBand.HIGH,
            PerformanceBand.MEDIUM,
            PerformanceBand.HIGH,
        )
        assert result == PerformanceBand.MEDIUM
