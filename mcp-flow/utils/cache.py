from typing import Any, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import json
from functools import wraps


class Cache:
    def __init__(self, ttl: int = 300, max_size: int = 1000):
        self.ttl = ttl
        self.max_size = max_size
        self.cache = {}
        self.timestamps = {}
        self.locks = {}
        self._cleanup_task = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            if datetime.now() - self.timestamps[key] < timedelta(seconds=self.ttl):
                return self.cache[key]
            else:
                await self._remove(key)
        return None

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache with TTL"""
        async with self._get_lock(key):
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = min(
                    self.timestamps.keys(), key=lambda k: self.timestamps[k]
                )
                await self._remove(oldest_key)

            self.cache[key] = value
            self.timestamps[key] = datetime.now()

    async def _remove(self, key: str) -> None:
        """Remove key from cache"""
        async with self._get_lock(key):
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create lock for key"""
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        return self.locks[key]

    async def clear(self) -> None:
        """Clear all cached values"""
        self.cache.clear()
        self.timestamps.clear()

    async def start_cleanup(self) -> None:
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self) -> None:
        """Stop background cleanup task"""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """Periodically remove expired entries"""
        while True:
            now = datetime.now()
            expired_keys = [
                key
                for key, timestamp in self.timestamps.items()
                if now - timestamp > timedelta(seconds=self.ttl)
            ]
            for key in expired_keys:
                await self._remove(key)
            await asyncio.sleep(self.ttl)


def cache_decorator(cache: Cache, key_generator: Callable = None):
    """Decorator to cache function results"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result)
            return result

        return wrapper

    return decorator


class JSONCache(Cache):
    """Cache implementation with JSON serialization"""

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache with JSON serialization"""
        serialized = json.dumps(value)
        await super().set(key, serialized)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with JSON deserialization"""
        serialized = await super().get(key)
        if serialized is not None:
            return json.loads(serialized)
        return None


def json_cache_decorator(cache: JSONCache, key_generator: Callable = None):
    """Decorator to cache function results with JSON serialization"""
    return cache_decorator(cache, key_generator)
