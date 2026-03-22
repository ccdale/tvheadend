# tvheadend

Small Python package for talking to a remote TVHeadend instance.

## Status

The package currently covers:

- typed configuration for connecting to TVHeadend
- low-level API requests
- DVR recording queries and helpers for grouping recordings by title
- EPG event queries with typed response entries

## Install

For local development with `uv`:

```bash
uv sync --extra dev
```

To build distributions:

```bash
uv build
```

To run tests:

```bash
uv run pytest -q
```

## Debian/Ubuntu Build Instructions

Install system dependencies:

```bash
sudo apt update
sudo apt install -y git curl python3 python3-venv python3-installer
```

Install `uv` (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Build and test from a clone of this repository:

```bash
uv sync --extra dev
uv run pytest -q
uv build
```

Install the built wheel into the system package root (for packaging workflows):

```bash
python3 -m installer --destdir="${PWD}/pkgroot" dist/*.whl
```

Install for local user testing:

```bash
python3 -m pip install --user dist/*.whl
```

## Packaging Guides

- Arch Linux packaging: [archlinux/README.md](archlinux/README.md)
- Debian packaging: [debian/README.md](debian/README.md)

## Module-level usage

```python
from tvheadend import configure
from tvheadend.tvh import allRecordings

configure(
	host="tvh.example",
	username="alice",
	password="secret",
	port=9981,
)

recordings, total = allRecordings()
```

## Client usage

```python
from tvheadend import TVHConfig, TVHeadendClient

client = TVHeadendClient(
	TVHConfig(
		host="tvh.example",
		username="alice",
		password="secret",
		port=9981,
	)
)

recordings, total = client.allRecordings()
upcoming, upcoming_total = client.upcomingRecordings()
active, active_total = client.activeRecordings()
channels, channel_total = client.channelGrid()
connections, connection_total = client.statusConnections()
epg_events, epg_total = client.epgEvents(limit=200)
channel_events, channel_epg_total = client.epgEventsOnChannel("ch-1", limit=50)
window_events, window_total = client.epgEvents(start=1700000000, stop=1700003600)
window_events_2, window_total_2 = client.epgEventsInWindow(1700000000, 1700003600)
filtered, grouped = client.filteredTitles(".ts")
```

## API Notes

- `TVHeadendClient.sendToTvh()` issues a GET request to `/api/<route>`.
- `client.allRecordings()` maps to `dvr/entry/grid_finished`.
- `client.upcomingRecordings()` maps to `dvr/entry/grid_upcoming`.
- `client.activeRecordings()` maps to `dvr/entry/grid`.
- `client.channelGrid()` maps to `channel/grid`.
- `client.statusConnections()` maps to `status/connections`.
- `client.epgEvents()` maps to `epg/events/grid`.
- `client.epgEventsOnChannel(channelUuid)` maps to `epg/events/grid` with a channel filter.
- `client.epgEvents(start=..., stop=...)` maps to `epg/events/grid` with a time-window filter.
- `client.epgEventsInWindow(start, stop)` is a convenience wrapper for time-window EPG queries.
- `client.deleteRecording(uuid)` maps to `dvr/entry/remove`.
- `client.fileMoved(src, dst)` maps to `dvr/entry/filemoved`.
- recording helpers normalize common title prefixes such as `New:` and `Live:`.

## Naming And Compatibility

- Public functions and methods use `camelCase`.
- Internal helpers use `snake_case` and are not part of the public API contract.
- `get_config()` and `clear_config()` currently remain as compatibility aliases for `getConfig()` and `clearConfig()`.
- New client code should use `camelCase` methods only.
