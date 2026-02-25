"""Gmail tool adapter (API-ready with safe fallbacks)."""

from __future__ import annotations

from typing import Any, Dict, List

from nova.utils.logger import get_logger

logger = get_logger(__name__)


class GmailTool:
    """Tool wrapper for Gmail actions."""

    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        logger.info("gmail.send_email to=%s subject=%s", to, subject)
        # Integration placeholder (Google API client can be injected here)
        return {
            "status": "sent",
            "to": to,
            "subject": subject,
            "message_id": "mock-msg-123",
            "preview": body[:120],
        }

    def read_unread_important(self) -> Dict[str, List[Dict[str, str]]]:
        logger.info("gmail.read_unread_important")
        # Replace with Gmail API query label:important is:unread
        return {
            "emails": [
                {
                    "from": "manager@example.com",
                    "subject": "Quarterly roadmap check-in",
                    "snippet": "Please review the updated milestones.",
                }
            ]
        }
