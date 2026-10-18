"""Pydantic models for DORA metrics dashboard."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PerformanceBand(str, Enum):
    ELITE = "Elite"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Deployment(BaseModel):
    """Represents a single deployment event."""

    id: str
    environment: str
    deployed_at: datetime
    commit_sha: str
    is_failure: bool = False
    pr_number: Optional[int] = None
    pr_merged_at: Optional[datetime] = None
    first_commit_at: Optional[datetime] = None


class Incident(BaseModel):
    """Represents a production incident."""

    id: str
    title: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    severity: str = "high"
    triggered_by_deployment: Optional[str] = None


class DeploymentFrequencyMetric(BaseModel):
    """Deployment Frequency DORA metric."""

    total_deployments: int
    days_in_window: int
    deployments_per_day: float
    deployments_per_week: float
    band: PerformanceBand


class LeadTimeMetric(BaseModel):
    """Lead Time for Changes DORA metric."""

    avg_lead_time_hours: float
    median_lead_time_hours: float
    p95_lead_time_hours: float
    sample_size: int
    band: PerformanceBand


class ChangeFailureRateMetric(BaseModel):
    """Change Failure Rate DORA metric."""

    total_deployments: int
    failed_deployments: int
    failure_rate_pct: float
    band: PerformanceBand


class MTTRMetric(BaseModel):
    """Mean Time to Recovery DORA metric."""

    total_incidents: int
    avg_mttr_hours: float
    median_mttr_hours: float
    band: PerformanceBand


class DORAReport(BaseModel):
    """Full DORA metrics report for a team over a time window."""

    team: str
    window_days: int
    generated_at: datetime
    deployment_frequency: DeploymentFrequencyMetric
    lead_time: LeadTimeMetric
    change_failure_rate: ChangeFailureRateMetric
    mttr: MTTRMetric
    overall_band: PerformanceBand
