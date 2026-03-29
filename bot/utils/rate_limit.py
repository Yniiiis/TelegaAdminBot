"""
Персонифицированные лимиты запросов в памяти процесса.
Для нескольких инстансов бота нужен Redis и т.п.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict


class UserRateLimiter:
    """Скользящее окно для общих событий и отдельный cooldown по действиям."""

    def __init__(
        self,
        *,
        window_sec: float,
        max_events: int,
    ) -> None:
        self._window_sec = window_sec
        self._max_events = max_events
        self._general: dict[int, list[float]] = defaultdict(list)
        self._cooldowns: dict[tuple[int, str], float] = {}
        self._lock = asyncio.Lock()

    def _prune(self, stamps: list[float], now: float) -> list[float]:
        cutoff = now - self._window_sec
        return [t for t in stamps if t >= cutoff]

    async def allow_general(self, user_id: int) -> bool:
        """True, если пользователь не превысил общий лимит событий за окно."""
        async with self._lock:
            now = time.monotonic()
            lst = self._prune(self._general[user_id], now)
            if len(lst) >= self._max_events:
                return False
            lst.append(now)
            self._general[user_id] = lst
            return True

    async def cooldown_remaining(self, user_id: int, action: str, min_interval_sec: float) -> float:
        """
        Возвращает 0, если действие разрешено; иначе секунды до конца cooldown.
        При разрешении обновляет время последнего вызова.
        """
        async with self._lock:
            now = time.monotonic()
            key = (user_id, action)
            last = self._cooldowns.get(key, 0.0)
            elapsed = now - last
            if elapsed < min_interval_sec:
                return min_interval_sec - elapsed
            self._cooldowns[key] = now
            return 0.0
