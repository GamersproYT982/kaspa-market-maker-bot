from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, Optional

import structlog

from src.config import Settings
from src.core.quote_engine import QuoteEngine, QuoteConfig
from src.exchanges import CexClient, OrderBook
from src.risk import InventoryManager
from src.services import metrics

logger = structlog.get_logger(__name__)


@dataclass
class ActiveOrder:
    id: str
    side: str
    price: float
    amount: float


class MarketMaker:
    """
    Simple two-sided market maker:
    - polls orderbook
    - computes mid and quotes
    - cancels/replaces stale orders
    - adjusts size/quotes based on inventory skew
    """

    def __init__(self, settings: Settings, client: CexClient) -> None:
        self.settings = settings
        self.client = client
        self.quote_engine = QuoteEngine(
            QuoteConfig(spread_bps=settings.spread_bps),
        )
        self.inventory = InventoryManager(
            target_pct=settings.inventory_target_pct,
            max_pct=settings.max_inventory_pct,
        )
        self.symbol = settings.symbol
        self.active_orders: Dict[str, ActiveOrder] = {}

    async def load_inventory_fraction(self, mid: float) -> float:
        bal = await self.client.fetch_balance()
        kas = bal.get(self.settings.base_asset, {}).get("free", 0) * mid
        usdt = bal.get(self.settings.quote_asset, {}).get("free", 0)
        frac = self.inventory.base_fraction(kas, usdt)
        metrics.set_inventory_fraction(self.client.keys.name, self.symbol, frac)
        return frac

    async def step(self) -> None:
        book: OrderBook = await self.client.fetch_order_book(self.symbol)
        mid = book.mid
        if not mid:
            logger.warning("mm_no_mid", symbol=self.symbol)
            return

        metrics.set_mid(self.client.keys.name, self.symbol, mid)

        inv_frac = await self.load_inventory_fraction(mid)
        skew = self.inventory.skew_factor(
            kas_value=inv_frac * (inv_frac + 1e-9), usdt_value=(1 - inv_frac)  # dummy normalisation
        )

        bid, ask = self.quote_engine.compute_quotes(mid, skew_factor=skew) or (None, None)
        if not bid or not ask:
            return

        spread_bps = (ask - bid) / mid * 10_000
        metrics.set_spread(self.client.keys.name, self.symbol, spread_bps)

        # Cancel existing orders and re-quote
        await self.client.cancel_all(self.symbol)

        size_quote = self.settings.order_size
        size_base = size_quote / mid

        buy = await self.client.create_limit_order(self.symbol, "buy", size_base, bid)
        sell = await self.client.create_limit_order(self.symbol, "sell", size_base, ask)

        metrics.inc_order(self.client.keys.name, self.symbol, "buy")
        metrics.inc_order(self.client.keys.name, self.symbol, "sell")

        self.active_orders = {
            "buy": ActiveOrder(id=buy["id"], side="buy", price=bid, amount=size_base),
            "sell": ActiveOrder(id=sell["id"], side="sell", price=ask, amount=size_base),
        }


