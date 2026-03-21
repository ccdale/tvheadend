# tvheadend

Small Python package for talking to a remote TVHeadend instance.

## Status

The package currently covers:

- typed configuration for connecting to TVHeadend
- low-level API requests
- DVR recording queries and helpers for grouping recordings by title

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
filtered, grouped = client.filteredTitles(".ts")
```

## API Notes

- `TVHeadendClient.sendToTvh()` issues a GET request to `/api/<route>`.
- `client.allRecordings()` maps to `dvr/entry/grid_finished`.
- `client.upcomingRecordings()` maps to `dvr/entry/grid_upcoming`.
- `client.activeRecordings()` maps to `dvr/entry/grid`.
- `client.channelGrid()` maps to `channel/grid`.
- `client.statusConnections()` maps to `status/connections`.
- `client.deleteRecording(uuid)` maps to `dvr/entry/remove`.
- `client.fileMoved(src, dst)` maps to `dvr/entry/filemoved`.
- recording helpers normalize common title prefixes such as `New:` and `Live:`.

## Naming And Compatibility

- Public functions and methods use `camelCase`.
- Internal helpers use `snake_case` and are not part of the public API contract.
- `get_config()` and `clear_config()` currently remain as compatibility aliases for `getConfig()` and `clearConfig()`.
- New client code should use `camelCase` methods only.
