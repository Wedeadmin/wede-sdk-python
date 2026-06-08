"""
Wede Offline Dispatch — Python SDK
Guaranteed delivery of operational dispatches without connectivity.
Patent INPI 120488 — Claim 5 implementation.
Queue is immutable — never deleted until server confirmation.
"""
from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .cache import WedeCache, WedeStorage
from .score_engine import EventInput, TeamInput, ScoredTeam, score_teams

QUEUE_KEY   = "wede_offline_dispatch_queue"
DEVICE_KEY  = "wede_device_id"


@dataclass
class OfflineDispatchRequest:
    id: str
    action_id: str
    event: Dict[str, Any]
    team_id: str
    team_name: str
    score: float
    channel: str
    queued_at: str
    synced: bool
    sequence_number: int


@dataclass
class DispatchOfflineResult:
    success: bool
    team: Optional[ScoredTeam]
    queued: bool
    queue_id: Optional[str]
    reason: Optional[str] = None


class WedeDeviceId:
    def __init__(self, storage: WedeStorage):
        self._storage = storage

    def get_or_create(self) -> str:
        existing = self._storage.get_item(DEVICE_KEY)
        if existing:
            return existing
        new_id = str(uuid.uuid4())
        self._storage.set_item(DEVICE_KEY, new_id)
        return new_id

    def get(self) -> Optional[str]:
        return self._storage.get_item(DEVICE_KEY)


class WedeOfflineDispatch:
    def __init__(self, storage: WedeStorage):
        self._storage = storage
        self._cache = WedeCache(storage)

    def score_locally(self, event: EventInput) -> List[ScoredTeam]:
        raw_teams = self._cache.get_teams()
        if not raw_teams:
            return []
        teams = [TeamInput(
            id=t["id"], name=t["name"], status=t["status"],
            vertical=t.get("vertical", ""),
            equipment=t.get("equipment", []),
            zone_lat=t.get("zone_lat"), zone_lng=t.get("zone_lng"),
            members=[]
        ) for t in raw_teams]
        return score_teams(teams, event)

    def dispatch(self, action_id: str, event: EventInput) -> DispatchOfflineResult:
        scored = self.score_locally(event)
        best = next((t for t in scored if t.status == "available"), None) or (scored[0] if scored else None)

        if not best:
            return DispatchOfflineResult(
                success=False, team=None, queued=False,
                queue_id=None, reason="no_teams_cached"
            )

        seq = self._get_next_sequence()
        entry_id = str(uuid.uuid4())
        entry = OfflineDispatchRequest(
            id=entry_id, action_id=action_id,
            event={"lat": event.lat, "lng": event.lng,
                   "vertical": event.vertical, "priority": event.priority},
            team_id=best.team_id, team_name=best.team_name,
            score=best.score, channel=best.channel,
            queued_at=datetime.now(timezone.utc).isoformat(),
            synced=False, sequence_number=seq
        )
        self._enqueue(entry)
        return DispatchOfflineResult(success=True, team=best, queued=True, queue_id=entry_id)

    def get_pending_queue(self) -> List[OfflineDispatchRequest]:
        return [e for e in self._get_all() if not e.synced]

    def mark_synced(self, entry_id: str) -> None:
        all_entries = self._get_all()
        updated = [
            OfflineDispatchRequest(**{**asdict(e), "synced": True}) if e.id == entry_id else e
            for e in all_entries
        ]
        self._storage.set_item(QUEUE_KEY, json.dumps([asdict(e) for e in updated]))

    def clear_synced(self) -> None:
        pending = [e for e in self._get_all() if not e.synced]
        self._storage.set_item(QUEUE_KEY, json.dumps([asdict(e) for e in pending]))

    def queue_size(self) -> int:
        return len(self.get_pending_queue())

    def _get_all(self) -> List[OfflineDispatchRequest]:
        raw = self._storage.get_item(QUEUE_KEY)
        if not raw:
            return []
        try:
            return [OfflineDispatchRequest(**e) for e in json.loads(raw)]
        except Exception:
            return []

    def _enqueue(self, entry: OfflineDispatchRequest) -> None:
        all_entries = self._get_all()
        all_entries.append(entry)
        self._storage.set_item(QUEUE_KEY, json.dumps([asdict(e) for e in all_entries]))

    def _get_next_sequence(self) -> int:
        all_entries = self._get_all()
        return max((e.sequence_number for e in all_entries), default=0) + 1
