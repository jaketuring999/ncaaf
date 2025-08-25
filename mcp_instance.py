"""
Shared MCP instance for all tools.
"""
from fastmcp import FastMCP

# Single global MCP instance  
mcp = FastMCP("NCAA Football GraphQL Server")