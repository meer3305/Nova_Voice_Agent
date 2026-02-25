"""Online ordering tool with real API-ready HTTP call structure."""

from __future__ import annotations

from typing import Any, Dict

import requests

from nova.utils.logger import get_logger

logger = get_logger(__name__)


class OrderTool:
    """Simulated ordering workflow with production HTTP contract."""

    def place_order(
        self,
        item: str,
        quantity: int,
        destination: str,
        api_url: str | None = None,
    ) -> Dict[str, Any]:
        payload = {
            "item": item,
            "quantity": quantity,
            "destination": destination,
        }
        logger.info("order.place_order %s", payload)

        if not api_url:
            return {
                "status": "simulated",
                "order_id": "ord-1001",
                "payload": payload,
                "detail": "No provider API URL configured; order simulated.",
            }

        try:
            response = requests.post(f"{api_url}/orders", json=payload, timeout=8)
            response.raise_for_status()
            data = response.json()
            return {"status": "submitted", "order": data}
        except requests.RequestException as exc:
            logger.exception("Order API failed")
            return {"status": "error", "error": str(exc), "payload": payload}
