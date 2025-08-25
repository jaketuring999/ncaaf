"""
Rankings-related MCP tools for college football data.
"""

from typing import Optional
from fastmcp import Context

# Import from server module at package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.mcp_server import mcp
from src.graphql_executor import execute_graphql, build_query_variables

# Placeholder - will implement later
GET_RANKINGS_QUERY = """
query GetRankings($season: smallint, $week: smallint) {
    rankings(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
        }
        orderBy: { rank: ASC }
    ) {
        season
        seasonType
        week
        poll
        rank
        school
        firstPlaceVotes
        points
    }
}
"""

@mcp.tool()
async def GetRankings(
    season: Optional[int] = None,
    week: Optional[int] = None,
    ctx: Context = None
) -> str:
    """Get college football rankings for a specific season and week."""
    variables = build_query_variables(season=season, week=week)
    return await execute_graphql(GET_RANKINGS_QUERY, variables, ctx)