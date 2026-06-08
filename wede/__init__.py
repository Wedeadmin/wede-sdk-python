from .client import WedeClient
from .errors import WedeError, WedeAuthError, WedeNetworkError, WedeValidationError
from .types import WedeEvent, WedeSyncBatch, WedeParserField

__all__ = [
    "WedeClient",
    "WedeError",
    "WedeAuthError",
    "WedeNetworkError",
    "WedeValidationError",
    "WedeEvent",
    "WedeSyncBatch",
    "WedeParserField",
]
__version__ = "0.1.0"

from .score_engine import score_teams, haversine_km, point_in_polygon, TeamInput, EventInput, ScoredTeam, GeoPoint
from .cache import WedeCache, DictStorage
from .offline_dispatch import WedeOfflineDispatch, WedeDeviceId, OfflineDispatchRequest, DispatchOfflineResult
