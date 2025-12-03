from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable, TypeVar

T = TypeVar("T")


async def gather_limited(*coroutines: Awaitable[T], limit: int = 10) -> list[T]:
    semaphore = asyncio.Semaphore(limit)

    async def _run(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(_run(c) for c in coroutines))


@asynccontextmanager
async def cancellation_scope() -> AsyncIterator[asyncio.TaskGroup]:
    # Python 3.11 TaskGroup helper for structured concurrency
    tg = asyncio.TaskGroup()
    async with tg:
        yield tg


