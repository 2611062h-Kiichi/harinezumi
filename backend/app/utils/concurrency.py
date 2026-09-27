"""Runs independent pipeline steps at the same time.

If a step fails, steps that are only waiting on the network (paid API calls)
are cancelled to stop spending on a request that will fail anyway. Steps
running in a worker thread cannot be interrupted and may still be reading an
uploaded file, so they are always waited for: once `wait()` returns or
raises, the caller can safely delete the upload's temp directory (on Windows
an open file would block that).
"""

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


class Stage:
    def __init__(self) -> None:
        # (task, cancellable) in the order the steps were started.
        self._steps: list[tuple[asyncio.Task, bool]] = []

    def call(self, coro: Coroutine[Any, Any, T], *, cancellable: bool = True) -> "asyncio.Task[T]":
        """Starts a coroutine now. Pass cancellable=False if it runs thread work
        on files (e.g. via asyncio.to_thread) that must finish before cleanup."""
        task = asyncio.ensure_future(coro)
        self._steps.append((task, cancellable))
        return task

    def in_thread(self, fn: Callable[..., T], *args: Any) -> "asyncio.Task[T]":
        """Starts blocking work (file parsing, video decoding) in a worker thread now."""
        return self.call(asyncio.to_thread(fn, *args), cancellable=False)

    async def wait(self) -> None:
        """Returns once every step has finished. If any step fails, raises the
        first failure (in start order) without waiting for slow network steps."""
        tasks = [task for task, _ in self._steps]
        if not tasks:
            return
        try:
            # asyncio.wait (unlike gather) never cancels the tasks itself, even if
            # this request is cancelled, so thread steps are not cut loose.
            await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        except asyncio.CancelledError:
            await self._abort()
            raise
        for task in tasks:
            if task.done() and not task.cancelled() and task.exception() is not None:
                await self._abort()
                raise task.exception()

    async def _abort(self) -> None:
        for task, cancellable in self._steps:
            if cancellable:
                task.cancel()
        # Let cancelled network steps unwind and thread steps run to completion.
        await asyncio.gather(*(task for task, _ in self._steps), return_exceptions=True)
