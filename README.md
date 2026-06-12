# wede-sdk-python

Official Python SDK for the Wede Technology platform.

Wede is an offline-first middleware layer that keeps critical operational workflows running regardless of connectivity. When internet fails, operations continue locally and sync automatically on reconnect.

## Installation

```bash
pip install wede-sdk
```

## Quick Start

```python
from wede import WedeClient

client = WedeClient(api_key="wede_live_YOUR_KEY")

# Send an event
event = client.send_event(
    type="EMERGENCY",
    priority="high",
    vertical="healthcare",
    idempotency_key="evt-001",
    payload={"condition": "cardiac_arrest"},
    location={"lat": 38.7169, "lng": -9.1395}
)

# Score and dispatch teams
scored = client.score_teams(
    lat=38.7169, lng=-9.1395,
    vertical="healthcare", priority="high"
)

client.dispatch(
    event_id=event["event_id"],
    team_id=scored["data"][0]["team_id"],
    event_lat=38.7169, event_lng=-9.1395
)
```

## Offline Operation

The SDK operates fully offline using a local score engine identical to the backend. Dispatches are queued with guaranteed delivery on reconnect.

```python
from wede import WedeClient, WedeDeviceId, DictStorage

storage = DictStorage()  # or implement WedeStorage for persistence
device_id = WedeDeviceId.get_or_create(storage)

# Register device on first launch
client.register_device(device_id, "other", "2.0.0")

# Dispatch works online and offline
result = client.dispatch(
    event_id="uuid", team_id="uuid",
    event_lat=38.7169, event_lng=-9.1395
)
# result["queued"] == True when offline

# Sync when connectivity restored
client.sync_device_queue(device_id)

# Request backup for active mission
client.request_backup(
    mission_id="uuid",
    event_id="uuid",
    event_lat=38.7169,
    event_lng=-9.1395
)

# Update dispatch settings
client.update_dispatch_settings(
    dispatch_mode=True,
    dispatch_threshold=0.20,
    reinforcement_timeout_min=10
)
```

## Method Reference

| Method | Description |
| --- | --- |
| `send_event(...)` | Submit an operational event |
| `list_events()` | List events for the tenant |
| `score_teams(...)` | Score available teams by proximity and capability |
| `dispatch(...)` | Dispatch a team to an event |
| `request_backup(...)` | Request backup for an active mission |
| `list_missions()` | List missions |
| `get_mission(id)` | Get a specific mission |
| `update_mission_status(id, status)` | Update mission status |
| `update_dispatch_settings(...)` | Configure auto-dispatch settings |
| `register_device(device_id, platform, version)` | Register device for offline sync |
| `sync_device_queue(device_id)` | Sync offline queue with server |
| `refresh_cache()` | Refresh local team and catalog cache |
| `get_tenant_info()` | Get tenant configuration |
| `get_usage(from_date, to_date)` | Get usage statistics |
| `list_zones()` | List operational zones |
| `list_parsers()` | List event parsers |
| `get_billing()` | Get billing information |
| `list_webhooks()` | List webhooks |
| `create_webhook(...)` | Create a webhook |

## Requirements

- Python 3.8+
- requests

## Documentation

[docs.wede.pt](https://docs.wede.pt)

## Patent

Wede Technology INPI 120488 (pending) — Claim 5: local score engine and guaranteed offline dispatch queue.

## License

MIT
