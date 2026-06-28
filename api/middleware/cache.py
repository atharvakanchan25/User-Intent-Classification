"""
In-memory cache (LRU) + request metrics tracker.
Production: swap cache backend to Redis via CACHE_BACKEND=redis env var.
"""
from __future__ import annotations
import time
import os
from collections import OrderedDict, defaultdict
from typing import Any, Optional, Dict


class LRUCache:
    def __init__(self, maxsize: int = 1000):
        self._cache: OrderedDict = OrderedDict()
        self.maxsize = maxsize
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            self._cache.move_to_end(key)
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

    @property
    def size(self) -> int:
        return len(self._cache)

    def clear(self):
        self._cache.clear()


class RequestMetrics:
    def __init__(self):
        self.total_requests: int = 0
        self.total_latency_ms: float = 0.0
        self.intent_distribution: Dict[str, int] = defaultdict(int)
        self._start_time: float = time.time()

    def record(self, intent_id: str, latency_ms: float):
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        self.intent_distribution[intent_id] += 1

    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return round(self.total_latency_ms / self.total_requests, 2)

    @property
    def uptime_seconds(self) -> float:
        return round(time.time() - self._start_time, 2)


# Module-level singletons
cache = LRUCache(maxsize=int(os.getenv("CACHE_MAXSIZE", "1000")))
metrics = RequestMetrics()
