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
