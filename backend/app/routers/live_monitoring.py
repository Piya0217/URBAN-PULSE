from threading import Lock

from fastapi import APIRouter

from src.urban_pulse.streaming.event_generator import (
    create_event,
    create_initial_events,
)


router = APIRouter(
    prefix="/api/live",
    tags=["Live Traffic Monitoring"],
)


# These are simulated events generated when this router is loaded.
event_store = create_initial_events()
MAX_EVENTS = 60
event_store_lock = Lock()


@router.get("/events")
def get_live_events():
    """Return the simulated events, newest first."""
    # Copy the already newest-first store while holding the lock so the
    # response count and data represent the same state.
    with event_store_lock:
        events = list(event_store)

    return {
        "status": "success",
        "count": len(events),
        "data": events,
    }


@router.post("/events/next")
def create_next_live_event():
    """Generate and store one new simulated event."""
    # Generate and insert together so concurrent requests preserve the
    # newest-first order of the event store.
    with event_store_lock:
        new_event = create_event()
        event_store.insert(0, new_event)
        del event_store[MAX_EVENTS:]

    return {
        "status": "success",
        "count": 1,
        "data": new_event,
    }
