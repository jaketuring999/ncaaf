"""
Non-blocking logging service for tracking API usage.

This service provides fire-and-forget logging that never blocks or
interferes with response times. All operations fail silently to ensure
the main API functionality is never affected.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

from ..db.connection import execute_insert_with_timeout, test_connection

logger = logging.getLogger(__name__)


class LoggingService:
    """
    Service for logging API usage metrics without blocking responses.
    
    All methods are designed to fail silently and never raise exceptions
    to the caller, ensuring logging issues never affect API responses.
    """
    
    def __init__(self, enabled: bool = True, timeout_ms: int = 1000, service_prefix: str = "ncaaf"):
        """
        Initialize the logging service.
        
        Args:
            enabled: Whether logging is enabled
            timeout_ms: Maximum time for any logging operation in milliseconds
            service_prefix: Prefix to add to usernames to identify service
        """
        self.enabled = enabled
        self.timeout_seconds = timeout_ms / 1000.0
        self.service_prefix = service_prefix
        self._healthy = True
        self._consecutive_failures = 0
        self._max_failures_before_circuit_break = 5
    
    def _format_username(self, username: str) -> str:
        """Add service prefix to username if not already present"""
        if username.startswith(f"{self.service_prefix}_"):
            return username
        return f"{self.service_prefix}_{username}"
    
    async def initialize(self) -> bool:
        """
        Test the database connection on startup.
        
        Returns:
            bool: True if database is available, False otherwise
        """
        if not self.enabled:
            logger.info("Usage logging is disabled")
            return False
        
        try:
            connected = await test_connection()
            if connected:
                logger.info("Usage logging database connection successful")
                self._healthy = True
                return True
            else:
                logger.warning("Usage logging database not available - logging will be disabled")
                self._healthy = False
                return False
        except Exception as e:
            logger.warning(f"Error testing database connection: {e}")
            self._healthy = False
            return False
    
    async def log_usage_async(
        self,
        username: str,
        query: str,
        query_timestamp: datetime,
        response_text: Optional[str] = None,
        processing_time_ms: int = 0,
        tool_calls_count: int = 0,
        tool_data: Optional[List[Dict[str, Any]]] = None,
        stream_events_count: int = 0,
        success: bool = True,
        error_message: Optional[str] = None,
        client_ip: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        requests_count: int = 0,
        cached_tokens: int = 0,
        reasoning_tokens: int = 0
    ) -> None:
        """
        Log usage data in a fire-and-forget manner.
        
        This method creates a background task to insert the log entry
        and returns immediately without waiting for completion.
        
        All parameters match the usage_logs table schema.
        """
        if not self.enabled or not self._healthy:
            return
        
        # Check circuit breaker
        if self._consecutive_failures >= self._max_failures_before_circuit_break:
            # Try to recover every 10th attempt
            if self._consecutive_failures % 10 != 0:
                return
        
        # Create log data
        log_data = {
            "id": str(uuid.uuid4()),
            "username": self._format_username(username),
            "query": query,
            "query_timestamp": query_timestamp,
            "response_text": response_text,
            "processing_time_ms": processing_time_ms,
            "tool_calls_count": tool_calls_count,
            "tool_data": json.dumps(tool_data or []),
            "stream_events_count": stream_events_count,
            "success": success,
            "error_message": error_message,
            "client_ip": client_ip,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "requests_count": requests_count,
            "cached_tokens": cached_tokens,
            "reasoning_tokens": reasoning_tokens
        }
        
        # Fire and forget - create task without awaiting
        try:
            asyncio.create_task(self._insert_log_with_timeout(log_data))
        except Exception:
            # Even task creation can fail in extreme cases
            pass
    
    async def _insert_log_with_timeout(self, log_data: Dict[str, Any]) -> None:
        """
        Insert a log entry with timeout protection.
        
        This method handles all errors internally and updates health status.
        """
        query = """
            INSERT INTO sim.usage_logs (
                id, username, query, query_timestamp, response_text,
                processing_time_ms, tool_calls_count, tool_data,
                stream_events_count, success, error_message, client_ip,
                input_tokens, output_tokens, total_tokens, requests_count,
                cached_tokens, reasoning_tokens
            ) VALUES (
                %(id)s, %(username)s, %(query)s, %(query_timestamp)s, %(response_text)s,
                %(processing_time_ms)s, %(tool_calls_count)s, %(tool_data)s::jsonb,
                %(stream_events_count)s, %(success)s, %(error_message)s, %(client_ip)s::inet,
                %(input_tokens)s, %(output_tokens)s, %(total_tokens)s, %(requests_count)s,
                %(cached_tokens)s, %(reasoning_tokens)s
            )
        """
        
        try:
            success = await execute_insert_with_timeout(
                query, 
                log_data,
                timeout=self.timeout_seconds
            )
            
            if success:
                self._consecutive_failures = 0
                self._healthy = True
                logger.debug("Usage log inserted successfully")
            else:
                self._consecutive_failures += 1
                logger.debug(f"Failed to insert usage log (attempt {self._consecutive_failures})")
                
        except Exception as e:
            self._consecutive_failures += 1
            logger.debug(f"Error in usage logging: {e}")
    
    def collect_streaming_metrics(
        self,
        query_start_time: float,
        tool_calls: Dict[Any, Dict[str, Any]],
        tool_data: List[Dict[str, Any]],
        response_text: str,
        stream_events_count: int = 0
    ) -> Dict[str, Any]:
        """
        Helper method to collect metrics from streaming data.
        
        Args:
            query_start_time: Timestamp when query started
            tool_calls: Dictionary of tool calls from streaming
            tool_data: List of tool responses
            response_text: Final response text
            stream_events_count: Number of stream events
            
        Returns:
            Dict containing formatted metrics for logging
        """
        processing_time_ms = int((asyncio.get_event_loop().time() - query_start_time) * 1000)
        
        return {
            "processing_time_ms": processing_time_ms,
            "tool_calls_count": len(tool_data),
            "tool_data": tool_data,
            "response_text": response_text,
            "stream_events_count": stream_events_count
        }
    
    @staticmethod
    def extract_token_usage(usage_data) -> Dict[str, int]:
        """
        Extract token usage metrics from agents SDK Usage object.
        
        Args:
            usage_data: Usage object from RunContextWrapper.usage
            
        Returns:
            Dict containing token usage metrics
        """
        if not usage_data:
            return {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "requests_count": 0,
                "cached_tokens": 0,
                "reasoning_tokens": 0
            }
        
        # Extract cached tokens from input_tokens_details
        cached_tokens = 0
        if hasattr(usage_data, 'input_tokens_details') and usage_data.input_tokens_details:
            cached_tokens = getattr(usage_data.input_tokens_details, 'cached_tokens', 0)
        
        # Extract reasoning tokens from output_tokens_details
        reasoning_tokens = 0
        if hasattr(usage_data, 'output_tokens_details') and usage_data.output_tokens_details:
            reasoning_tokens = getattr(usage_data.output_tokens_details, 'reasoning_tokens', 0)
        
        return {
            "input_tokens": getattr(usage_data, 'input_tokens', 0),
            "output_tokens": getattr(usage_data, 'output_tokens', 0),
            "total_tokens": getattr(usage_data, 'total_tokens', 0),
            "requests_count": getattr(usage_data, 'requests', 0),
            "cached_tokens": cached_tokens,
            "reasoning_tokens": reasoning_tokens
        }


# Global instance for easy access
_logging_service: Optional[LoggingService] = None


def get_logging_service() -> Optional[LoggingService]:
    """Get the global logging service instance."""
    return _logging_service


async def initialize_logging_service(enabled: bool = True, timeout_ms: int = 1000, service_prefix: str = "ncaaf") -> LoggingService:
    """
    Initialize the global logging service.
    
    Args:
        enabled: Whether logging is enabled
        timeout_ms: Timeout for logging operations
        service_prefix: Prefix to add to usernames to identify service
        
    Returns:
        LoggingService instance
    """
    global _logging_service
    
    _logging_service = LoggingService(enabled=enabled, timeout_ms=timeout_ms, service_prefix=service_prefix)
    await _logging_service.initialize()
    
    return _logging_service