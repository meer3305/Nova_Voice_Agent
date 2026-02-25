"""LinkedIn tool with Playwright automation for semi-automated posting."""

from __future__ import annotations

from typing import Any, Dict

from nova.automation.playwright_engine import PlaywrightEngine
from nova.utils.logger import get_logger

logger = get_logger(__name__)


class LinkedInTool:
    """Tool wrapper for LinkedIn semi-automated actions."""

    def __init__(self) -> None:
        self.engine = None

    async def _init_engine(self) -> bool:
        """Initialize browser engine."""
        try:
            self.engine = PlaywrightEngine(headless=False)
            await self.engine.init()
            return True
        except Exception as exc:
            logger.warning(f"Failed to initialize Playwright: {exc}")
            return False

    async def prepare_post(self, content: str) -> Dict[str, Any]:
        """
        Prepare LinkedIn post (semi-automated - stops before publish).
        
        This opens LinkedIn, navigates to post composer, inserts content,
        and waits for user to manually review and click publish.
        """
        logger.info(f"linkedin.prepare_post len={len(content)}")

        try:
            if not await self._init_engine():
                return {
                    "status": "error",
                    "message": "Playwright not available - install with: pip install playwright && playwright install",
                    "platform": "linkedin",
                }

            result = await self.engine.linkedin_prepare_post(content)
            await self.engine.close()
            return result
        except Exception as exc:
            logger.exception(f"LinkedIn preparation failed: {exc}")
            if self.engine:
                try:
                    await self.engine.close()
                except:
                    pass
            return {
                "status": "error",
                "message": str(exc),
                "platform": "linkedin",
            }

    def prepare_post_sync(self, content: str) -> Dict[str, Any]:
        """Synchronous wrapper for prepare_post."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context - return error
                return {
                    "status": "error",
                    "message": "Cannot run async automation in current context",
                    "platform": "linkedin",
                }
        except RuntimeError:
            pass

        try:
            return asyncio.run(self.prepare_post(content))
        except Exception as exc:
            logger.exception(f"Sync wrapper failed: {exc}")
            return {
                "status": "error",
                "message": str(exc),
                "platform": "linkedin",
            }
