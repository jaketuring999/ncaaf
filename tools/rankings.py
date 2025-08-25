"""
Rankings-related MCP tools for college football data.
"""

from typing import Optional, Union
from fastmcp import Context

# Import from server module at package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.mcp_server import mcp
from src.graphql_executor import execute_graphql, build_query_variables
from src.param_processor import safe_int_conversion

# GraphQL query for rankings data
GET_RANKINGS_QUERY = """
query GetRankings($season: Int, $week: smallint) {
    poll(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
        }
        orderBy: { week: ASC }
    ) {
        season
        seasonType
        week
        pollType {
            name
            abbreviation
        }
        rankings(
            orderBy: { rank: ASC }
        ) {
            rank
            firstPlaceVotes
            points
            team {
                teamId
                school
                conference
                abbreviation
            }
        }
    }
}
"""

@mcp.tool()
async def GetRankings(
    season: Optional[Union[str, int]] = None,
    week: Optional[Union[str, int]] = None,
    ctx: Context = None
) -> str:
    """
    Get college football rankings for a specific season and week.
    
    Args:
        season: Season year (e.g., 2024 or "2024")
        week: Week number (can be string or int)
    
    Returns:
        JSON string with rankings data
    """
    # Convert string inputs to integers
    season_int = safe_int_conversion(season, 'season') if season is not None else None
    week_int = safe_int_conversion(week, 'week') if week is not None else None
    
    variables = build_query_variables(season=season_int, week=week_int)
    return await execute_graphql(GET_RANKINGS_QUERY, variables, ctx)