"""Calendar tool adapter with Google Calendar API support."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from nova.config import get_settings
from nova.utils.logger import get_logger

logger = get_logger(__name__)


class CalendarTool:
    """Tool wrapper for Google Calendar actions."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.service = self._init_calendar_service()

    def _init_calendar_service(self) -> Optional[Any]:
        """Initialize Google Calendar API service."""
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import pickle
            import os

            creds = None
            token_path = "token.pickle"

            # Load existing token
            if os.path.exists(token_path):
                with open(token_path, "rb") as token_file:
                    creds = pickle.load(token_file)

            # Refresh if needed
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif not creds and self.settings.gmail_refresh_token:
                creds = Credentials(
                    token=None,
                    refresh_token=self.settings.gmail_refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.settings.gmail_client_id,
                    client_secret=self.settings.gmail_client_secret,
                )
                creds.refresh(Request())

            if creds:
                return build("calendar", "v3", credentials=creds)
            else:
                logger.warning("Calendar credentials not available")
                return None
        except ImportError:
            logger.warning("Google Auth libraries not installed")
            return None
        except Exception as exc:
            logger.exception(f"Failed to initialize Calendar service: {exc}")
            return None

    def create_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create calendar event."""
        logger.info(f"calendar.create_event title={title} start={start_time}")

        if not self.service:
            logger.warning("Calendar service not available - using simulated response")
            return {
                "status": "simulated",
                "event_id": "evt-simulated-001",
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "attendees": attendees or [],
                "message": "Calendar not configured",
            }

        try:
            event = {
                "summary": title,
                "start": {"dateTime": start_time},
                "end": {"dateTime": end_time},
            }

            if description:
                event["description"] = description
            if location:
                event["location"] = location
            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]

            result = self.service.events().insert(
                calendarId="primary",
                body=event
            ).execute()

            logger.info(f"Event created: {result.get('id')}")
            return {
                "status": "created",
                "event_id": result.get("id"),
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "attendees": attendees or [],
                "web_link": result.get("htmlLink"),
            }
        except Exception as exc:
            logger.exception(f"Event creation failed: {exc}")
            return {
                "status": "error",
                "title": title,
                "error": str(exc),
            }

    def upcoming_events(self, within_minutes: int = 120, limit: int = 10) -> Dict[str, Any]:
        """Get upcoming calendar events."""
        logger.info(f"calendar.upcoming_events within_minutes={within_minutes}")

        if not self.service:
            logger.warning("Calendar service not available - returning mock data")
            now = datetime.now(timezone.utc)
            event_time = (now + timedelta(minutes=30)).isoformat()
            return {
                "events": [
                    {
                        "title": "Simulated Meeting",
                        "start_time": event_time,
                        "location": "Calendar not configured",
                    }
                ]
            }

        try:
            now = datetime.utcnow()
            later = now + timedelta(minutes=within_minutes)

            results = self.service.events().list(
                calendarId="primary",
                timeMin=now.isoformat() + "Z",
                timeMax=later.isoformat() + "Z",
                maxResults=limit,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = results.get("items", [])
            formatted_events = []

            for event in events:
                start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
                end = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")

                formatted_events.append({
                    "title": event.get("summary", "No title"),
                    "start_time": start,
                    "end_time": end,
                    "location": event.get("location", ""),
                    "description": event.get("description", ""),
                })

            return {"events": formatted_events, "count": len(formatted_events)}
        except Exception as exc:
            logger.exception(f"Fetch events failed: {exc}")
            return {"events": [], "error": str(exc)}

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Delete calendar event."""
        logger.info(f"calendar.delete_event event_id={event_id}")

        if not self.service:
            return {
                "status": "simulated",
                "event_id": event_id,
                "message": "Calendar not configured",
            }

        try:
            self.service.events().delete(
                calendarId="primary",
                eventId=event_id
            ).execute()

            logger.info(f"Event deleted: {event_id}")
            return {
                "status": "deleted",
                "event_id": event_id,
            }
        except Exception as exc:
            logger.exception(f"Event deletion failed: {exc}")
            return {
                "status": "error",
                "event_id": event_id,
                "error": str(exc),
            }

