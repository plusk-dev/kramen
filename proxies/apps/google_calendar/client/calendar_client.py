import json
from datetime import datetime
from typing import Optional, List
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from fastapi import HTTPException
import pytz

class CalendarClient:
    def __init__(self, auth_json: dict, time_zone: Optional[str] = None):
        self.creds = Credentials.from_authorized_user_info(auth_json)
        self.service = build("calendar", "v3", credentials=self.creds)
        self.time_zone = time_zone

    def to_timezone(self, local_dt: datetime) -> dict:
        """
        Converts a datetime in the user's local time zone (from X-TimeZone header)
        to UTC and returns the result in Google Calendar API format.
        """
        if not self.time_zone:
            raise HTTPException(status_code=400, detail="Missing X-TimeZone header")
        try:
            tz = pytz.timezone(self.time_zone)
            print("Time zone from header: ", tz)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid time zone: {self.time_zone}")

        # If the datetime is naive, localize it to the user's timezone
        if local_dt.tzinfo is None:
            print("Local datetime has no timezone info")
            local_dt = tz.localize(local_dt)
        # The datetime is already in the user's timezone, so we can convert directly to UTC
        
        # Convert to UTC
        utc_dt = local_dt.astimezone(pytz.utc)
        print("UTC datetime: ", utc_dt)

        return {
            "dateTime": utc_dt.isoformat(),
            "timeZone": "UTC"
        }

    def parse_event_time(self, event_time: dict) -> datetime:
        if "dateTime" in event_time:
            return datetime.fromisoformat(event_time["dateTime"].replace("Z", "+00:00"))
        elif "date" in event_time:
            return datetime.fromisoformat(event_time["date"] + "T00:00:00+00:00")
        else:
            raise ValueError("Event time missing 'dateTime' and 'date'")

    def list_events(self, max_results: int = 10) -> List[dict]:
        now = datetime.now(pytz.utc).isoformat()
        events_result = (
            self.service.events()
            .list(calendarId="primary", timeMin=now, timeZone=self.time_zone, maxResults=max_results, singleEvents=True, orderBy="startTime")
            .execute()
        )
        return events_result.get("items", [])

    def create_event(self, summary: str, description: Optional[str], start: datetime, end: datetime) -> dict:
        body = {
            "summary": summary,
            "description": description,
            "start": self.to_timezone(start),
            "end": self.to_timezone(end),
        }
        return self.service.events().insert(calendarId="primary", body=body).execute()

    def update_event(self, event_id: str, summary: Optional[str], description: Optional[str], start: Optional[datetime], end: Optional[datetime]) -> dict:
        current = self.service.events().get(calendarId="primary", eventId=event_id).execute()
        if summary:
            current["summary"] = summary
        if description:
            current["description"] = description
        if start:
            current["start"] = self.to_timezone(start)
        if end:
            current["end"] = self.to_timezone(end)
        return self.service.events().update(calendarId="primary", eventId=event_id, body=current).execute()

    def delete_event(self, event_id: str):
        self.service.events().delete(calendarId="primary", eventId=event_id).execute() 