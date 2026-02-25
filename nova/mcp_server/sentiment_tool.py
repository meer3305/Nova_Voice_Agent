"""Sentiment analysis utility for tone adjustment."""

from __future__ import annotations

from typing import Any, Dict

from nova.utils.logger import get_logger

logger = get_logger(__name__)


class SentimentTool:
    """Simple sentiment analyzer (replaceable by a model API)."""

    def analyze_text(self, text: str) -> Dict[str, Any]:
        logger.info("sentiment.analyze_text len=%s", len(text))
        lowered = text.lower()
        if any(k in lowered for k in ["angry", "urgent", "frustrated", "upset"]):
            sentiment = "negative"
            tone = "empathetic and concise"
        elif any(k in lowered for k in ["great", "thanks", "awesome", "happy"]):
            sentiment = "positive"
            tone = "friendly and upbeat"
        else:
            sentiment = "neutral"
            tone = "professional and calm"

        return {"sentiment": sentiment, "recommended_tone": tone}
