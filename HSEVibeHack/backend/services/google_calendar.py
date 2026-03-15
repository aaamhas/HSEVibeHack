from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
from typing import Optional
import os


def get_calendar_service(access_token: str):
    """Create a Google Calendar service with user's access token"""
    credentials = Credentials(token=access_token)
    return build("calendar", "v3", credentials=credentials)


def add_hackathon_to_calendar(
    access_token: str,
    title: str,
    start_date: datetime,
    end_date: Optional[datetime] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
):
    """Add a hackathon event to user's Google Calendar"""
    try:
        service = get_calendar_service(access_token)

        if end_date is None:
            end_date = start_date + timedelta(hours=1)

        event = {
            "summary": title,
            "description": description or "",
            "location": location or "",
            "start": {"dateTime": start_date.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_date.isoformat(), "timeZone": "UTC"},
        }

        created_event = service.events().insert(calendarId="primary", body=event).execute()
        return {"success": True, "event_id": created_event.get("id")}

    except Exception as e:
        return {"success": False, "error": str(e)}


def remove_hackathon_from_calendar(access_token: str, event_id: str):
    """Remove a hackathon event from user's Google Calendar"""
    try:
        service = get_calendar_service(access_token)
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_calendar_events(access_token: str, max_results: int = 10):
    """Get upcoming events from user's Google Calendar"""
    try:
        service = get_calendar_service(access_token)

        now = datetime.utcnow().isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        return {"success": True, "events": events_result.get("items", [])}

    except Exception as e:
        return {"success": False, "error": str(e)}
