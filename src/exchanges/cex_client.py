from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import ccxt.async_support as ccxt
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import ExchangeKeys
from src.risk import TokenBucket

logger = structlog.get_logger(__name__)


@dataclass
class OrderBook:
    bids: List[Tuple[float, float]]
    asks: List[Tuple[float, float]]

    @property
    def mid(self) -> Optional[float]:
        if not self.bids or not self.asks:
            return None
        return (self.bids[0][0] + self.asks[0][0]) / 2


class CexClient:
    """
    Thin wrapper around ccxt for a single exchange.
    Handles:
    - authenticated REST (balance, orders)
    - orderbook polling fallback (if websocket not used)
    - simple rate limiting via TokenBucket
    """

    def __init__(self, keys: ExchangeKeys, rate_limit_per_sec: int = 20) -> None:
        self.keys = keys
        self.bucket = TokenBucket(rate=rate_limit_per_sec)
        exchange_class = getattr(ccxt, keys.name)
        self.exchange = exchange_class(
            {
                "apiKey": keys.api_key,
                "secret": keys.secret_key,
                "password": keys.password,
                "enableRateLimit": False,
            }
        )
        if keys.testnet and hasattr(self.exchange, "set_sandbox_mode"):
            self.exchange.set_sandbox_mode(True)

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(5))
    async def fetch_order_book(self, symbol: str, limit: int = 50) -> OrderBook:
        async with self.bucket.acquire():
            raw = await self.exchange.fetch_order_book(symbol, limit)
        book = OrderBook(
            bids=[(b[0], b[1]) for b in raw.get("bids", [])],
            asks=[(a[0], a[1]) for a in raw.get("asks", [])],
        )
        return book

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(5))
    async def fetch_balance(self) -> Dict[str, Any]:
        async with self.bucket.acquire():
            return await self.exchange.fetch_balance()

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(5))
    async def create_limit_order(
        self, symbol: str, side: str, amount: float, price: float
    ) -> Dict[str, Any]:
        async with self.bucket.acquire():
            logger.info("mm_send_order", symbol=symbol, side=side, amount=amount, price=price)
            return await self.exchange.create_limit_order(symbol, side, amount, price)

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(5))
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        async with self.bucket.acquire():
            logger.info("mm_cancel_order", order_id=order_id, symbol=symbol)
            return await self.exchange.cancel_order(order_id, symbol)

    async def cancel_all(self, symbol: str) -> None:
        open_orders = await self.exchange.fetch_open_orders(symbol)
        for order in open_orders:
            try:
                await self.cancel_order(order["id"], symbol)
            except Exception as exc:
                logger.warning("cancel_failed", order_id=order["id"], error=str(exc))

    async def close(self) -> None:
        await self.exchange.close()


