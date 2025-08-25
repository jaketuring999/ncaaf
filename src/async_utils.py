"""
Async utilities and resource management for the NCAAF MCP Server.
"""

import asyncio
import time
import logging
from typing import Set, List, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class AsyncResourceManager:
    """Manage async resources properly"""
    
    def __init__(self):
        self._clients: List[httpx.AsyncClient] = []
        self._tasks: Set[asyncio.Task] = set()
    
    async def create_client(self, timeout: int = 30) -> httpx.AsyncClient:
        """
        Create and track an HTTP client with proper configuration.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            Configured HTTP client
        """
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0),
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10
            ),
            transport=httpx.AsyncHTTPTransport(retries=3)
        )
        self._clients.append(client)
        return client
    
    def create_task(self, coro):
        """Create and track async tasks"""
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task
    
    async def cleanup(self):
        """Cleanup all managed resources"""
        # Cancel pending tasks
        for task in self._tasks.copy():
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Close all clients
        for client in self._clients:
            await client.aclose()
        
        self._clients.clear()
        self._tasks.clear()


class RateLimiter:
    """Simple rate limiting implementation"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times: Dict[str, List[float]] = {}
    
    def check_rate_limit(self, identifier: str = "default") -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier for the client/user
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        if identifier not in self.request_times:
            self.request_times[identifier] = []
        
        # Remove old entries outside the window
        self.request_times[identifier] = [
            req_time for req_time in self.request_times[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.request_times[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.request_times[identifier].append(now)
        return True
    
    def get_remaining_requests(self, identifier: str = "default") -> int:
        """Get number of remaining requests for identifier"""
        current_requests = len(self.request_times.get(identifier, []))
        return max(0, self.max_requests - current_requests)
    
    def get_reset_time(self, identifier: str = "default") -> float:
        """Get when the rate limit resets for identifier"""
        if identifier not in self.request_times or not self.request_times[identifier]:
            return time.time()
        
        oldest_request = min(self.request_times[identifier])
        return oldest_request + self.window_seconds
    
    def stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        active_windows = len([times for times in self.request_times.values() if times])
        total_tracked = sum(len(times) for times in self.request_times.values())
        
        return {
            "max_requests_per_window": self.max_requests,
            "window_seconds": self.window_seconds,
            "active_windows": active_windows,
            "total_tracked_requests": total_tracked
        }


async def run_with_timeout(coro, timeout_seconds: float):
    """
    Run a coroutine with a timeout.
    
    Args:
        coro: Coroutine to run
        timeout_seconds: Timeout in seconds
        
    Returns:
        Result of coroutine
        
    Raises:
        asyncio.TimeoutError: If coroutine times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"Operation timed out after {timeout_seconds} seconds")
        raise


def generate_request_id() -> str:
    """Generate a unique request ID for logging correlation"""
    timestamp = int(time.time() * 1000)
    return f"req_{timestamp}_{id(object())}"