# wede-sdk

Official Python SDK for the Wede Technology platform.

Wede is an offline-first infrastructure layer that keeps critical digital services operational when connectivity, cloud, or infrastructure fails.

## Installation

pip install wede-sdk

## Quick Start

from wede import WedeClient, WedeEvent

client = WedeClient(api_key="wede_live_YOUR_KEY")

# Send an event
event = WedeEvent(
    type="EMERGENCY",
    idempotency_key="evt-001",
    vertical="healthcare",
    priority="critical",
    payload={"patient_id": "PT123"}
)
result = client.send_event(event)

# List zones
zones = client.list_zones()

# Sync offline batch
from wede import WedeSyncBatch
from datetime import datetime, timezone

batch = WedeSyncBatch(
    events=[event],
    captured_at=datetime.now(timezone.utc).isoformat(),
    device_id="device-001"
)
result = client.sync_batch(batch)

## Methods

| Method | Description |
|--------|-------------|
| send_event(event) | Submit a new event |
| list_events(...) | List events |
| list_zones() | List all zones |
| get_zone(zone_id) | Get a specific zone |
| sync_batch(batch) | Sync offline events |
| get_sync_status(batch_id) | Get sync batch status |
| get_connectivity_status(zone_id) | Get zone connectivity |
| report_connectivity(...) | Report connectivity state |
| list_parsers() | List all parsers |
| get_parser(parser_id) | Get a specific parser |
| get_active_parser(vertical) | Get active parser for vertical |
| create_parser(...) | Create a new parser |
| update_parser(...) | Update an existing parser |
| list_webhooks() | List all webhooks |
| create_webhook(...) | Create a new webhook |
| delete_webhook(webhook_id) | Delete a webhook |
| get_tenant_info() | Get tenant details |
| get_usage(from_date, to_date) | Get usage statistics |

## Documentation

https://docs.wede.pt

## License

MIT
