"""
Server state management for the NCAAF MCP Server.
"""

import os
import time
import logging
from typing import Optional
import httpx

from .models import ServerConfig, GraphQLError
from .cache import AdvancedCache
from .async_utils import AsyncResourceManager, RateLimiter
from .graphql import GraphQLClient, generate_cache_key

logger = logging.getLogger(__name__)


class ServerState:
    """Enhanced server state management"""
    
    def __init__(self):
        # Caching
        self.schema_cache = AdvancedCache(max_size=10, default_ttl=3600)  # 1 hour for schema
        self.query_cache = AdvancedCache(max_size=500, default_ttl=300)   # 5 minutes for queries
        
        # State tracking
        self.request_count = 0
        self.startup_time = time.time()
        self.initialized = False
        
        # Configuration and clients
        self.config: Optional[ServerConfig] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.graphql_client: Optional[GraphQLClient] = None
        
        # Resource management
        self.resource_manager = AsyncResourceManager()
        self.rate_limiter = RateLimiter()
    
    def get_cache_key(self, query: str, variables: dict) -> str:
        """Generate cache key for query"""
        return generate_cache_key(query, variables)
    
    def check_rate_limit(self, identifier: str = "default") -> bool:
        """Check if request is within rate limit"""
        return self.rate_limiter.check_rate_limit(identifier)
    
    async def initialize(self):
        """Initialize server configuration and HTTP client"""
        if self.initialized:
            return
            
        try:
            # Get configuration from environment variables
            api_key = os.getenv("CFBD_API_KEY")
            if not api_key:
                raise ValueError("API key not found. Set CFBD_API_KEY environment variable.")
            
            # Get configuration from environment with defaults
            endpoint = os.getenv("CFBD_ENDPOINT", "https://graphql.collegefootballdata.com/v1/graphql")
            timeout = int(os.getenv("QUERY_TIMEOUT", "30"))
            max_retries = int(os.getenv("MAX_RETRIES", "3"))
            cache_ttl = int(os.getenv("CACHE_TTL", "300"))
            rate_limit = int(os.getenv("RATE_LIMIT", "100"))
            
            # Build headers with API key
            headers = {"Authorization": f"Bearer {api_key}"}
            
            # Create server configuration
            server_config_data = {
                "endpoint": endpoint,
                "headers": headers,
                "timeout": timeout,
                "max_retries": max_retries,
                "cache_ttl": cache_ttl,
                "rate_limit": rate_limit
            }
            self.config = ServerConfig(**server_config_data)
            
            # Update rate limiter configuration
            self.rate_limiter = RateLimiter(max_requests=rate_limit)
            
            # Initialize HTTP client
            self.http_client = await self.resource_manager.create_client(self.config.timeout)
            
            # Initialize GraphQL client
            self.graphql_client = GraphQLClient(
                http_client=self.http_client,
                endpoint=self.config.endpoint,
                headers=self.config.headers,
                max_retries=self.config.max_retries
            )
            
            self.initialized = True
            logger.info(f"Server initialized with endpoint: {self.config.endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.resource_manager.cleanup()
            self.query_cache.clear()
            self.schema_cache.clear()
            self.http_client = None
            self.graphql_client = None
            self.initialized = False
            logger.info("Server cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise
    
    def get_stats(self) -> dict:
        """Get comprehensive server statistics"""
        uptime = time.time() - self.startup_time
        query_cache_stats = self.query_cache.stats()
        schema_cache_stats = self.schema_cache.stats()
        rate_limit_stats = self.rate_limiter.stats()
        
        return {
            "server": {
                "uptime_seconds": round(uptime, 2),
                "request_count": self.request_count,
                "initialized": self.initialized,
                "startup_time": self.startup_time
            },
            "cache": {
                "query_cache": query_cache_stats,
                "schema_cache": schema_cache_stats
            },
            "config": {
                "endpoint": self.config.endpoint if self.config else None,
                "timeout": self.config.timeout if self.config else None,
                "max_retries": self.config.max_retries if self.config else None,
                "rate_limit": self.config.rate_limit if self.config else None,
            },
            "rate_limiting": rate_limit_stats
        }
    
    def get_masked_config(self) -> dict:
        """Get configuration with sensitive data masked"""
        if not self.config:
            return {"error": "Server not configured"}
        
        config_dict = self.config.model_dump()
        # Mask sensitive information
        if "headers" in config_dict and "Authorization" in config_dict["headers"]:
            config_dict["headers"]["Authorization"] = "Bearer ***masked***"
        
        return config_dict