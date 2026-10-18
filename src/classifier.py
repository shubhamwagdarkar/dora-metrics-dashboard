"""DORA performance band classifier.

Thresholds based on the DORA 2023 State of DevOps Report.
"""

from src.models import PerformanceBand


class DORAClassifier:
    """Classifies DORA metric values into Elite/High/Medium/Low performance bands."""

    def classify_deployment_frequency(self, deployments_per_day: float) -> PerformanceBand:
        """Elite: >=1/day | High: >=1/week | Medium: >=1/month | Low: <1/month."""
        if deployments_per_day >= 1.0:
            return PerformanceBand.ELITE
        if deployments_per_day >= 1 / 7:
            return PerformanceBand.HIGH
        if deployments_per_day >= 1 / 30:
            return PerformanceBand.MEDIUM
        return PerformanceBand.LOW

    def classify_lead_time(self, avg_hours: float) -> PerformanceBand:
        """Elite: <1hr | High: <1day | Medium: <1week | Low: >=1week."""
        if avg_hours < 1.0:
            return PerformanceBand.ELITE
        if avg_hours < 24.0:
            return PerformanceBand.HIGH
        if avg_hours < 168.0:
            return PerformanceBand.MEDIUM
        return PerformanceBand.LOW

    def classify_change_failure_rate(self, rate_pct: float) -> PerformanceBand:
        """Elite: <5% | High: <10% | Medium: <15% | Low: >=15%."""
        if rate_pct < 5.0:
            return PerformanceBand.ELITE
        if rate_pct < 10.0:
            return PerformanceBand.HIGH
        if rate_pct < 15.0:
            return PerformanceBand.MEDIUM
        return PerformanceBand.LOW

    def classify_mttr(self, avg_hours: float) -> PerformanceBand:
        """Elite: <1hr | High: <1day | Medium: <1week | Low: >=1week."""
        if avg_hours < 1.0:
            return PerformanceBand.ELITE
        if avg_hours < 24.0:
            return PerformanceBand.HIGH
        if avg_hours < 168.0:
            return PerformanceBand.MEDIUM
        return PerformanceBand.LOW

    def classify_overall(
        self,
        df: PerformanceBand,
        lt: PerformanceBand,
        cfr: PerformanceBand,
        mttr: PerformanceBand,
    ) -> PerformanceBand:
        """Overall band = the lowest (worst) of the four individual bands."""
        order = [
            PerformanceBand.LOW,
            PerformanceBand.MEDIUM,
            PerformanceBand.HIGH,
            PerformanceBand.ELITE,
        ]
        return min([df, lt, cfr, mttr], key=lambda b: order.index(b))
