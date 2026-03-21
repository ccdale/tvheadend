from __future__ import annotations

from typing import Any, Mapping

from .config import TVHConfig
from .recordings import RecordingSummary, filteredTitles, recordedTitles
from .tvh import (
    ChannelEntry,
    RecordingEntry,
    StatusConnectionEntry,
    active_recordings,
    all_recordings,
    channel_grid,
    delete_recording,
    file_moved,
    send_to_tvh,
    status_connections,
    upcoming_recordings,
)


class TVHeadendClient:
    def __init__(self, config: TVHConfig) -> None:
        self.config = config

    def sendToTvh(
        self, route: str, data: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        return send_to_tvh(self.config, route, data)

    def allRecordings(self) -> tuple[list[RecordingEntry], int]:
        return all_recordings(self.config)

    def upcomingRecordings(self) -> tuple[list[RecordingEntry], int]:
        return upcoming_recordings(self.config)

    def activeRecordings(self) -> tuple[list[RecordingEntry], int]:
        return active_recordings(self.config)

    def channelGrid(self, limit: int = 9999) -> tuple[list[ChannelEntry], int]:
        return channel_grid(self.config, limit=limit)

    def statusConnections(
        self,
        limit: int = 9999,
    ) -> tuple[list[StatusConnectionEntry], int]:
        return status_connections(self.config, limit=limit)

    def deleteRecording(self, uuid: str) -> None:
        delete_recording(self.config, uuid)

    def fileMoved(self, src: str, dst: str) -> None:
        file_moved(self.config, src, dst)

    def recordedTitles(
        self,
    ) -> tuple[list[dict[str, Any]], dict[str | None, list[RecordingSummary]]]:
        return recordedTitles(self)

    def filteredTitles(
        self,
        filetype: str = ".ts",
    ) -> tuple[list[dict[str, Any]], dict[str | None, list[RecordingSummary]]]:
        return filteredTitles(filetype=filetype, client=self)
