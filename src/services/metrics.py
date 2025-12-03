from __future__ import annotations

from prometheus_client import Gauge, Counter, start_http_server

mid_price_gauge = Gauge("kas_mid_price", "Mid price for KAS market", ["symbol", "exchange"])
spread_gauge = Gauge("kas_quote_spread_bps", "Current quoting spread in bps", ["symbol", "exchange"])
inventory_frac_gauge = Gauge(
    "kas_inventory_fraction", "Fraction of portfolio in KAS", ["symbol", "exchange"]
)
order_counter = Counter(
    "kas_mm_orders_total", "Total MM orders sent", ["symbol", "exchange", "side"]
)


def start_metrics(host: str, port: int) -> None:
    start_http_server(port, addr=host)


def set_mid(exchange: str, symbol: str, mid: float) -> None:
    mid_price_gauge.labels(symbol=symbol, exchange=exchange).set(mid)


def set_spread(exchange: str, symbol: str, bps: float) -> None:
    spread_gauge.labels(symbol=symbol, exchange=exchange).set(bps)


def set_inventory_fraction(exchange: str, symbol: str, frac: float) -> None:
    inventory_frac_gauge.labels(symbol=symbol, exchange=exchange).set(frac)


def inc_order(exchange: str, symbol: str, side: str) -> None:
    order_counter.labels(symbol=symbol, exchange=exchange, side=side).inc()


