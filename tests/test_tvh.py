from __future__ import annotations

import json

import pytest
import requests

from tvheadend.client import TVHeadendClient
from tvheadend.config import clearConfig, configure
from tvheadend.tvh import (
    TVHError,
    activeRecordings,
    allRecordings,
    channelGrid,
    deleteRecording,
    epgEvents,
    epgEventsInWindow,
    epgEventsOnChannel,
    fileMoved,
    sendToTvh,
    statusConnections,
    upcomingRecordings,
)


class DummyResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        json_data: dict[str, object] | None = None,
        text: str = "",
        json_error: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self._json_error = json_error

    def json(self) -> dict[str, object]:
        if self._json_error is not None:
            raise self._json_error
        return self._json_data


@pytest.fixture(autouse=True)
def configured_client() -> None:
    clearConfig()
    configure("tvh.local", "alice", "secret", port=9981, timeout=4.5)
    yield
    clearConfig()


def test_send_to_tvh_uses_configured_connection(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, *, params, auth, timeout: float):
        captured["url"] = url
        captured["params"] = params
        captured["auth"] = auth
        captured["timeout"] = timeout
        return DummyResponse(json_data={"ok": True})

    monkeypatch.setattr("tvheadend.tvh.requests.get", fake_get)

    result = sendToTvh("status/connections", {"limit": 5})

    assert result == {"ok": True}
    assert captured == {
        "url": "http://tvh.local:9981/api/status/connections",
        "params": {"limit": 5},
        "auth": ("alice", "secret"),
        "timeout": 4.5,
    }


def test_send_to_tvh_sanitizes_control_characters_before_json_fallback(
    monkeypatch,
) -> None:
    response = DummyResponse(
        text='{"entries": [\u0019], "total": 1}',
        json_error=json.JSONDecodeError("bad json", "", 0),
    )

    monkeypatch.setattr("tvheadend.tvh.requests.get", lambda *args, **kwargs: response)

    result = sendToTvh("dvr/entry/grid_finished")

    assert result == {"entries": [], "total": 1}


def test_send_to_tvh_wraps_transport_errors(monkeypatch) -> None:
    def fake_get(*args, **kwargs):
        raise requests.RequestException("boom")

    monkeypatch.setattr("tvheadend.tvh.requests.get", fake_get)

    with pytest.raises(TVHError, match="error communicating"):
        sendToTvh("status/connections")


def test_recording_route_helpers_use_expected_routes(monkeypatch) -> None:
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def fake_send(
        cfg, route: str, data: dict[str, object] | None = None
    ) -> dict[str, object]:
        calls.append((cfg.host, route, data))
        if route == "dvr/entry/grid_finished":
            return {"entries": [{"uuid": "uuid-1"}], "total": 1}
        return {"ok": True}

    monkeypatch.setattr("tvheadend.tvh.send_to_tvh", fake_send)

    assert allRecordings() == ([{"uuid": "uuid-1"}], 1)
    deleteRecording("uuid-1")
    fileMoved("/old.ts", "/new.ts")

    assert calls == [
        ("tvh.local", "dvr/entry/grid_finished", {"limit": 9999}),
        ("tvh.local", "dvr/entry/remove", {"uuid": "uuid-1"}),
        ("tvh.local", "dvr/entry/filemoved", {"src": "/old.ts", "dst": "/new.ts"}),
    ]


def test_client_wraps_same_http_behaviour(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, *, params, auth, timeout: float):
        captured["url"] = url
        captured["params"] = params
        captured["auth"] = auth
        captured["timeout"] = timeout
        return DummyResponse(json_data={"entries": [], "total": 0})

    monkeypatch.setattr("tvheadend.tvh.requests.get", fake_get)

    client = TVHeadendClient(configure("tvh.example", "bob", "secret", port=9981))
    result = client.allRecordings()

    assert result == ([], 0)
    assert captured == {
        "url": "http://tvh.example:9981/api/dvr/entry/grid_finished",
        "params": {"limit": 9999},
        "auth": ("bob", "secret"),
        "timeout": 10.0,
    }


def test_additional_endpoint_helpers_use_expected_routes(monkeypatch) -> None:
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def fake_send(
        cfg, route: str, data: dict[str, object] | None = None
    ) -> dict[str, object]:
        calls.append((cfg.host, route, data))
        return {"entries": [], "total": 0}

    monkeypatch.setattr("tvheadend.tvh.send_to_tvh", fake_send)

    assert upcomingRecordings() == ([], 0)
    assert activeRecordings() == ([], 0)
    assert channelGrid() == ([], 0)
    assert statusConnections(limit=100) == ([], 0)

    assert calls == [
        ("tvh.local", "dvr/entry/grid_upcoming", {"limit": 9999}),
        ("tvh.local", "dvr/entry/grid", {"limit": 9999}),
        ("tvh.local", "channel/grid", {"limit": 9999}),
        ("tvh.local", "status/connections", {"limit": 100}),
    ]


def test_client_additional_endpoints(monkeypatch) -> None:
    captured: list[tuple[str, dict[str, object] | None]] = []

    def fake_send(
        cfg, route: str, data: dict[str, object] | None = None
    ) -> dict[str, object]:
        captured.append((route, data))
        return {"entries": [], "total": 0}

    monkeypatch.setattr("tvheadend.tvh.send_to_tvh", fake_send)

    client = TVHeadendClient(configure("tvh.example", "bob", "secret", port=9981))

    assert client.upcomingRecordings() == ([], 0)
    assert client.activeRecordings() == ([], 0)
    assert client.channelGrid(limit=12) == ([], 0)
    assert client.statusConnections(limit=34) == ([], 0)

    assert captured == [
        ("dvr/entry/grid_upcoming", {"limit": 9999}),
        ("dvr/entry/grid", {"limit": 9999}),
        ("channel/grid", {"limit": 12}),
        ("status/connections", {"limit": 34}),
    ]


def test_epg_endpoint_helpers_use_expected_routes(monkeypatch) -> None:
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def fake_send(
        cfg, route: str, data: dict[str, object] | None = None
    ) -> dict[str, object]:
        calls.append((cfg.host, route, data))
        return {"entries": [], "total": 0}

    monkeypatch.setattr("tvheadend.tvh.send_to_tvh", fake_send)

    assert epgEvents() == ([], 0)
    assert epgEvents(limit=50, title="News") == ([], 0)
    assert epgEventsOnChannel("ch-1", limit=25) == ([], 0)
    assert epgEvents(start=1000, stop=2000) == ([], 0)
    assert epgEventsOnChannel("ch-1", limit=25, start=1000, stop=2000) == ([], 0)
    assert epgEventsInWindow(
        1000, 2000, limit=10, channelUuid="ch-1", title="News"
    ) == ([], 0)

    assert calls == [
        ("tvh.local", "epg/events/grid", {"limit": 9999}),
        ("tvh.local", "epg/events/grid", {"limit": 50, "title": "News"}),
        ("tvh.local", "epg/events/grid", {"limit": 25, "channelUuid": "ch-1"}),
        ("tvh.local", "epg/events/grid", {"limit": 9999, "start": 1000, "stop": 2000}),
        (
            "tvh.local",
            "epg/events/grid",
            {"limit": 25, "channelUuid": "ch-1", "start": 1000, "stop": 2000},
        ),
        (
            "tvh.local",
            "epg/events/grid",
            {
                "limit": 10,
                "channelUuid": "ch-1",
                "title": "News",
                "start": 1000,
                "stop": 2000,
            },
        ),
    ]


def test_client_epg_smoke_payload_shape(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, *, params, auth, timeout: float):
        captured["url"] = url
        captured["params"] = params
        captured["auth"] = auth
        captured["timeout"] = timeout
        return DummyResponse(
            json_data={
                "entries": [
                    {
                        "eventId": 42,
                        "title": "Evening News",
                        "start": 1700000000,
                        "stop": 1700001800,
                        "channelUuid": "ch-1",
                    }
                ],
                "total": 1,
            }
        )

    monkeypatch.setattr("tvheadend.tvh.requests.get", fake_get)

    client = TVHeadendClient(configure("tvh.example", "bob", "secret", port=9981))
    entries, total = client.epgEventsOnChannel("ch-1", limit=5)

    assert total == 1
    assert len(entries) == 1
    assert entries[0]["eventId"] == 42
    assert entries[0]["title"] == "Evening News"
    assert entries[0]["channelUuid"] == "ch-1"
    assert captured == {
        "url": "http://tvh.example:9981/api/epg/events/grid",
        "params": {"limit": 5, "channelUuid": "ch-1"},
        "auth": ("bob", "secret"),
        "timeout": 10.0,
    }


def test_client_epg_window_filters(monkeypatch) -> None:
    captured: list[dict[str, object]] = []

    def fake_send(
        cfg, route: str, data: dict[str, object] | None = None
    ) -> dict[str, object]:
        assert route == "epg/events/grid"
        captured.append(data or {})
        return {"entries": [], "total": 0}

    monkeypatch.setattr("tvheadend.tvh.send_to_tvh", fake_send)

    client = TVHeadendClient(configure("tvh.example", "bob", "secret", port=9981))

    assert client.epgEvents(start=1000, stop=2000) == ([], 0)
    assert client.epgEventsInWindow(1000, 2000, limit=20, title="Sport") == ([], 0)

    assert captured == [
        {"limit": 9999, "start": 1000, "stop": 2000},
        {"limit": 20, "title": "Sport", "start": 1000, "stop": 2000},
    ]
