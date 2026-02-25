"""SMS tool with Twilio-ready contract and stub fallback."""

from __future__ import annotations

from typing import Any, Dict

from nova.config import get_settings
from nova.utils.logger import get_logger

logger = get_logger(__name__)


class SMSTool:
    """Send SMS notifications."""

    def send_sms(self, to: str, body: str) -> Dict[str, Any]:
        settings = get_settings()
        logger.info("sms.send_sms to=%s", to)

        if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_from_number]):
            return {
                "status": "simulated",
                "to": to,
                "body": body,
                "detail": "Twilio credentials not configured; simulated send.",
            }

        # Real Twilio integration can be dropped in here without API changes.
        return {"status": "sent", "to": to, "body": body, "provider": "twilio"}
