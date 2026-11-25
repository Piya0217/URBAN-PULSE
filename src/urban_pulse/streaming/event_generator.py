"""Generate simulated traffic events for URBAN PULSE.

Events and coordinates in this module are illustrative simulations. They are
not real traffic observations.
"""

import random
from datetime import datetime, timedelta, timezone
from itertools import count


EVENT_CATEGORIES = [
    "Accident",
    "Speeding",
    "Traffic congestion",
    "Signal violation",
    "Road blockage",
]

# These locations and coordinates are illustrative simulated data.
AREAS = [
    {
        "name": "Silk Board",
        "lat": 12.9177,
        "lng": 77.6233,
    },
    {
        "name": "Marathahalli",
        "lat": 12.9591,
        "lng": 77.7011,
    },
    {
        "name": "Hebbal",
        "lat": 13.0358,
        "lng": 77.597,
    },
    {
        "name": "KR Puram",
        "lat": 13.0072,
        "lng": 77.695,
    },
    {
        "name": "Whitefield",
        "lat": 12.9698,
        "lng": 77.75,
    },
    {
        "name": "Indiranagar",
        "lat": 12.9784,
        "lng": 77.6408,
    },
    {
        "name": "Hosur Road",
        "lat": 12.8956,
        "lng": 77.601,
    },
    {
        "name": "Yelahanka",
        "lat": 13.1007,
        "lng": 77.5963,
    },
]

SEVERITIES = ["Low", "Medium", "High", "Critical"]

STATUSES_BY_CATEGORY = {
    "Accident": ["Active", "Monitoring"],
    "Speeding": ["Monitoring", "Reviewed"],
    "Traffic congestion": ["Monitoring", "Active"],
    "Signal violation": ["Reviewed", "Monitoring"],
    "Road blockage": ["Active", "Monitoring"],
}

_event_sequence = count(1)


def create_event(timestamp: datetime | None = None) -> dict:
    """Create one simulated traffic event."""
    event_category = random.choice(EVENT_CATEGORIES)
    area = random.choice(AREAS)

    # Use UTC and ISO 8601 format so timestamps are consistent.
    event_time = timestamp or datetime.now(timezone.utc)

    return {
        "id": f"SIM-{next(_event_sequence):06d}",
        "eventType": event_category,
        "location": area["name"],
        "severity": random.choice(SEVERITIES),
        "timestamp": event_time.isoformat(),
        "status": random.choice(STATUSES_BY_CATEGORY[event_category]),
        "coordinates": {
            "lat": area["lat"],
            "lng": area["lng"],
        },
        "source": "simulated-stream",
    }


def create_initial_events() -> list[dict]:
    """Create four simulated events with timestamps spaced into the past."""
    current_time = datetime.now(timezone.utc)

    return [
        create_event(
            timestamp=current_time - timedelta(minutes=15 * minutes_ago)
        )
        for minutes_ago in (1, 2, 3, 4)
    ]
