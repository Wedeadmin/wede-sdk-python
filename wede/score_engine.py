"""
Wede Proximity Score Engine — Python SDK
Identical algorithm to backend scoreEngine.ts and JS/RN/Android/Swift SDKs.
No external dependencies. Pure Python. Works fully offline.
Patent INPI 120488 — Claim 5: local scoring without connectivity.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone


@dataclass
class GeoPoint:
    lat: float
    lng: float


@dataclass
class TeamMemberInput:
    id: str
    status: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    last_seen: Optional[str] = None


@dataclass
class TeamEquipmentInput:
    code: str
    status: str


@dataclass
class TeamVerticalInput:
    vertical: str
    event_types: List[str] = field(default_factory=list)


@dataclass
class TeamInput:
    id: str
    name: str
    status: str
    vertical: str
    equipment: List[str] = field(default_factory=list)
    zone_lat: Optional[float] = None
    zone_lng: Optional[float] = None
    zone_boundary: Optional[List[GeoPoint]] = None
    members: List[TeamMemberInput] = field(default_factory=list)
    verticals: Optional[List[TeamVerticalInput]] = None
    team_equipment: Optional[List[TeamEquipmentInput]] = None


@dataclass
class EventInput:
    lat: float
    lng: float
    vertical: Optional[str] = None
    event_type: Optional[str] = None
    priority: Optional[str] = None
    required_equipment: Optional[List[str]] = None


@dataclass
class TeamPosition:
    lat: float
    lng: float
    source: str
    last_seen: Optional[str] = None


@dataclass
class ScoredTeam:
    team_id: str
    team_name: str
    status: str
    vertical: str
    distance_km: float
    eta_min: int
    equipment_match: float
    member_availability: float
    score: float
    recommended: bool
    channel: str
    position: TeamPosition


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    d_lat = (lat2 - lat1) * math.pi / 180
    d_lng = (lng2 - lng1) * math.pi / 180
    a = math.sin(d_lat / 2) ** 2 +         math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * math.sin(d_lng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def point_in_polygon(lat: float, lng: float, polygon: List[GeoPoint]) -> bool:
    if len(polygon) < 3:
        return False
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i].lng, polygon[i].lat
        xj, yj = polygon[j].lng, polygon[j].lat
        intersect = ((yi > lat) != (yj > lat)) and             (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside


def _resolve_position(team: TeamInput) -> TeamPosition:
    now = datetime.now(timezone.utc)
    ten_min = 600  # seconds

    fresh = []
    for m in team.members:
        if m.status == "available" and m.lat is not None and m.lng is not None and m.last_seen:
            try:
                ts = datetime.fromisoformat(m.last_seen.replace("Z", "+00:00"))
                if (now - ts).total_seconds() < ten_min:
                    fresh.append(m)
            except Exception:
                pass

    if fresh:
        best = max(fresh, key=lambda m: m.last_seen or "")
        return TeamPosition(lat=best.lat, lng=best.lng, source="gps", last_seen=best.last_seen)

    any_gps = next((m for m in team.members if m.lat is not None and m.lng is not None), None)
    if any_gps:
        return TeamPosition(lat=any_gps.lat, lng=any_gps.lng, source="gps", last_seen=any_gps.last_seen)

    if team.zone_lat is not None and team.zone_lng is not None:
        return TeamPosition(lat=team.zone_lat, lng=team.zone_lng, source="zone")

    return TeamPosition(lat=0.0, lng=0.0, source="unknown")


def _resolve_channel(eta_min: int, priority: Optional[str]) -> str:
    if priority in ("P1_CRITICAL", "CRITICAL"):
        return "sms" if eta_min > 5 else "internet"
    return "sms" if eta_min > 15 else "internet"


def score_teams(teams: List[TeamInput], evt: EventInput) -> List[ScoredTeam]:
    available = [t for t in teams if t.status in ("available", "on_mission")]
    scored = []

    for team in available:
        pos = _resolve_position(team)

        distance_km = 0.0
        if pos.source != "unknown":
            distance_km = round(haversine_km(pos.lat, pos.lng, evt.lat, evt.lng), 2)
        eta_min = round(distance_km / 0.7)

        member_avail = (
            len([m for m in team.members if m.status == "available"]) / len(team.members)
            if team.members else 0.0
        )

        operational_equip = (
            [e.code for e in team.team_equipment if e.status == "operational"]
            if team.team_equipment else team.equipment
        )
        required = evt.required_equipment or []
        if required:
            equipment_match = len([e for e in required if e in operational_equip]) / len(required)
        elif operational_equip:
            equipment_match = 0.8
        else:
            equipment_match = 0.5

        in_zone = (
            point_in_polygon(evt.lat, evt.lng, team.zone_boundary)
            if team.zone_boundary and len(team.zone_boundary) >= 3 else True
        )
        geofence_penalty = 0.0 if in_zone else 0.2

        covers_vertical = (
            not evt.vertical or team.vertical == evt.vertical or
            any(v.vertical == evt.vertical for v in (team.verticals or []))
        )
        covers_event_type = (
            not evt.event_type or
            any(evt.event_type in v.event_types for v in (team.verticals or []))
        ) if team.verticals else True
        capability_bonus = 0.0 if (covers_vertical and covers_event_type) else 0.3

        travel_score = min(eta_min / 30.0, 1.0)
        cap_score = (1 - equipment_match) + capability_bonus
        member_score = 1 - member_avail
        load_penalty = 0.5 if team.status == "on_mission" else 0.0

        final_score = (
            0.35 * travel_score + 0.25 * cap_score +
            0.2 * member_score + 0.1 * load_penalty + 0.1 * geofence_penalty
        )

        scored.append(ScoredTeam(
            team_id=team.id, team_name=team.name, status=team.status,
            vertical=team.vertical, distance_km=distance_km, eta_min=eta_min,
            equipment_match=round(equipment_match, 2),
            member_availability=round(member_avail, 2),
            score=round(final_score, 4),
            recommended=False,
            channel=_resolve_channel(eta_min, evt.priority),
            position=pos
        ))

    scored.sort(key=lambda t: t.score, reverse=True)
    if scored:
        scored[0].recommended = True
    return scored
