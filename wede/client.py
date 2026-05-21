import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
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
    ):
        if not api_key:
            raise WedeAuthError("API key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._retries = retries

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

    # Tenant
    def get_tenant_info(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/tenant/me")

    def get_usage(self, from_date: str, to_date: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/tenant/usage?from={from_date}&to={to_date}")
