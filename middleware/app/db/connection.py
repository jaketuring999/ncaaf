"""
PostgreSQL connection pool management for usage logging.

Provides non-blocking database connections with aggressive timeouts
to ensure logging never interferes with response times.
"""

import os
import logging
from typing import Optional, Any, Dict, cast
from contextlib import asynccontextmanager
import asyncio

import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[AsyncConnectionPool] = None


def get_connection_string() -> Optional[str]:
    """
    Get the database connection string from environment variables.
    
    Returns None if not configured, allowing the system to run without logging.
    """
    postgres_url = os.getenv("POSTGRES_URL_USAGE")
    if not postgres_url:
        logger.debug("POSTGRES_URL not set - usage logging will be disabled")
        return None
    return postgres_url


async def create_pool() -> Optional[AsyncConnectionPool]:
    """
    Create and return a PostgreSQL connection pool.
    
    Returns None if database is not configured, allowing graceful degradation.
    """
    global _pool
    
    if _pool is not None:
        return _pool
    
    # Get connection string
    postgres_url = get_connection_string()
    if not postgres_url:
        return None
    
    try:
        # Create the pool with aggressive timeouts for non-blocking behavior
        _pool = AsyncConnectionPool(
            postgres_url,
            min_size=1,  # Keep minimal connections
            max_size=5,  # Limit connection overhead
            timeout=1.0,  # 1 second max wait for connection
            kwargs={
                "row_factory": dict_row,
                "autocommit": True,
                "connect_timeout": 1,  # 1 second connection timeout
                "options": "-c statement_timeout=1000"  # 1 second statement timeout
            }
        )
        logger.info("Database connection pool created successfully")
        return _pool
    except Exception as e:
        logger.warning(f"Failed to create database pool: {e}")
        return None


async def close_pool() -> None:
    """Close the connection pool if it exists."""
    global _pool
    
    if _pool is not None:
        try:
            await _pool.close()
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.warning(f"Error closing database pool: {e}")
        finally:
            _pool = None


@asynccontextmanager
async def get_connection(timeout: float = 1.0):
    """
    Get a connection from the pool as a context manager.
    
    Args:
        timeout: Maximum time to wait for a connection in seconds
        
    Yields:
        Connection object or None if unavailable
    """
    pool = await create_pool()
    if not pool:
        yield None
        return
    
    conn = None
    try:
        # Try to get a connection with timeout
        conn = await asyncio.wait_for(
            pool.getconn(),
            timeout=timeout
        )
        yield conn
    except asyncio.TimeoutError:
        logger.debug("Timeout getting database connection")
        yield None
    except Exception as e:
        logger.debug(f"Error getting database connection: {e}")
        yield None
    finally:
        if conn and pool:
            try:
                await pool.putconn(conn)
            except Exception:
                pass  # Silently ignore putconn errors


async def execute_insert_with_timeout(
    query: str,
    params: Dict[str, Any],
    timeout: float = 1.0
) -> bool:
    """
    Execute an INSERT query with timeout protection.
    
    Args:
        query: SQL query to execute
        params: Query parameters as a dictionary
        timeout: Maximum execution time in seconds
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        async with get_connection(timeout=timeout) as conn:
            if not conn:
                return False
            
            async with conn.cursor() as cur:
                # Execute with timeout
                await asyncio.wait_for(
                    cur.execute(cast(Any, query), params),
                    timeout=timeout
                )
                return True
    except asyncio.TimeoutError:
        logger.debug("Query execution timed out")
        return False
    except Exception as e:
        logger.debug(f"Error executing query: {e}")
        return False


async def test_connection() -> bool:
    """
    Test if the database connection is working.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        async with get_connection(timeout=1.0) as conn:
            if not conn:
                return False
            
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                result = await cur.fetchone()
                return result is not None
    except Exception:
        return False