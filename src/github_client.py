"""GitHub API client — fetches deployments and PR lead time data."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from src.models import Deployment

logger = logging.getLogger(__name__)


class GitHubClient:
    """Thin wrapper around the GitHub REST API for DORA data collection."""

    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.token = token
        self.owner = owner
        self.repo = repo
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def _get_deployment_status(self, deployment_id: int) -> str:
        """Return the latest state string for a deployment ('success', 'failure', etc.)."""
        resp = self.session.get(
            f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/deployments/{deployment_id}/statuses"
        )
        resp.raise_for_status()
        statuses = resp.json()
        if not statuses:
            return "unknown"
        return statuses[0]["state"]  # GitHub returns newest-first

    def get_deployments(
        self, environment: str = "production", since_days: int = 30
    ) -> list[Deployment]:
        """Fetch deployments from GitHub for the given environment and time window."""
        since = datetime.now(timezone.utc) - timedelta(days=since_days)
        deployments: list[Deployment] = []
        page = 1

        while True:
            resp = self.session.get(
                f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/deployments",
                params={"environment": environment, "per_page": 100, "page": page},
            )
            resp.raise_for_status()
            data = resp.json()

            if not data:
                break

            stop = False
            for d in data:
                created_at = datetime.fromisoformat(
                    d["created_at"].replace("Z", "+00:00")
                )
                if created_at < since:
                    stop = True
                    break

                state = self._get_deployment_status(d["id"])
                is_failure = state in ("failure", "error")

                deployments.append(
                    Deployment(
                        id=str(d["id"]),
                        environment=d["environment"],
                        deployed_at=created_at,
                        commit_sha=d["sha"],
                        is_failure=is_failure,
                    )
                )

            if stop:
                break
            page += 1

        return deployments

    def enrich_with_pr_data(self, deployments: list[Deployment]) -> list[Deployment]:
        """Enrich deployments with PR number and first-commit timestamp for lead time."""
        for dep in deployments:
            try:
                pr_resp = self.session.get(
                    f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/commits/{dep.commit_sha}/pulls",
                    headers={"Accept": "application/vnd.github.groot-preview+json"},
                )
                if not pr_resp.ok or not pr_resp.json():
                    continue

                pr = pr_resp.json()[0]
                merged_at = pr.get("merged_at")
                if not merged_at:
                    continue

                dep.pr_number = pr["number"]
                dep.pr_merged_at = datetime.fromisoformat(
                    merged_at.replace("Z", "+00:00")
                )

                commits_resp = self.session.get(
                    f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/pulls/{pr['number']}/commits"
                )
                if not commits_resp.ok or not commits_resp.json():
                    continue

                first_commit = commits_resp.json()[0]
                commit_date = first_commit["commit"]["committer"]["date"]
                dep.first_commit_at = datetime.fromisoformat(
                    commit_date.replace("Z", "+00:00")
                )

            except Exception as exc:
                logger.warning("Failed to enrich deployment %s: %s", dep.id, exc)

        return deployments
