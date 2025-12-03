from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field, validator


class ExchangeKeys(BaseSettings):
    name: str
    api_key: str
    secret_key: str
    password: Optional[str] = None  # some exchanges (e.g. KuCoin) call this passphrase
    testnet: bool = False


class Settings(BaseSettings):
    environment: str = Field("development")
    symbol: str = Field("KAS/USDT", description="Market making symbol")
    base_asset: str = "KAS"
    quote_asset: str = "USDT"

    spread_bps: float = Field(8.0, description="Target spread in basis points around mid")
    order_size: float = Field(200.0, description="Base order size in quote currency")
    inventory_target_pct: float = Field(
        0.5, description="Target fraction of portfolio in base (KAS)"
    )
    max_inventory_pct: float = Field(
        0.8, description="Hard cap on inventory fraction in base (KAS)"
    )

    exchange: ExchangeKeys

    ws_url: str | None = Field(
        default=None,
        description="Optional override for exchange websocket URL; otherwise use ccxt defaults",
    )

    metrics_host: str = "0.0.0.0"
    metrics_port: int = 9301
    log_level: str = "INFO"

    @validator("exchange", pre=True)
    def _ensure_exchange(cls, v):
        if isinstance(v, str):
            import json

            return ExchangeKeys(**json.loads(v))
        if isinstance(v, dict):
            return ExchangeKeys(**v)
        return v

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


@lru_cache
def get_settings() -> Settings:
    return Settings()


