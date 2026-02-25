"""Calendar tool adapter (API-ready)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from nova.utils.logger import get_logger

logger = get_logger(__name__)


class CalendarTool:
    """Tool wrapper for calendar actions."""

    def create_event(self, title: str, start_time: str, end_time: str, attendees: List[str] | None = None) -> Dict[str, Any]:
        logger.info("calendar.create_event title=%s start=%s", title, start_time)
        return {
            "status": "created",
            "event_id": "evt-001",
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees or [],
        }

    def upcoming_events(self, within_minutes: int = 120) -> Dict[str, Any]:
        logger.info("calendar.upcoming_events within_minutes=%s", within_minutes)
        now = datetime.utcnow()
        event_time = (now + timedelta(minutes=30)).isoformat()
        return {
            "events": [
                {
                    "title": "Design sync",
                    "start_time": event_time,
                    "location": "Teams",
                }
            ]
        }
