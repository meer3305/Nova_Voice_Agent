"""Gmail tool adapter with OAuth support."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from nova.config import get_settings
from nova.utils.logger import get_logger

logger = get_logger(__name__)


class GmailTool:
    """Tool wrapper for Gmail actions using Google API."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.service = self._init_gmail_service()

    def _init_gmail_service(self) -> Optional[Any]:
        """Initialize Gmail API service."""
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
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
                # Use refresh token from env
                creds = Credentials(
                    token=None,
                    refresh_token=self.settings.gmail_refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.settings.gmail_client_id,
                    client_secret=self.settings.gmail_client_secret,
                )
                creds.refresh(Request())
                
                # Save token
                with open(token_path, "wb") as token_file:
                    pickle.dump(creds, token_file)

            if creds:
                return build("gmail", "v1", credentials=creds)
            else:
                logger.warning("Gmail credentials not available")
                return None
        except ImportError:
            logger.warning("Google Auth libraries not installed")
            return None
        except Exception as exc:
            logger.exception(f"Failed to initialize Gmail service: {exc}")
            return None

    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email via Gmail API."""
        logger.info(f"gmail.send_email to={to} subject={subject}")
        
        if not self.service:
            logger.warning("Gmail service not available - using simulated response")
            return {
                "status": "simulated",
                "to": to,
                "subject": subject,
                "message": "Gmail credentials not configured",
                "preview": body[:100],
            }

        try:
            from email.mime.text import MIMEText
            import base64

            # Create message
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject

            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = self.service.users().messages().send(
                userId="me",
                body={"raw": raw_message}
            ).execute()

            logger.info(f"Email sent: {result.get('id')}")
            return {
                "status": "sent",
                "to": to,
                "subject": subject,
                "message_id": result.get("id"),
                "preview": body[:100],
            }
        except Exception as exc:
            logger.exception(f"Email send failed: {exc}")
            return {
                "status": "error",
                "to": to,
                "error": str(exc),
            }

    def draft_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Create email draft."""
        logger.info(f"gmail.draft_email to={to} subject={subject}")
        
        if not self.service:
            logger.warning("Gmail service not available - using simulated response")
            return {
                "status": "simulated",
                "to": to,
                "subject": subject,
                "message": "Gmail credentials not configured",
            }

        try:
            from email.mime.text import MIMEText
            import base64

            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = self.service.users().drafts().create(
                userId="me",
                body={"message": {"raw": raw_message}}
            ).execute()

            logger.info(f"Draft created: {result.get('id')}")
            return {
                "status": "drafted",
                "to": to,
                "subject": subject,
                "draft_id": result.get("id"),
                "preview": body[:100],
            }
        except Exception as exc:
            logger.exception(f"Draft creation failed: {exc}")
            return {
                "status": "error",
                "to": to,
                "error": str(exc),
            }

    def read_unread_important(self, limit: int = 10) -> Dict[str, List[Dict[str, str]]]:
        """Read unread important emails."""
        logger.info("gmail.read_unread_important")
        
        if not self.service:
            logger.warning("Gmail service not available - returning mock data")
            return {
                "emails": [
                    {
                        "from": "noreply@example.com",
                        "subject": "Important notification",
                        "snippet": "This is a simulated email (Gmail not configured).",
                    }
                ]
            }

        try:
            results = self.service.users().messages().list(
                userId="me",
                q="is:unread label:important",
                maxResults=limit
            ).execute()

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                try:
                    data = self.service.users().messages().get(
                        userId="me",
                        id=msg["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject"]
                    ).execute()

                    headers = data.get("payload", {}).get("headers", [])
                    email_dict = {
                        "from": next((h["value"] for h in headers if h["name"] == "From"), "Unknown"),
                        "subject": next((h["value"] for h in headers if h["name"] == "Subject"), "No subject"),
                        "snippet": data.get("snippet", ""),
                    }
                    emails.append(email_dict)
                except Exception as exc:
                    logger.warning(f"Failed to fetch message: {exc}")

            return {"emails": emails, "count": len(emails)}
        except Exception as exc:
            logger.exception(f"Read unread failed: {exc}")
            return {"emails": [], "error": str(exc)}

