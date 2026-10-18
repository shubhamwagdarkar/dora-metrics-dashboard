"""Tests for src/github_client.py — 20 tests."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from src.github_client import GitHubClient
from src.models import Deployment

NOW = datetime.now(timezone.utc)


def _make_response(data, status_code: int = 200, ok: bool = True) -> MagicMock:
    resp = MagicMock()
    resp.ok = ok
    resp.status_code = status_code
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


def _make_error_response() -> MagicMock:
    resp = MagicMock()
    resp.ok = False
    resp.status_code = 500
    resp.raise_for_status.side_effect = Exception("HTTP 500")
    return resp


def _deployment_payload(id: int = 1, sha: str = "abc123",
                        environment: str = "production",
                        created_at: datetime | None = None) -> dict:
    ts = (created_at or NOW).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"id": id, "sha": sha, "environment": environment, "created_at": ts}


@pytest.fixture
def mock_session() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(mock_session) -> GitHubClient:
    return GitHubClient("test-token", "my-org", "my-repo", session=mock_session)


# ── get_deployments ────────────────────────────────────────────────────────────

class TestGetDeployments:
    def test_empty_response_returns_empty_list(self, client, mock_session):
        mock_session.get.side_effect = [_make_response([])]
        result = client.get_deployments()
        assert result == []

    def test_single_deployment_returned(self, client, mock_session):
        dep = _deployment_payload(id=1, sha="abc", environment="production")
        mock_session.get.side_effect = [
            _make_response([dep]),        # deployments page 1
            _make_response([{"state": "success"}]),  # statuses for dep 1
            _make_response([]),            # deployments page 2 (empty)
        ]
        result = client.get_deployments(since_days=30)
        assert len(result) == 1
        assert result[0].commit_sha == "abc"
        assert result[0].is_failure is False

    def test_failure_status_marked(self, client, mock_session):
        dep = _deployment_payload(id=2)
        mock_session.get.side_effect = [
            _make_response([dep]),
            _make_response([{"state": "failure"}]),
            _make_response([]),
        ]
        result = client.get_deployments(since_days=30)
        assert result[0].is_failure is True

    def test_error_status_marked_as_failure(self, client, mock_session):
        dep = _deployment_payload(id=3)
        mock_session.get.side_effect = [
            _make_response([dep]),
            _make_response([{"state": "error"}]),
            _make_response([]),
        ]
        result = client.get_deployments(since_days=30)
        assert result[0].is_failure is True

    def test_old_deployment_filtered_out(self, client, mock_session):
        old_ts = NOW - timedelta(days=40)
        dep = _deployment_payload(created_at=old_ts)
        mock_session.get.side_effect = [_make_response([dep])]
        result = client.get_deployments(since_days=30)
        assert result == []

    def test_pagination_two_pages(self, client, mock_session):
        dep1 = _deployment_payload(id=1, sha="aaa")
        dep2 = _deployment_payload(id=2, sha="bbb")
        mock_session.get.side_effect = [
            _make_response([dep1]),                   # page 1
            _make_response([{"state": "success"}]),   # statuses dep1
            _make_response([dep2]),                   # page 2
            _make_response([{"state": "success"}]),   # statuses dep2
            _make_response([]),                       # page 3 (empty)
        ]
        result = client.get_deployments(since_days=30)
        assert len(result) == 2

    def test_stops_pagination_on_empty_page(self, client, mock_session):
        mock_session.get.side_effect = [_make_response([])]
        result = client.get_deployments()
        assert result == []

    def test_http_error_raises(self, client, mock_session):
        mock_session.get.side_effect = [_make_error_response()]
        with pytest.raises(Exception):
            client.get_deployments()

    def test_no_statuses_returns_unknown_not_failure(self, client, mock_session):
        dep = _deployment_payload(id=5)
        mock_session.get.side_effect = [
            _make_response([dep]),
            _make_response([]),   # empty statuses → unknown
            _make_response([]),   # page 2
        ]
        result = client.get_deployments(since_days=30)
        assert result[0].is_failure is False

    def test_environment_passed_in_params(self, client, mock_session):
        mock_session.get.side_effect = [_make_response([])]
        client.get_deployments(environment="staging", since_days=30)
        call_kwargs = mock_session.get.call_args
        assert call_kwargs[1]["params"]["environment"] == "staging"

    def test_deployment_id_stored_as_string(self, client, mock_session):
        dep = _deployment_payload(id=42)
        mock_session.get.side_effect = [
            _make_response([dep]),
            _make_response([{"state": "success"}]),
            _make_response([]),
        ]
        result = client.get_deployments(since_days=30)
        assert result[0].id == "42"


# ── enrich_with_pr_data ────────────────────────────────────────────────────────

class TestEnrichWithPRData:
    def _make_client_with_session(self) -> tuple[GitHubClient, MagicMock]:
        sess = MagicMock()
        return GitHubClient("tok", "org", "repo", session=sess), sess

    def _base_deployment(self) -> Deployment:
        return Deployment(
            id="dep-1", environment="production",
            deployed_at=NOW, commit_sha="sha123",
        )

    def test_enriches_pr_number_and_first_commit(self):
        client, sess = self._make_client_with_session()
        dep = self._base_deployment()
        merged_at = (NOW - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        first_commit_ts = (NOW - timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

        sess.get.side_effect = [
            _make_response([{"number": 99, "merged_at": merged_at}]),  # commits/pulls
            _make_response([{  # pull commits
                "commit": {"committer": {"date": first_commit_ts}}
            }]),
        ]
        result = client.enrich_with_pr_data([dep])
        assert result[0].pr_number == 99
        assert result[0].first_commit_at is not None

    def test_no_pr_skips_enrichment(self):
        client, sess = self._make_client_with_session()
        dep = self._base_deployment()
        sess.get.side_effect = [_make_response([])]  # no PRs
        result = client.enrich_with_pr_data([dep])
        assert result[0].pr_number is None
        assert result[0].first_commit_at is None

    def test_pr_not_merged_skips_enrichment(self):
        client, sess = self._make_client_with_session()
        dep = self._base_deployment()
        sess.get.side_effect = [
            _make_response([{"number": 5, "merged_at": None}])
        ]
        result = client.enrich_with_pr_data([dep])
        assert result[0].pr_number is None

    def test_empty_commits_list_skips_first_commit(self):
        client, sess = self._make_client_with_session()
        dep = self._base_deployment()
        merged_at = (NOW - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        sess.get.side_effect = [
            _make_response([{"number": 10, "merged_at": merged_at}]),
            _make_response([]),  # empty commits
        ]
        result = client.enrich_with_pr_data([dep])
        assert result[0].pr_number == 10
        assert result[0].first_commit_at is None

    def test_returns_same_count_as_input(self):
        client, sess = self._make_client_with_session()
        deps = [
            Deployment(id=str(i), environment="prod", deployed_at=NOW, commit_sha=f"s{i}")
            for i in range(3)
        ]
        sess.get.side_effect = [_make_response([])] * 3
        result = client.enrich_with_pr_data(deps)
        assert len(result) == 3

    def test_api_failure_does_not_raise(self):
        client, sess = self._make_client_with_session()
        dep = self._base_deployment()
        sess.get.side_effect = [Exception("network error")]
        result = client.enrich_with_pr_data([dep])
        assert len(result) == 1
        assert result[0].first_commit_at is None
