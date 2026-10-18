"""Sample data loader for demo mode — no API keys required."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.models import Deployment, Incident


def load_sample_data() -> tuple[list[Deployment], list[Incident]]:
    """Return pre-built sample deployments and incidents for the demo command."""
    now = datetime.now(timezone.utc)

    deployments: list[Deployment] = [
        Deployment(
            id="dep-001",
            environment="production",
            deployed_at=now - timedelta(days=1, hours=2),
            commit_sha="a1b2c3d",
            pr_number=201,
            pr_merged_at=now - timedelta(days=1, hours=3),
            first_commit_at=now - timedelta(days=1, hours=18),
            is_failure=False,
        ),
        Deployment(
            id="dep-002",
            environment="production",
            deployed_at=now - timedelta(days=2, hours=5),
            commit_sha="b2c3d4e",
            pr_number=200,
            pr_merged_at=now - timedelta(days=2, hours=6),
            first_commit_at=now - timedelta(days=3, hours=2),
            is_failure=False,
        ),
        Deployment(
            id="dep-003",
            environment="production",
            deployed_at=now - timedelta(days=4, hours=1),
            commit_sha="c3d4e5f",
            pr_number=198,
            pr_merged_at=now - timedelta(days=4, hours=2),
            first_commit_at=now - timedelta(days=4, hours=28),
            is_failure=True,
        ),
        Deployment(
            id="dep-004",
            environment="production",
            deployed_at=now - timedelta(days=5, hours=3),
            commit_sha="d4e5f6a",
            pr_number=197,
            pr_merged_at=now - timedelta(days=5, hours=4),
            first_commit_at=now - timedelta(days=6, hours=10),
            is_failure=False,
        ),
        Deployment(
            id="dep-005",
            environment="production",
            deployed_at=now - timedelta(days=7, hours=2),
            commit_sha="e5f6a7b",
            pr_number=195,
            pr_merged_at=now - timedelta(days=7, hours=3),
            first_commit_at=now - timedelta(days=8, hours=5),
            is_failure=False,
        ),
        Deployment(
            id="dep-006",
            environment="production",
            deployed_at=now - timedelta(days=9, hours=4),
            commit_sha="f6a7b8c",
            pr_number=194,
            pr_merged_at=now - timedelta(days=9, hours=5),
            first_commit_at=now - timedelta(days=10, hours=14),
            is_failure=False,
        ),
        Deployment(
            id="dep-007",
            environment="production",
            deployed_at=now - timedelta(days=11, hours=1),
            commit_sha="a7b8c9d",
            pr_number=192,
            pr_merged_at=now - timedelta(days=11, hours=2),
            first_commit_at=now - timedelta(days=12, hours=20),
            is_failure=False,
        ),
        Deployment(
            id="dep-008",
            environment="production",
            deployed_at=now - timedelta(days=14, hours=3),
            commit_sha="b8c9d0e",
            pr_number=190,
            pr_merged_at=now - timedelta(days=14, hours=4),
            first_commit_at=now - timedelta(days=15, hours=8),
            is_failure=False,
        ),
        Deployment(
            id="dep-009",
            environment="production",
            deployed_at=now - timedelta(days=17, hours=2),
            commit_sha="c9d0e1f",
            pr_number=188,
            pr_merged_at=now - timedelta(days=17, hours=3),
            first_commit_at=now - timedelta(days=18, hours=16),
            is_failure=False,
        ),
        Deployment(
            id="dep-010",
            environment="production",
            deployed_at=now - timedelta(days=20, hours=1),
            commit_sha="d0e1f2a",
            pr_number=186,
            pr_merged_at=now - timedelta(days=20, hours=2),
            first_commit_at=now - timedelta(days=21, hours=12),
            is_failure=False,
        ),
    ]

    incidents: list[Incident] = [
        Incident(
            id="inc-001",
            title="Database connection pool exhausted",
            created_at=now - timedelta(days=4, hours=1, minutes=5),
            resolved_at=now - timedelta(days=4, hours=0, minutes=20),
            severity="high",
        ),
        Incident(
            id="inc-002",
            title="Payment service 502 errors — upstream timeout",
            created_at=now - timedelta(days=10, hours=3),
            resolved_at=now - timedelta(days=10, hours=1),
            severity="high",
        ),
        Incident(
            id="inc-003",
            title="Elevated error rate on /api/v2/orders",
            created_at=now - timedelta(days=15, hours=2),
            resolved_at=now - timedelta(days=15, hours=1, minutes=15),
            severity="low",
        ),
        Incident(
            id="inc-004",
            title="Search service degraded — Elasticsearch OOM",
            created_at=now - timedelta(days=22, hours=5),
            resolved_at=now - timedelta(days=22, hours=3, minutes=30),
            severity="high",
        ),
    ]

    return deployments, incidents
