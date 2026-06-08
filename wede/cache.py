"""
Wede SDK Local Cache — Python
Stores teams locally for offline scoring.
Reference data only — operational queue is separate.
"""
from __future__ import annotations
import json
import time
from typing import Any, Dict, List, Optional, Protocol


class WedeStorage(Protocol):
    def get_item(self, key: str) -> Optional[str]: ...
    def set_item(self, key: str, value: str) -> None: ...
    def remove_item(self, key: str) -> None: ...


class DictStorage:
    """Simple in-memory storage — use for testing only."""
    def __init__(self):
        self._store: Dict[str, str] = {}
    def get_item(self, key: str) -> Optional[str]:
        return self._store.get(key)
    def set_item(self, key: str, value: str) -> None:
        self._store[key] = value
    def remove_item(self, key: str) -> None:
        self._store.pop(key, None)


CACHE_KEY_TEAMS  = "wede_cache_teams"
CACHE_KEY_META   = "wede_cache_meta"
CACHE_TTL_SEC    = 5 * 60


class WedeCache:
    def __init__(self, storage: WedeStorage):
        self._storage = storage

    def set_teams(self, teams: List[Dict[str, Any]]) -> None:
        self._storage.set_item(CACHE_KEY_TEAMS, json.dumps(teams))
        self._storage.set_item(CACHE_KEY_META, json.dumps({"teams_at": time.time()}))

    def get_teams(self) -> Optional[List[Dict[str, Any]]]:
        raw = self._storage.get_item(CACHE_KEY_TEAMS)
        if not raw:
            return None
        meta_raw = self._storage.get_item(CACHE_KEY_META)
        if meta_raw:
            meta = json.loads(meta_raw)
            if time.time() - meta.get("teams_at", 0) > CACHE_TTL_SEC:
                return None
        return json.loads(raw)

    def clear(self) -> None:
        self._storage.remove_item(CACHE_KEY_TEAMS)
        self._storage.remove_item(CACHE_KEY_META)
