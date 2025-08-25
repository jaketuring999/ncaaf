"""
FastMCP server instance that can be imported by tools without circular imports.
"""

from fastmcp import FastMCP

# Create the FastMCP server instance
mcp = FastMCP("College Football GraphQL Server")