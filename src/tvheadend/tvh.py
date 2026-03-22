"""TVHeadend HTTP client helpers."""

from __future__ import annotations

import json
from typing import Any, Mapping, TypedDict, cast

import requests

from .config import TVHConfig, getConfig

__all__ = [
    "ChannelEntry",
    "EpgEventEntry",
    "RecordingEntry",
    "StatusConnectionEntry",
    "TVHError",
    "activeRecordings",
    "allRecordings",
    "channelGrid",
    "deleteRecording",
    "epgEvents",
    "epgEventsInWindow",
    "epgEventsOnChannel",
    "fileMoved",
    "sendToTvh",
    "statusConnections",
    "upcomingRecordings",
]


class TVHError(Exception):
    """Raised when TVHeadend communication fails."""


class RecordingEntry(TypedDict, total=False):
    uuid: str
    channelname: str
    disp_title: str
    filename: str
    start: int
    stop: int
    status: str


class ChannelEntry(TypedDict, total=False):
    uuid: str
    name: str
    number: int
    enabled: bool
    tags: list[str]


class StatusConnectionEntry(TypedDict, total=False):
    id: int
    user: str
    peer: str
    started: int
    streaming: bool


class EpgEventEntry(TypedDict, total=False):
    eventId: int
    title: str
    subtitle: str
    summary: str
    start: int
    stop: int
    channelUuid: str


def send_to_tvh(
    cfg: TVHConfig,
    route: str,
    data: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        response = requests.get(
            cfg.api_url(route),
            params=data,
            auth=cfg.auth,
            timeout=cfg.timeout,
        )
    except requests.RequestException as exc:
        raise TVHError(f"error communicating with tvh: {exc}") from exc

    if response.status_code != 200:
        raise TVHError(f"error communicating with tvh: {response.status_code}")

    try:
        payload = response.json()
        if not isinstance(payload, dict):
            raise TVHError("TVHeadend returned a non-object JSON payload")
        return payload
    except ValueError:
        try:
            txt = response.text.replace(chr(25), " ")
            return json.loads(txt)
        except json.JSONDecodeError as exc:
            raise TVHError("error decoding json from tvh response") from exc


def sendToTvh(route: str, data: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Send a GET request to the TVHeadend API and decode the response."""
    return send_to_tvh(getConfig(), route, data)


def parse_grid_payload(
    payload: dict[str, Any],
    *,
    error_message: str,
) -> tuple[list[Mapping[str, Any]], int]:
    entries = payload.get("entries", [])
    total = payload.get("total", len(entries))
    if not isinstance(entries, list) or not isinstance(total, int):
        raise TVHError(error_message)
    return cast(list[Mapping[str, Any]], entries), total


def list_recordings(
    cfg: TVHConfig,
    route: str,
    limit: int = 9999,
) -> tuple[list[RecordingEntry], int]:
    payload = send_to_tvh(cfg, route, data={"limit": limit})
    entries, total = parse_grid_payload(
        payload,
        error_message="unexpected TVHeadend recordings payload",
    )
    return cast(list[RecordingEntry], entries), total


def all_recordings(cfg: TVHConfig) -> tuple[list[RecordingEntry], int]:
    return list_recordings(cfg, "dvr/entry/grid_finished")


def allRecordings() -> tuple[list[RecordingEntry], int]:
    return all_recordings(getConfig())


def upcoming_recordings(cfg: TVHConfig) -> tuple[list[RecordingEntry], int]:
    return list_recordings(cfg, "dvr/entry/grid_upcoming")


def upcomingRecordings() -> tuple[list[RecordingEntry], int]:
    return upcoming_recordings(getConfig())


def active_recordings(cfg: TVHConfig) -> tuple[list[RecordingEntry], int]:
    return list_recordings(cfg, "dvr/entry/grid")


def activeRecordings() -> tuple[list[RecordingEntry], int]:
    return active_recordings(getConfig())


def delete_recording(cfg: TVHConfig, uuid: str) -> None:
    data = {"uuid": uuid}
    send_to_tvh(cfg, "dvr/entry/remove", data)


def deleteRecording(uuid: str) -> None:
    delete_recording(getConfig(), uuid)


def file_moved(cfg: TVHConfig, src: str, dst: str) -> None:
    data = {"src": src, "dst": dst}
    send_to_tvh(cfg, "dvr/entry/filemoved", data)


def fileMoved(src: str, dst: str) -> None:
    file_moved(getConfig(), src, dst)


def channel_grid(cfg: TVHConfig, limit: int = 9999) -> tuple[list[ChannelEntry], int]:
    payload = send_to_tvh(cfg, "channel/grid", data={"limit": limit})
    entries, total = parse_grid_payload(
        payload,
        error_message="unexpected TVHeadend channels payload",
    )
    return cast(list[ChannelEntry], entries), total


def channelGrid(limit: int = 9999) -> tuple[list[ChannelEntry], int]:
    return channel_grid(getConfig(), limit=limit)


def status_connections(
    cfg: TVHConfig,
    limit: int = 9999,
) -> tuple[list[StatusConnectionEntry], int]:
    payload = send_to_tvh(cfg, "status/connections", data={"limit": limit})
    entries, total = parse_grid_payload(
        payload,
        error_message="unexpected TVHeadend status payload",
    )
    return cast(list[StatusConnectionEntry], entries), total


def statusConnections(limit: int = 9999) -> tuple[list[StatusConnectionEntry], int]:
    return status_connections(getConfig(), limit=limit)


def epg_events(
    cfg: TVHConfig,
    *,
    limit: int = 9999,
    channelUuid: str | None = None,
    title: str | None = None,
    start: int | None = None,
    stop: int | None = None,
) -> tuple[list[EpgEventEntry], int]:
    params: dict[str, Any] = {"limit": limit}
    if channelUuid is not None:
        # TVHeadend EPG grid uses 'channel' (not 'channelUuid') to filter by channel.
        params["channel"] = channelUuid
    if title is not None:
        params["title"] = title
    if start is not None:
        # TVHeadend uses 'startsAfter' / 'startsBefore' for time filtering.
        # 'start' / 'stop' are event IDs, not Unix timestamps.
        params["startsAfter"] = start
    if stop is not None:
        params["startsBefore"] = stop

    payload = send_to_tvh(cfg, "epg/events/grid", data=params)
    entries, total = parse_grid_payload(
        payload,
        error_message="unexpected TVHeadend EPG payload",
    )
    return cast(list[EpgEventEntry], entries), total


def epgEvents(
    *,
    limit: int = 9999,
    channelUuid: str | None = None,
    title: str | None = None,
    start: int | None = None,
    stop: int | None = None,
) -> tuple[list[EpgEventEntry], int]:
    return epg_events(
        getConfig(),
        limit=limit,
        channelUuid=channelUuid,
        title=title,
        start=start,
        stop=stop,
    )


def epgEventsOnChannel(
    channelUuid: str,
    *,
    limit: int = 9999,
    start: int | None = None,
    stop: int | None = None,
) -> tuple[list[EpgEventEntry], int]:
    return epg_events(
        getConfig(),
        limit=limit,
        channelUuid=channelUuid,
        start=start,
        stop=stop,
    )


def epgEventsInWindow(
    start: int,
    stop: int,
    *,
    limit: int = 9999,
    channelUuid: str | None = None,
    title: str | None = None,
) -> tuple[list[EpgEventEntry], int]:
    return epg_events(
        getConfig(),
        limit=limit,
        channelUuid=channelUuid,
        title=title,
        start=start,
        stop=stop,
    )
