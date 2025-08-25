"""
Advanced caching implementation with TTL and LRU eviction for the NCAAF GraphQL MCP Server.
"""

import time
from typing import Dict, Any, Optional


class AdvancedCache:
    """Enhanced caching with TTL and size limits"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.access_times = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get an item from cache if it hasn't expired"""
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.default_ttl:
                self.access_times[key] = time.time()
                self.hits += 1
                return self.cache[key]
            else:
                self.invalidate(key)
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set an item in cache with optional custom TTL"""
        # Use custom TTL if provided, otherwise use default
        effective_ttl = ttl if ttl is not None else self.default_ttl
        
        # Implement LRU eviction if cache is full
        if len(self.cache) >= self.max_size:
            # Find least recently used item
            if self.access_times:
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            else:
                oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            self.invalidate(oldest_key)
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.access_times[key] = time.time()
    
    def invalidate(self, key: str):
        """Remove a specific key from cache"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        self.access_times.pop(key, None)
    
    def clear(self):
        """Clear all cached items and reset stats"""
        self.cache.clear()
        self.timestamps.clear()
        self.access_times.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "total_requests": total_requests
        }
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)