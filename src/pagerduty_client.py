"""PagerDuty API client — fetches incidents for MTTR calculation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from src.models import Incident

logger = logging.getLogger(__name__)


class PagerDutyClient:
    """Thin wrapper around the PagerDuty REST API v2."""

    BASE_URL = "https://api.pagerduty.com"

    def __init__(
        self,
        api_key: str,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Token token={api_key}",
                "Accept": "application/vnd.pagerduty+json;version=2",
                "Content-Type": "application/json",
            }
        )

    def get_incidents(self, since_days: int = 30) -> list[Incident]:
        """Fetch all incidents (all statuses) within the given time window."""
        since = (
            datetime.now(timezone.utc) - timedelta(days=since_days)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        incidents: list[Incident] = []
        offset = 0
        limit = 100

        while True:
            resp = self.session.get(
                f"{self.BASE_URL}/incidents",
                params={
                    "since": since,
                    "limit": limit,
                    "offset": offset,
                    "statuses[]": ["triggered", "acknowledged", "resolved"],
                },
            )
            resp.raise_for_status()
            data = resp.json()

            for inc in data.get("incidents", []):
                created_at = datetime.fromisoformat(
                    inc["created_at"].replace("Z", "+00:00")
                )
                resolved_at: Optional[datetime] = None
                if inc.get("resolved_at"):
                    resolved_at = datetime.fromisoformat(
                        inc["resolved_at"].replace("Z", "+00:00")
                    )

                incidents.append(
                    Incident(
                        id=inc["id"],
                        title=inc["title"],
                        created_at=created_at,
                        resolved_at=resolved_at,
                        severity=inc.get("urgency", "high"),
                    )
                )

            if not data.get("more", False):
                break
            offset += limit

        return incidents
