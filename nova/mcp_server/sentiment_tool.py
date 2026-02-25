"""Sentiment analysis tool with Groq LLM support."""

from __future__ import annotations

from typing import Any, Dict

from nova.config import get_settings
from nova.utils.logger import get_logger

logger = get_logger(__name__)


class SentimentTool:
    """Sentiment analyzer for tone adjustment."""

    def _llm_sentiment(self, text: str) -> Dict[str, Any]:
        """Use Groq to analyze sentiment with LLM."""
        settings = get_settings()
        if not settings.groq_api_key:
            return self._rule_based_sentiment(text)

        try:
            from groq import Groq

            client = Groq(api_key=settings.groq_api_key)
            system = (
                "You are a sentiment analyzer. Analyze the sentiment of the user input. "
                "Return a JSON object with: sentiment (positive/negative/neutral), "
                "confidence (0-1), and recommended_tone (professional/empathetic/friendly/casual/urgent). "
                "Be concise."
            )

            response = client.chat.completions.create(
                model=settings.groq_model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )

            import json
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return {
                "sentiment": result.get("sentiment", "neutral"),
                "confidence": result.get("confidence", 0.5),
                "recommended_tone": result.get("recommended_tone", "professional"),
                "source": "llm",
            }
        except ImportError:
            logger.warning("Groq library not installed")
            return self._rule_based_sentiment(text)
        except Exception as exc:
            logger.warning(f"LLM sentiment analysis failed: {exc}, falling back to rule-based")
            return self._rule_based_sentiment(text)

    def _rule_based_sentiment(self, text: str) -> Dict[str, Any]:
        """Fallback rule-based sentiment analysis."""
        lowered = text.lower()

        # Negative keywords
        negative_keywords = [
            "angry", "frustrated", "upset", "sad", "disappointed",
            "hate", "terrible", "awful", "horrible", "bad", "worst"
        ]
        # Positive keywords
        positive_keywords = [
            "happy", "great", "awesome", "excellent", "wonderful",
            "love", "fantastic", "amazing", "best", "thanks", "grateful"
        ]
        # Urgent keywords
        urgent_keywords = [
            "urgent", "asap", "immediately", "emergency", "critical",
            "now", "quickly", "right away"
        ]

        negative_count = sum(1 for kw in negative_keywords if kw in lowered)
        positive_count = sum(1 for kw in positive_keywords if kw in lowered)
        urgent_count = sum(1 for kw in urgent_keywords if kw in lowered)

        # Determine sentiment
        if negative_count > positive_count:
            sentiment = "negative"
            tone = "empathetic and concise"
        elif positive_count > negative_count:
            sentiment = "positive"
            tone = "friendly and upbeat"
        else:
            sentiment = "neutral"
            tone = "professional and calm"

        # Override tone if urgent
        if urgent_count > 0:
            tone = "urgent and action-focused"

        # Estimate confidence (simple heuristic)
        total_keywords = negative_count + positive_count + urgent_count
        confidence = min(0.95, 0.5 + (total_keywords * 0.1))

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "recommended_tone": tone,
            "source": "rule-based",
        }

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment and recommend tone."""
        logger.info(f"sentiment.analyze_text len={len(text)}")

        result = {
            "text_length": len(text),
            "word_count": len(text.split()),
        }

        # Try LLM first, fall back to rules
        analysis = self._llm_sentiment(text)
        result.update(analysis)

        logger.info(
            f"Sentiment: {result['sentiment']}, "
            f"Confidence: {result.get('confidence', 0):.2f}, "
            f"Tone: {result['recommended_tone']}"
        )

        return result

