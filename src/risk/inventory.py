from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InventoryState:
    base_free: float
    quote_free: float

    @property
    def total_value_quote(self) -> float:
        return self.base_free + self.quote_free


class InventoryManager:
    """
    Tracks KAS/USDT inventory and decides whether to skew quotes.
    """

    def __init__(self, target_pct: float, max_pct: float) -> None:
        self.target_pct = target_pct
        self.max_pct = max_pct

    def base_fraction(self, kas_value: float, usdt_value: float) -> float:
        total = kas_value + usdt_value
        if total <= 0:
            return 0.0
        return kas_value / total

    def skew_factor(self, kas_value: float, usdt_value: float) -> float:
        """
        Returns a factor in [0.5, 1.5] to bias buy/sell size depending on inventory.
        >1 => prefer selling KAS, <1 => prefer buying KAS.
        """
        frac = self.base_fraction(kas_value, usdt_value)
        if frac > self.max_pct:
            return 1.5
        if frac > self.target_pct:
            return 1.2
        if frac < self.target_pct * 0.5:
            return 0.6
        if frac < self.target_pct:
            return 0.8
        return 1.0


