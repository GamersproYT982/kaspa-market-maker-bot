from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class QuoteConfig:
    spread_bps: float
    min_spread_bps: float = 3.0
    max_spread_bps: float = 50.0


class QuoteEngine:
    """
    Calculates bid/ask quotes around mid price, with optional skewing.
    """

    def __init__(self, cfg: QuoteConfig) -> None:
        self.cfg = cfg

    def compute_quotes(
        self, mid: float, skew_factor: float = 1.0
    ) -> Optional[Tuple[float, float]]:
        if mid <= 0:
            return None
        spread_bps = min(max(self.cfg.spread_bps * skew_factor, self.cfg.min_spread_bps), self.cfg.max_spread_bps)
        spread = mid * (spread_bps / 10_000)
        bid = mid - spread / 2.0
        ask = mid + spread / 2.0
        return round(bid, 8), round(ask, 8)


