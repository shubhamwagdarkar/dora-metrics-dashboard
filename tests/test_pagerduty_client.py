"""Tests for src/pagerduty_client.py — 15 tests."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.pagerduty_client import PagerDutyClient
from src.models import Incident

NOW = datetime.now(timezone.utc)


def _make_response(data: dict, ok: bool = True) -> MagicMock:
    resp = MagicMock()
    resp.ok = ok
    resp.status_code = 200 if ok else 500
    resp.json.return_value = data
    if ok:
        resp.raise_for_status.return_value = None
    else:
        resp.raise_for_status.side_effect = Exception("HTTP 500")
    return resp


def _incident_payload(
    id: str = "P123",
    title: str = "Test incident",
    created_at: datetime | None = None,
    resolved_at: datetime | None = None,
    urgency: str = "high",
) -> dict:
    ts = (created_at or NOW).strftime("%Y-%m-%dT%H:%M:%SZ")
    resolved = resolved_at.strftime("%Y-%m-%dT%H:%M:%SZ") if resolved_at else None
    return {
        "id": id,
        "title": title,
        "created_at": ts,
        "resolved_at": resolved,
        "urgency": urgency,
    }


@pytest.fixture
def mock_session() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(mock_session) -> PagerDutyClient:
    return PagerDutyClient("test-key", session=mock_session)


class TestGetIncidents:
    def test_empty_response_returns_empty_list(self, client, mock_session):
        mock_session.get.return_value = _make_response({"incidents": [], "more": False})
        result = client.get_incidents()
        assert result == []

    def test_single_resolved_incident(self, client, mock_session):
        inc = _incident_payload(
            id="P001",
            created_at=NOW - timedelta(hours=3),
            resolved_at=NOW - timedelta(hours=1),
        )
        mock_session.get.return_value = _make_response({"incidents": [inc], "more": False})
        result = client.get_incidents()
        assert len(result) == 1
        assert result[0].id == "P001"
        assert result[0].resolved_at is not None

    def test_unresolved_incident_has_none_resolved_at(self, client, mock_session):
        inc = _incident_payload(id="P002")  # resolved_at=None
        mock_session.get.return_value = _make_response({"incidents": [inc], "more": False})
        result = client.get_incidents()
        assert result[0].resolved_at is None

    def test_urgency_mapped_to_severity(self, client, mock_session):
        inc = _incident_payload(id="P003", urgency="low")
        mock_session.get.return_value = _make_response({"incidents": [inc], "more": False})
        result = client.get_incidents()
        assert result[0].severity == "low"

    def test_pagination_two_pages(self, client, mock_session):
        page1 = [_incident_payload(id="P1"), _incident_payload(id="P2")]
        page2 = [_incident_payload(id="P3")]
        mock_session.get.side_effect = [
            _make_response({"incidents": page1, "more": True}),
            _make_response({"incidents": page2, "more": False}),
        ]
        result = client.get_incidents()
        assert len(result) == 3

    def test_stops_pagination_when_more_false(self, client, mock_session):
        inc = _incident_payload(id="P1")
        mock_session.get.return_value = _make_response({"incidents": [inc], "more": False})
        result = client.get_incidents()
        assert mock_session.get.call_count == 1

    def test_http_error_raises(self, client, mock_session):
        mock_session.get.return_value = _make_response({}, ok=False)
        with pytest.raises(Exception):
            client.get_incidents()

    def test_since_parameter_passed(self, client, mock_session):
        mock_session.get.return_value = _make_response({"incidents": [], "more": False})
        client.get_incidents(since_days=7)
        call_kwargs = mock_session.get.call_args[1]
        assert "since" in call_kwargs["params"]

    def test_multiple_incidents_correct_count(self, client, mock_session):
        incidents = [_incident_payload(id=f"P{i}") for i in range(5)]
        mock_session.get.return_value = _make_response({"incidents": incidents, "more": False})
        result = client.get_incidents()
        assert len(result) == 5

    def test_correct_auth_header_set(self, mock_session):
        client = PagerDutyClient("my-api-key", session=mock_session)
        mock_session.get.return_value = _make_response({"incidents": [], "more": False})
        client.get_incidents()
        mock_session.headers.update.assert_called_once()
        call_args = mock_session.headers.update.call_args[0][0]
        assert "Token token=my-api-key" in call_args["Authorization"]

    def test_incident_created_at_parsed_correctly(self, client, mock_session):
        ts = NOW - timedelta(days=5)
        inc = _incident_payload(id="P10", created_at=ts)
        mock_session.get.return_value = _make_response({"incidents": [inc], "more": False})
        result = client.get_incidents()
        assert result[0].created_at.tzinfo is not None

    def test_incident_id_preserved(self, client, mock_session):
        inc = _incident_payload(id="PXYZ999")
        mock_session.get.return_value = _make_response({"incidents": [inc], "more": False})
        result = client.get_incidents()
        assert result[0].id == "PXYZ999"

    def test_incident_title_preserved(self, client, mock_session):
        inc = _incident_payload(id="P1", title="Disk full on db-01")
        mock_session.get.return_value = _make_response({"incidents": [inc], "more": False})
        result = client.get_incidents()
        assert result[0].title == "Disk full on db-01"

    def test_missing_urgency_defaults_to_high(self, client, mock_session):
        payload = {
            "id": "P20",
            "title": "No urgency field",
            "created_at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "resolved_at": None,
            # no urgency key
        }
        mock_session.get.return_value = _make_response({"incidents": [payload], "more": False})
        result = client.get_incidents()
        assert result[0].severity == "high"

    def test_offset_incremented_on_pagination(self, client, mock_session):
        page1 = [_incident_payload(id=f"P{i}") for i in range(3)]
        page2 = [_incident_payload(id=f"Q{i}") for i in range(2)]
        mock_session.get.side_effect = [
            _make_response({"incidents": page1, "more": True}),
            _make_response({"incidents": page2, "more": False}),
        ]
        client.get_incidents()
        second_call_params = mock_session.get.call_args_list[1][1]["params"]
        assert second_call_params["offset"] == 100
