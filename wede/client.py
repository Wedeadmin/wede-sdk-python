import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from .offline_dispatch import WedeOfflineDispatch, WedeDeviceId
from .cache import WedeCache
from .errors import WedeAuthError, WedeError, WedeNetworkError
from .types import WedeEvent, WedeSyncBatch, WedeParserField

DEFAULT_BASE_URL = "https://api.wede.pt"
DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 3


class WedeClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        storage=None,
    ):
        if not api_key:
            raise WedeAuthError("API key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._retries = retries
        self.offline = WedeOfflineDispatch(storage) if storage else None
        self.cache = WedeCache(storage) if storage else None
        self._device_id = WedeDeviceId(storage) if storage else None

    def _request(self, method: str, path: str, body: Any = None, attempt: int = 1) -> Any:
        url = self._base_url + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "x-wede-api-key": self._api_key,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as res:
                return json.loads(res.read().decode())
        except urllib.error.HTTPError as e:
            body_raw = e.read().decode()
            try:
                err = json.loads(body_raw)
            except Exception:
                err = {}
            if e.code == 401:
                raise WedeAuthError()
            raise WedeError(
                err.get("message", "Request failed"),
                err.get("error", "api_error"),
                e.code,
            )
        except Exception as e:
            if attempt < self._retries:
                time.sleep(0.3 * attempt)
                return self._request(method, path, body, attempt + 1)
            raise WedeNetworkError(str(e))

    # Events
    def send_event(self, event: WedeEvent) -> Dict[str, Any]:
        return self._request("POST", "/v1/events", event.to_dict())

    def list_events(self, zone_id: str = None, vertical: str = None, limit: int = None) -> Dict[str, Any]:
        params = {}
        if zone_id: params["zone_id"] = zone_id
        if vertical: params["vertical"] = vertical
        if limit: params["limit"] = str(limit)
        qs = ("?" + "&".join(f"{k}={v}" for k, v in params.items())) if params else ""
        return self._request("GET", f"/v1/events{qs}")

    # Zones
    def list_zones(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/zones")

    def get_zone(self, zone_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/zones/{zone_id}")

    # Sync
    def sync_batch(self, batch: WedeSyncBatch) -> Dict[str, Any]:
        return self._request("POST", "/v1/sync/batch", batch.to_dict())

    def get_sync_status(self, batch_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/sync/status?batch_id={batch_id}")

    # Connectivity
    def get_connectivity_status(self, zone_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/connectivity/status?zone_id={zone_id}")

    def report_connectivity(self, zone_id: str, state: str, channel_used: str) -> Dict[str, Any]:
        return self._request("POST", "/v1/connectivity/report", {
            "zone_id": zone_id,
            "state": state,
            "channel_used": channel_used,
        })

    # Parsers
    def list_parsers(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/parsers")

    def get_parser(self, parser_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/parsers/{parser_id}")

    def get_active_parser(self, vertical: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/parsers/vertical/{vertical}/active")

    def create_parser(self, vertical: str, name: str, schema: List[WedeParserField], description: str = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"vertical": vertical, "name": name, "schema": [f.to_dict() for f in schema]}
        if description: body["description"] = description
        return self._request("POST", "/v1/parsers", body)

    def update_parser(self, parser_id: str, name: str = None, schema: List[WedeParserField] = None, is_active: bool = None, description: str = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        if name is not None: body["name"] = name
        if description is not None: body["description"] = description
        if schema is not None: body["schema"] = [f.to_dict() for f in schema]
        if is_active is not None: body["is_active"] = is_active
        return self._request("PATCH", f"/v1/parsers/{parser_id}", body)

    # Webhooks
    def list_webhooks(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/webhooks")

    def create_webhook(self, url: str, events: List[str], secret: str = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"url": url, "events": events}
        if secret: body["secret"] = secret
        return self._request("POST", "/v1/webhooks", body)

    def delete_webhook(self, webhook_id: str) -> None:
        self._request("DELETE", f"/v1/webhooks/{webhook_id}")


    # Teams
    def list_teams(self, tenant_id: str = None) -> dict:
        qs = f"?tenant_id={tenant_id}" if tenant_id else ""
        return self._request("GET", f"/v1/teams{qs}")

    def get_team(self, team_id: str) -> dict:
        return self._request("GET", f"/v1/teams/{team_id}")

    def update_member_location(self, team_id: str, member_id: str, lat: float, lng: float) -> dict:
        return self._request("PATCH", f"/v1/teams/{team_id}/members/{member_id}/location", {
            "lat": lat, "lng": lng
        })

    # Dispatch
    def score_teams(self, lat: float, lng: float, vertical: str = None,
                    priority: str = None, required_equipment: list = None) -> dict:
        body = {"lat": lat, "lng": lng}
        if vertical: body["vertical"] = vertical
        if priority: body["priority"] = priority
        if required_equipment: body["required_equipment"] = required_equipment
        return self._request("POST", "/v1/teams/dispatch/score", body)

    def dispatch(self, event_id: str, team_id: str, notes: str = None,
                 event_lat: float = None, event_lng: float = None) -> dict:
        body = {"event_id": event_id, "team_id": team_id}
        if notes: body["notes"] = notes
        if event_lat is not None: body["event_lat"] = event_lat
        if event_lng is not None: body["event_lng"] = event_lng
        return self._request("POST", "/v1/teams/dispatch", body)

    # Missions
    def list_missions(self, team_id: str = None, status: str = None, limit: int = None) -> dict:
        params = {}
        if team_id: params["team_id"] = team_id
        if status: params["status"] = status
        if limit: params["limit"] = str(limit)
        qs = ("?" + "&".join(f"{k}={v}" for k, v in params.items())) if params else ""
        return self._request("GET", f"/v1/missions{qs}")

    def get_mission(self, mission_id: str) -> dict:
        return self._request("GET", f"/v1/missions/{mission_id}")

    def update_mission_status(self, mission_id: str, status: str, feedback: dict = None) -> dict:
        body = {"status": status}
        if feedback: body["feedback"] = feedback
        return self._request("PATCH", f"/v1/missions/{mission_id}/status", body)

    # Catalog
    def list_catalog_actions(self, vertical: str = None) -> dict:
        qs = f'?vertical={vertical}' if vertical else ''
        return self._request('GET', f'/v1/catalog/actions{qs}')

    def create_catalog_action(self, vertical: str, code: str, name: str, description: str = None) -> dict:
        body = {'vertical': vertical, 'code': code, 'name': name}
        if description: body['description'] = description
        return self._request('POST', '/v1/catalog/actions', body)

    def delete_catalog_action(self, action_id: str) -> None:
        return self._request('DELETE', f'/v1/catalog/actions/{action_id}')

    # Billing
    def get_billing(self) -> dict:
        return self._request("GET", "/v1/tenant/billing")

    # Tenant
    def get_tenant_info(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/tenant/me")

    def get_usage(self, from_date: str, to_date: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/tenant/usage?from={from_date}&to={to_date}")

    # Device & Offline Sync

    def register_device(self, platform: str = "other", app_version: str = None) -> dict:
        if not self._device_id:
            raise ValueError("Storage required for device registration")
        device_id = self._device_id.get_or_create()
        body = {"device_id": device_id, "platform": platform}
        if app_version:
            body["app_version"] = app_version
        return self._request("POST", "/v1/devices/register", body)

    def sync_device_queue(self) -> dict:
        if not self.offline or not self._device_id:
            return {}
        device_id = self._device_id.get()
        if not device_id:
            return {}
        pending = self.offline.get_pending_queue()
        dispatches = [{
            "sequence_number": d.sequence_number,
            "action_id": d.action_id,
            "event_lat": d.event.get("lat"),
            "event_lng": d.event.get("lng"),
            "vertical": d.event.get("vertical"),
            "priority": d.event.get("priority"),
            "created_offline_at": d.queued_at,
        } for d in pending]
        body = {"device_id": device_id, "last_received_seq": 0, "dispatches": dispatches}
        result = self._request("POST", "/v1/devices/sync", body)
        for seq in result.get("accepted", []):
            entry = next((d for d in pending if d.sequence_number == seq), None)
            if entry:
                self.offline.mark_synced(entry.id)
        self.offline.clear_synced()
        return result

    def refresh_cache(self) -> None:
        if not self.cache:
            return
        teams_res = self._request("GET", "/v1/teams")
        self.cache.set_teams(teams_res.get("data", []))

    def request_backup(self, mission_id: str, event_id: str, event_lat: float = None, event_lng: float = None) -> dict:
        """Request a backup team for an active mission."""
        body = {
            "event_id": event_id,
            "notes": f"Backup requested by field operator for mission {mission_id}",
        }
        if event_lat is not None:
            body["event_lat"] = event_lat
        if event_lng is not None:
            body["event_lng"] = event_lng
        return self._request("POST", "/v1/teams/dispatch", body)

    def update_dispatch_settings(self, dispatch_mode: bool = None, dispatch_threshold: float = None, reinforcement_timeout_min: int = None) -> dict:
        """Update tenant dispatch settings including reinforcement timeout."""
        body = {}
        if dispatch_mode is not None:
            body["dispatch_mode"] = dispatch_mode
        if dispatch_threshold is not None:
            body["dispatch_threshold"] = dispatch_threshold
        if reinforcement_timeout_min is not None:
            body["reinforcement_timeout_min"] = reinforcement_timeout_min
        return self._request("PATCH", "/v1/tenant/dispatch-settings", body)
