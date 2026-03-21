from __future__ import annotations

"""Helpers for shaping and filtering TVHeadend recording data."""

import re
import time
from typing import TYPE_CHECKING, Any, Mapping, Protocol, TypedDict

from .tvh import allRecordings

if TYPE_CHECKING:
    from .client import TVHeadendClient


class SupportsAllRecordings(Protocol):
    def allRecordings(self) -> tuple[list[Mapping[str, Any]], int]: ...


class RecordingSummary(TypedDict):
    category: list[str]
    channelname: str | None
    ctimestart: str
    description: str | None
    disp_description: str | None
    duration: int | None
    episode: str | None
    extratext: str | None
    filename: str
    filesize: int | None
    recorddate: int | None
    season: str | None
    start_real: int
    status: str | None
    stop_real: int
    subtitle: str | None
    summary: str | None
    title: str | None
    uuid: str | None


def cleanStringStart(xstr: str | None, remove: str = "new:") -> str | None:
    if xstr is None:
        return None
    if xstr.lower().startswith(remove.lower()):
        xstr = xstr[len(remove) :]
    return xstr.strip()


def cleanTitle(title: str | None) -> str | None:
    """rules to clean up the title string."""
    xt = cleanStringStart(title, remove="new:")
    xt = cleanStringStart(xt, remove="live:")
    xt = cleanStringStart(xt, remove="live:")
    xt = cleanStringStart(xt, remove="new:")
    return xt


def tidyRecording(rec: Mapping[str, Any]) -> RecordingSummary:
    """retrieve the info we want about each recording."""
    filename = rec.get("filename") or ""
    description = rec.get("disp_description")
    extdesc = rec.get("disp_extratext")
    if description and extdesc:
        description = f"{description}. {extdesc}"
    elif extdesc:
        description = extdesc

    season, episode = getEpisode(rec.get("episode_disp"))
    return {
        "channelname": rec.get("channelname"),
        "description": description,
        "duration": rec.get("duration"),
        "episode": episode,
        "extratext": extdesc,
        "filename": filename,
        "filesize": rec.get("filesize"),
        "recorddate": rec.get("start"),
        "season": season,
        "start_real": rec.get("start_real", 0),
        "status": rec.get("status"),
        "stop_real": rec.get("stop_real", 0),
        "subtitle": cleanStringStart(rec.get("disp_subtitle"), " - "),
        "summary": rec.get("disp_summary"),
        "title": cleanTitle(rec.get("disp_title")),
        "uuid": rec.get("uuid"),
        "disp_description": rec.get("disp_description"),
        "ctimestart": time.ctime(rec.get("start_real", 0)),
        "category": rec.get("category", []),
    }


def getEpisode(eps: str | None) -> tuple[str | None, str | None]:
    """extracts the season and episode numbers if they exist

    the input string, eps,  is of the form:
    ''
    'Episode 37'
    'Season 12.Episode 2'
    """
    episode = None
    season = None
    spatt = r"^Season (\d+).*$"
    epatt = r"^.*Episode (\d+).*$"
    if eps is not None:
        smatch = re.match(spatt, eps)
        if smatch:
            season = smatch.group(1)
        ematch = re.match(epatt, eps)
        if ematch:
            episode = ematch.group(1)
    return season, episode


def load_recordings(
    client: SupportsAllRecordings | None = None,
) -> tuple[list[Mapping[str, Any]], int]:
    if client is None:
        return allRecordings()
    return client.allRecordings()


def recordedTitles(
    client: SupportsAllRecordings | None = None,
) -> tuple[list[Mapping[str, Any]], dict[str | None, list[RecordingSummary]]]:
    """Obtain all recorded titles as a dictionary of lists of those recordings."""  # noqa: E501
    recs, _total = load_recordings(client)
    titles: dict[str | None, list[RecordingSummary]] = {}
    for rec in recs:
        show = tidyRecording(rec)
        if not show["filename"].startswith("/var/lib/tvheadend/radio"):
            titles.setdefault(show["title"], []).append(show)
    return recs, titles


def filteredTitles(
    filetype: str = ".ts",
    client: SupportsAllRecordings | None = None,
) -> tuple[list[Mapping[str, Any]], dict[str | None, list[RecordingSummary]]]:
    """Obtain all recorded titles as a dictionary of lists of those recordings."""  # noqa: E501
    recs, _total = load_recordings(client)
    titles: dict[str | None, list[RecordingSummary]] = {}
    matched_recordings: list[Mapping[str, Any]] = []
    for rec in recs:
        filename = rec.get("filename", "")
        if not filename.lower().endswith(filetype.lower()):
            continue
        show = tidyRecording(rec)
        matched_recordings.append(rec)
        if not show["filename"].startswith("/var/lib/tvheadend/radio"):
            titles.setdefault(show["title"], []).append(show)
    return matched_recordings, titles
