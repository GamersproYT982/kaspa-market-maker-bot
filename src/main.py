from __future__ import annotations

import asyncio
import signal

import structlog
from dotenv import load_dotenv

from src.config import get_settings
from src.core import MarketMaker
from src.exchanges import CexClient
from src.logging_config import configure_logging
from src.services import metrics

logger = structlog.get_logger(__name__)


async def run_bot() -> None:
    load_dotenv()
    settings = get_settings()
    configure_logging(settings.log_level)
    metrics.start_metrics(settings.metrics_host, settings.metrics_port)

    client = CexClient(settings.exchange)
    mm = MarketMaker(settings, client)

    stop_event = asyncio.Event()

    def _handle_signal():
        logger.info("shutdown_signal")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            pass

    logger.info("mm_bot_started", symbol=settings.symbol, exchange=settings.exchange.name)

    try:
        while not stop_event.is_set():
            await mm.step()
            await asyncio.sleep(1.0)
    finally:
        await client.close()
        logger.info("mm_bot_stopped")


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()


