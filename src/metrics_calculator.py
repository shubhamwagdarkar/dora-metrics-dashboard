"""DORA metrics calculator — computes the four key metrics from raw data."""

from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean, median
from typing import Optional

from src.classifier import DORAClassifier
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


class MetricsCalculator:
    """Computes DORA metrics from lists of Deployment and Incident objects."""

    def __init__(self, classifier: Optional[DORAClassifier] = None) -> None:
        self.classifier = classifier or DORAClassifier()

    def compute_deployment_frequency(
        self, deployments: list[Deployment], window_days: int
    ) -> DeploymentFrequencyMetric:
        total = len(deployments)
        per_day = total / window_days if window_days > 0 else 0.0
        per_week = per_day * 7
        band = self.classifier.classify_deployment_frequency(per_day)
        return DeploymentFrequencyMetric(
            total_deployments=total,
            days_in_window=window_days,
            deployments_per_day=round(per_day, 2),
            deployments_per_week=round(per_week, 2),
            band=band,
        )

    def compute_lead_time(self, deployments: list[Deployment]) -> LeadTimeMetric:
        """Lead time = time from first commit in PR to deployment to production."""
        lead_times: list[float] = []
        for dep in deployments:
            if dep.first_commit_at and dep.deployed_at:
                hours = (dep.deployed_at - dep.first_commit_at).total_seconds() / 3600
                if hours >= 0:
                    lead_times.append(hours)

        if not lead_times:
            return LeadTimeMetric(
                avg_lead_time_hours=0.0,
                median_lead_time_hours=0.0,
                p95_lead_time_hours=0.0,
                sample_size=0,
                band=PerformanceBand.LOW,
            )

        sorted_times = sorted(lead_times)
        p95_idx = min(int(len(sorted_times) * 0.95), len(sorted_times) - 1)
        p95 = sorted_times[p95_idx]
        avg = mean(lead_times)
        med = median(lead_times)
        band = self.classifier.classify_lead_time(avg)

        return LeadTimeMetric(
            avg_lead_time_hours=round(avg, 2),
            median_lead_time_hours=round(med, 2),
            p95_lead_time_hours=round(p95, 2),
            sample_size=len(lead_times),
            band=band,
        )

    def compute_change_failure_rate(
        self, deployments: list[Deployment]
    ) -> ChangeFailureRateMetric:
        total = len(deployments)
        failed = sum(1 for d in deployments if d.is_failure)
        rate = (failed / total * 100) if total > 0 else 0.0
        band = self.classifier.classify_change_failure_rate(rate)
        return ChangeFailureRateMetric(
            total_deployments=total,
            failed_deployments=failed,
            failure_rate_pct=round(rate, 2),
            band=band,
        )

    def compute_mttr(self, incidents: list[Incident]) -> MTTRMetric:
        resolved = [i for i in incidents if i.resolved_at is not None]
        total = len(incidents)

        if not resolved:
            return MTTRMetric(
                total_incidents=total,
                avg_mttr_hours=0.0,
                median_mttr_hours=0.0,
                band=PerformanceBand.LOW,
            )

        durations = [
            (i.resolved_at - i.created_at).total_seconds() / 3600  # type: ignore[operator]
            for i in resolved
        ]
        avg = mean(durations)
        med = median(durations)
        band = self.classifier.classify_mttr(avg)

        return MTTRMetric(
            total_incidents=total,
            avg_mttr_hours=round(avg, 2),
            median_mttr_hours=round(med, 2),
            band=band,
        )

    def compute_report(
        self,
        team: str,
        deployments: list[Deployment],
        incidents: list[Incident],
        window_days: int,
    ) -> DORAReport:
        df_metric = self.compute_deployment_frequency(deployments, window_days)
        lt_metric = self.compute_lead_time(deployments)
        cfr_metric = self.compute_change_failure_rate(deployments)
        mttr_metric = self.compute_mttr(incidents)
        overall = self.classifier.classify_overall(
            df_metric.band, lt_metric.band, cfr_metric.band, mttr_metric.band
        )
        return DORAReport(
            team=team,
            window_days=window_days,
            generated_at=datetime.now(timezone.utc),
            deployment_frequency=df_metric,
            lead_time=lt_metric,
            change_failure_rate=cfr_metric,
            mttr=mttr_metric,
            overall_band=overall,
        )
