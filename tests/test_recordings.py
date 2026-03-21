from __future__ import annotations

from tvheadend import recordings
from tvheadend.client import TVHeadendClient
from tvheadend.config import TVHConfig


def make_recording(**overrides: object) -> dict[str, object]:
    recording: dict[str, object] = {
        "channelname": "BBC One",
        "disp_description": "Description",
        "disp_extratext": "Bonus details",
        "disp_subtitle": " - Part 1",
        "disp_summary": "Summary",
        "disp_title": "New: Live: Example Show",
        "duration": 1800,
        "episode_disp": "Season 2.Episode 7",
        "filename": "/recordings/example.ts",
        "filesize": 1024,
        "start": 1700000000,
        "start_real": 1700000000,
        "status": "completed",
        "stop_real": 1700001800,
        "uuid": "uuid-1",
        "category": ["Drama"],
    }
    recording.update(overrides)
    return recording


def test_clean_title_removes_known_prefixes() -> None:
    assert recordings.cleanTitle(" Live: New: Example Show ") == "Example Show"


def test_get_episode_extracts_season_and_episode() -> None:
    assert recordings.getEpisode("Season 12.Episode 2") == ("12", "2")
    assert recordings.getEpisode("Episode 37") == (None, "37")
    assert recordings.getEpisode(None) == (None, None)


def test_tidy_recording_normalizes_fields() -> None:
    result = recordings.tidyRecording(make_recording())

    assert result["title"] == "Example Show"
    assert result["subtitle"] == "Part 1"
    assert result["description"] == "Description. Bonus details"
    assert result["season"] == "2"
    assert result["episode"] == "7"
    assert result["filename"] == "/recordings/example.ts"


def test_recorded_titles_groups_non_radio_recordings(monkeypatch) -> None:
    recs = [
        make_recording(),
        make_recording(filename="/var/lib/tvheadend/radio/show.ts", uuid="uuid-2"),
    ]

    monkeypatch.setattr(recordings, "allRecordings", lambda: (recs, len(recs)))

    returned_recs, titles = recordings.recordedTitles()

    assert returned_recs == recs
    assert list(titles) == ["Example Show"]
    assert len(titles["Example Show"]) == 1


def test_filtered_titles_filters_extension(monkeypatch) -> None:
    recs = [
        make_recording(filename="/recordings/first.ts", uuid="uuid-1"),
        make_recording(filename="/recordings/second.mkv", uuid="uuid-2"),
    ]

    monkeypatch.setattr(recordings, "allRecordings", lambda: (recs, len(recs)))

    matched, titles = recordings.filteredTitles(".ts")

    assert matched == [recs[0]]
    assert list(titles) == ["Example Show"]
    assert len(titles["Example Show"]) == 1


def test_recorded_titles_accepts_client_instance(monkeypatch) -> None:
    recs = [make_recording()]
    client = TVHeadendClient(TVHConfig("tvh.local", "user", "pass"))

    monkeypatch.setattr(client, "allRecordings", lambda: (recs, len(recs)))

    returned_recs, titles = recordings.recordedTitles(client)

    assert returned_recs == recs
    assert list(titles) == ["Example Show"]
