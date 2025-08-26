"""
NCAAF Agent Service - Manages MCP server connection and agent initialization
"""

import asyncio
import logging
from typing import Optional
from agents import Agent
from agents.mcp import MCPServerStreamableHttp

from ..config import settings, SystemPromptLoader


logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing NCAAF MCP agent and server connection"""
    
    def __init__(self):
        self._mcp_server: Optional[MCPServerStreamableHttp] = None
        self._agent: Optional[Agent] = None
        self._system_prompt: str = ""
        self._connection_lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize MCP server connection and agent"""
        async with self._connection_lock:
            if self._agent is not None:
                return
                
            try:
                # Load system prompt
                self._system_prompt = SystemPromptLoader.load_prompt()
                logger.info("Loaded system prompt")
                
                # Initialize MCP server connection
                mcp_params = {
                    "url": settings.mcp_server_url,
                    "headers": {},
                    "timeout": 60.0,
                    "sse_read_timeout": 300.0,
                    "terminate_on_close": True
                }
                
                self._mcp_server = MCPServerStreamableHttp(
                    params=mcp_params,
                    cache_tools_list=True,
                    client_session_timeout_seconds=settings.mcp_server_timeout
                )
                
                # Initialize OpenAI Agent
                self._agent = Agent(
                    name="NCAAF-Analytics-Agent",
                    instructions=self._system_prompt,
                    model=settings.openai_model,
                    mcp_servers=[self._mcp_server]
                )
                
                logger.info(f"NCAAF Agent initialized successfully with MCP server at {settings.mcp_server_url}")
                
            except Exception as e:
                logger.error(f"Failed to initialize NCAAF agent: {e}")
                raise
    
    @property
    def agent(self) -> Agent:
        """Get the initialized agent"""
        if self._agent is None:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        return self._agent
    
    @property
    def mcp_server(self) -> MCPServerStreamableHttp:
        """Get the MCP server instance"""
        if self._mcp_server is None:
            raise RuntimeError("MCP server not initialized. Call initialize() first.")
        return self._mcp_server
    
    async def connect(self) -> None:
        """Connect to the MCP server"""
        if self._mcp_server is None:
            await self.initialize()
        
        try:
            logger.info("Connecting to MCP server...")
            await self._mcp_server.connect()
            logger.info("MCP server connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise

    async def health_check(self) -> dict:
        """Check health of MCP server connection"""
        try:
            if self._mcp_server is None:
                await self.initialize()
                
            # Connect if not already connected
            await self.connect()
            
            # Try to get tools list to verify connection
            tools = await self._mcp_server.list_tools()
            
            return {
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            if self._mcp_server:
                # Close MCP server connection if it has a close method
                if hasattr(self._mcp_server, 'close'):
                    await self._mcp_server.close()
                self._mcp_server = None
            
            self._agent = None
            logger.info("Agent service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global agent service instance
agent_service = AgentService()