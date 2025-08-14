from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Request Models
class EventCreateRequest(BaseModel):
    summary: str = Field(..., description="Short summary of the event", example="Team Meeting")
    description: Optional[str] = Field(None, description="Detailed description of the event", example="Monthly sync-up")
    start: datetime = Field(..., description="Start time in UTC (RFC3339 format)", example="2024-07-01T10:00:00Z")
    end: datetime = Field(..., description="End time in UTC (RFC3339 format)", example="2024-07-01T11:00:00Z")

class EventUpdateRequest(BaseModel):
    event_id: str = Field(..., description="Unique ID of the event to update", example="abc123def456")
    summary: Optional[str] = Field(None, description="Updated summary")
    description: Optional[str] = Field(None, description="Updated description")
    start: Optional[datetime] = Field(None, description="Updated start time in UTC (RFC3339 format)")
    end: Optional[datetime] = Field(None, description="Updated end time in UTC (RFC3339 format)")

class EventDeleteRequest(BaseModel):
    event_id: str = Field(..., description="ID of the event to delete")

# Data Models
class EventResponse(BaseModel):
    id: str
    summary: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime

# API Response Models
class ListEventsResponse(BaseModel):
    success: bool = Field(..., description="Whether the event listing was successful")
    events: List[EventResponse] = Field(default_factory=list, description="List of events retrieved from Google Calendar")
    error: Optional[str] = Field(None, description="Error message if the operation failed")

class CreateEventResponse(BaseModel):
    success: bool = Field(..., description="Whether the event creation was successful")
    event: Optional[EventResponse] = Field(None, description="Details of the created event (if successful)")
    error: Optional[str] = Field(None, description="Error message if the operation failed")

class UpdateEventResponse(BaseModel):
    success: bool = Field(..., description="Whether the event update was successful")
    event: Optional[EventResponse] = Field(None, description="Details of the updated event (if successful)")
    error: Optional[str] = Field(None, description="Error message if the operation failed")

class DeleteEventResponse(BaseModel):
    success: bool = Field(..., description="Whether the event deletion was successful")
    event_id: Optional[str] = Field(None, description="ID of the deleted event")
    error: Optional[str] = Field(None, description="Error message if the operation failed") 