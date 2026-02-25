"""Online ordering tool with Playwright automation for semi-automated checkout."""

from __future__ import annotations

from typing import Any, Dict

import requests

from nova.automation.playwright_engine import PlaywrightEngine
from nova.utils.logger import get_logger

logger = get_logger(__name__)


class OrderTool:
    """Tool wrapper for semi-automated food ordering."""

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

    async def prepare_order(
        self,
        site_url: str,
        item: str,
        quantity: int = 1,
        add_to_cart_selector: str = "button[data-test='add-to-cart']",
    ) -> Dict[str, Any]:
        """
        Prepare food order (semi-automated - stops before payment).
        
        This navigates to the ordering site, searches for item, adds to cart,
        and stops at checkout page for user to review and complete payment.
        """
        logger.info(f"order.prepare_order item={item} qty={quantity}")

        try:
            if not await self._init_engine():
                return {
                    "status": "error",
                    "message": "Playwright not available - install with: pip install playwright && playwright install",
                    "item": item,
                    "quantity": quantity,
                }

            result = await self.engine.order_prepare_checkout(
                site_url=site_url,
                search_term=item,
                add_to_cart_selector=add_to_cart_selector
            )
            result["quantity"] = quantity
            await self.engine.close()
            return result
        except Exception as exc:
            logger.exception(f"Order preparation failed: {exc}")
            if self.engine:
                try:
                    await self.engine.close()
                except:
                    pass
            return {
                "status": "error",
                "message": str(exc),
                "item": item,
                "quantity": quantity,
            }

    def prepare_order_sync(
        self,
        site_url: str,
        item: str,
        quantity: int = 1,
        add_to_cart_selector: str = "button[data-test='add-to-cart']",
    ) -> Dict[str, Any]:
        """Synchronous wrapper for prepare_order."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context
                return {
                    "status": "error",
                    "message": "Cannot run async automation in current context",
                    "item": item,
                }
        except RuntimeError:
            pass

        try:
            return asyncio.run(
                self.prepare_order(
                    site_url=site_url,
                    item=item,
                    quantity=quantity,
                    add_to_cart_selector=add_to_cart_selector
                )
            )
        except Exception as exc:
            logger.exception(f"Sync wrapper failed: {exc}")
            return {
                "status": "error",
                "message": str(exc),
                "item": item,
                "quantity": quantity,
            }

    def place_order(
        self,
        item: str,
        quantity: int,
        destination: str,
        api_url: str | None = None,
    ) -> Dict[str, Any]:
        """
        Fallback: place order via API (if provider API is configured).
        
        For production, would connect to actual ordering service APIs
        like Swiggy, Zomato, Blinkit, etc.
        """
        payload = {
            "item": item,
            "quantity": quantity,
            "destination": destination,
        }
        logger.info(f"order.place_order {payload}")

        if not api_url:
            return {
                "status": "simulated",
                "order_id": "ord-1001",
                "payload": payload,
                "detail": "No provider API URL configured; order simulated. For semi-automated flow, use prepare_order_sync() instead.",
            }

        try:
            response = requests.post(f"{api_url}/orders", json=payload, timeout=8)
            response.raise_for_status()
            data = response.json()
            return {"status": "submitted", "order": data}
        except requests.RequestException as exc:
            logger.exception("Order API failed")
            return {"status": "error", "error": str(exc), "payload": payload}

