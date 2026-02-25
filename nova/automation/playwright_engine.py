"""Playwright-based browser automation engine for semi-automated actions."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from nova.utils.logger import get_logger

logger = get_logger(__name__)


class PlaywrightEngine:
    """Headless browser automation using Playwright."""

    def __init__(self, headless: bool = True, timeout: int = 30000) -> None:
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.page = None

    async def init(self) -> None:
        """Initialize browser and context."""
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            logger.info("Playwright engine initialized")
        except ImportError:
            logger.warning("Playwright not installed - browser automation unavailable")
            raise ImportError("Please install playwright: pip install playwright")

    async def close(self) -> None:
        """Close browser."""
        if self.browser:
            await self.browser.close()
            logger.info("Playwright engine closed")

    async def goto(self, url: str) -> None:
        """Navigate to URL."""
        if not self.page:
            raise RuntimeError("Engine not initialized")
        await self.page.goto(url)
        logger.info(f"Navigated to {url}")

    async def fill(self, selector: str, text: str) -> None:
        """Fill form field."""
        if not self.page:
            raise RuntimeError("Engine not initialized")
        await self.page.fill(selector, text)
        logger.info(f"Filled {selector}")

    async def click(self, selector: str) -> None:
        """Click element."""
        if not self.page:
            raise RuntimeError("Engine not initialized")
        await self.page.click(selector)
        logger.info(f"Clicked {selector}")

    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> None:
        """Wait for element."""
        if not self.page:
            raise RuntimeError("Engine not initialized")
        await self.page.wait_for_selector(selector, timeout=timeout)

    async def get_screenshot(self, path: str) -> None:
        """Take screenshot."""
        if not self.page:
            raise RuntimeError("Engine not initialized")
        await self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")

    async def linkedin_prepare_post(self, content: str) -> Dict[str, Any]:
        """
        Prepare LinkedIn post (semi-automated - stops before publish).
        
        Steps:
        1. Login to LinkedIn (requires manual intervention or stored cookies)
        2. Click 'Start a post'
        3. Insert generated content
        4. Wait for user review
        5. Return status
        """
        try:
            await self.goto("https://www.linkedin.com/feed/")
            
            # Wait for page load
            await self.wait_for_selector("svg[data-test-icon='post-icon']", timeout=5000)
            
            # Click "Start a post"
            await self.click("svg[data-test-icon='post-icon']")
            
            # Wait for modal
            await self.wait_for_selector("[contenteditable='true']", timeout=5000)
            
            # Insert content
            await self.click("[contenteditable='true']")
            await self.page.keyboard.type(content)
            
            return {
                "status": "ready_for_publish",
                "message": "Post prepared - review and publish manually",
                "platform": "linkedin",
                "content_length": len(content),
            }
        except Exception as exc:
            logger.exception("LinkedIn automation failed")
            return {
                "status": "error",
                "message": str(exc),
                "platform": "linkedin",
            }

    async def order_prepare_checkout(
        self, 
        site_url: str,
        search_term: str,
        add_to_cart_selector: str
    ) -> Dict[str, Any]:
        """
        Prepare food order (semi-automated - stops before payment).
        
        Steps:
        1. Navigate to site
        2. Search for item
        3. Add to cart
        4. Go to checkout
        5. Return status (stop before payment)
        """
        try:
            await self.goto(site_url)
            
            # Search for item
            search_selector = "input[placeholder*='search'], input[type='search']"
            await self.wait_for_selector(search_selector, timeout=5000)
            await self.fill(search_selector, search_term)
            await self.page.keyboard.press("Enter")
            
            # Wait for results
            await self.page.wait_for_timeout(2000)
            
            # Click first result's add to cart
            await self.click(add_to_cart_selector)
            
            # Go to cart
            await self.page.goto(f"{site_url}/cart")
            
            # Wait for checkout button
            checkout_selector = "button:has-text('Proceed to Checkout'), button:has-text('Checkout')"
            await self.wait_for_selector(checkout_selector, timeout=5000)
            
            return {
                "status": "ready_for_checkout",
                "message": "Order ready - review shipping and complete payment manually",
                "item": search_term,
                "next_action": "Review cart and proceed with payment",
            }
        except Exception as exc:
            logger.exception("Order automation failed")
            return {
                "status": "error",
                "message": str(exc),
                "item": search_term,
            }


# Async wrapper for sync context
def run_async_browser_action(coro):
    """Run async function in current event loop or create new one."""
    try:
        loop = asyncio.get_running_loop()
        # Already in async context - this shouldn't normally happen in FastAPI
        return asyncio.create_task(coro)
    except RuntimeError:
        # No async context - create new loop
        return asyncio.run(coro)
