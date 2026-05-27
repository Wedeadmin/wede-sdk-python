from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class WedeEvent:
    type: str
    idempotency_key: str
    payload: Dict[str, Any]
    priority: Optional[str] = None
    vertical: Optional[str] = None
    zone_id: Optional[str] = None
    channel_preference: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "type": self.type,
            "idempotency_key": self.idempotency_key,
            "payload": self.payload,
        }
        if self.priority: d["priority"] = self.priority
        if self.vertical: d["vertical"] = self.vertical
        if self.zone_id: d["zone_id"] = self.zone_id
        if self.channel_preference: d["channel_preference"] = self.channel_preference
        return d

@dataclass
class WedeSyncBatch:
    events: List[WedeEvent]
    captured_at: str
    device_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "events": [e.to_dict() for e in self.events],
            "captured_at": self.captured_at,
        }
        if self.device_id: d["device_id"] = self.device_id
        return d

@dataclass
class WedeParserField:
    id: str
    name: str
    sms_code: str
    type: str
    required: bool
    enabled: bool
    offline_capable: bool
    section: str
    max_bytes: int
    description: Optional[str] = None
    enum_values: Optional[List[str]] = None
    legal: Optional[bool] = None
    custom: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "name": self.name,
            "sms_code": self.sms_code,
            "type": self.type,
            "required": self.required,
            "enabled": self.enabled,
            "offline_capable": self.offline_capable,
            "section": self.section,
            "max_bytes": self.max_bytes,
        }
        if self.description: d["description"] = self.description
        if self.enum_values: d["enum_values"] = self.enum_values
        if self.legal is not None: d["legal"] = self.legal
        if self.custom is not None: d["custom"] = self.custom
        return d


from typing import Literal

MissionStatus = Literal['CREATED', 'SENT', 'ACK', 'ON_ROUTE', 'ON_SITE', 'COMPLETED', 'FAILED']


class WedeTeamMember:
    def __init__(self, id: str, team_id: str, name: str, role: str,
                 status: str, lat: float = None, lng: float = None, last_seen: str = None):
        self.id = id
        self.team_id = team_id
        self.name = name
        self.role = role
        self.status = status
        self.lat = lat
        self.lng = lng
        self.last_seen = last_seen


class WedeTeam:
    def __init__(self, id: str, tenant_id: str, name: str, type: str,
                 vertical: str, status: str, zone_id: str = None, members=None,
                 created_at: str = None, updated_at: str = None):
        self.id = id
        self.tenant_id = tenant_id
        self.name = name
        self.type = type
        self.vertical = vertical
        self.status = status
        self.zone_id = zone_id
        self.members = members or []
        self.created_at = created_at
        self.updated_at = updated_at


class WedeMission:
    def __init__(self, id: str, event_id: str, team_id: str, status: str,
                 channel_used: str, dispatched_at: str, vertical: str = None,
                 priority: str = None, payload: dict = None, feedback: dict = None,
                 notes: str = None, event_lat: float = None, event_lng: float = None,
                 on_route_at: str = None, on_site_at: str = None,
                 completed_at: str = None, failed_at: str = None):
        self.id = id
        self.event_id = event_id
        self.team_id = team_id
        self.status = status
        self.channel_used = channel_used
        self.dispatched_at = dispatched_at
        self.vertical = vertical
        self.priority = priority
        self.payload = payload
        self.feedback = feedback
        self.notes = notes
        self.event_lat = event_lat
        self.event_lng = event_lng
        self.on_route_at = on_route_at
        self.on_site_at = on_site_at
        self.completed_at = completed_at
        self.failed_at = failed_at
