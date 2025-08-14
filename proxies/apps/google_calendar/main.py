from fastapi import APIRouter, Request, HTTPException, status
from typing import List
import json
from .client.calendar_client import CalendarClient
from .schemas.calendar import (
    EventCreateRequest, EventUpdateRequest, EventDeleteRequest,
    EventResponse, ListEventsResponse, CreateEventResponse, UpdateEventResponse, DeleteEventResponse
)

google_calendar_router = APIRouter(prefix="/calendar", tags=["Google Calendar"])

def get_calendar_client(request: Request) -> CalendarClient:
    auth_json = request.headers.get("X-Auth")
    time_zone = request.headers.get("X-TimeZone")
    if not auth_json:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication header (X-Auth)")
    try:
        auth_dict = json.loads(auth_json)
        return CalendarClient(auth_dict, time_zone)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to initialize Calendar client: {str(e)}")

@google_calendar_router.get("/events", response_model=ListEventsResponse, summary="List upcoming events", response_description="List of upcoming events")
async def list_events(request: Request):
    """Get a list of upcoming events from the user's Google Calendar."""
    try:
        client = get_calendar_client(request)
        events = client.list_events()
        event_objs = [
            EventResponse(
                id=e["id"],
                summary=e.get("summary", ""),
                description=e.get("description"),
                start_time=client.parse_event_time(e["start"]),
                end_time=client.parse_event_time(e["end"])
            ) for e in events if ("dateTime" in e["start"] or "date" in e["start"])
        ]
        return ListEventsResponse(success=True, events=event_objs)
    except Exception as e:
        return ListEventsResponse(success=False, error=str(e))

@google_calendar_router.post("/events", response_model=CreateEventResponse, summary="Create a new event", response_description="Created event details")
async def create_event(request: Request, event: EventCreateRequest):
    """Create a new event in the user's Google Calendar."""
    try:
        client = get_calendar_client(request)
        result = client.create_event(event.summary, event.description, event.start, event.end)
        event_obj = EventResponse(
            id=result["id"],
            summary=result["summary"],
            description=result.get("description"),
            start_time=client.parse_event_time(result["start"]),
            end_time=client.parse_event_time(result["end"])
        )
        return CreateEventResponse(success=True, event=event_obj)
    except Exception as e:
        return CreateEventResponse(success=False, error=str(e))

@google_calendar_router.put("/events", response_model=UpdateEventResponse, summary="Update an event", response_description="Updated event details")
async def update_event(request: Request, event: EventUpdateRequest):
    """Update an existing event in the user's Google Calendar."""
    try:
        client = get_calendar_client(request)
        updated = client.update_event(event.event_id, event.summary, event.description, event.start, event.end)
        event_obj = EventResponse(
            id=updated["id"],
            summary=updated["summary"],
            description=updated.get("description"),
            start_time=client.parse_event_time(updated["start"]),
            end_time=client.parse_event_time(updated["end"])
        )
        return UpdateEventResponse(success=True, event=event_obj)
    except Exception as e:
        return UpdateEventResponse(success=False, error=str(e))

@google_calendar_router.delete("/events", response_model=DeleteEventResponse, summary="Delete an event", response_description="Event deleted message")
async def delete_event(request: Request, event: EventDeleteRequest):
    """Delete an existing event from the user's Google Calendar."""
    try:
        client = get_calendar_client(request)
        client.delete_event(event.event_id)
        return DeleteEventResponse(success=True, event_id=event.event_id)
    except Exception as e:
        return DeleteEventResponse(success=False, error=str(e)) 