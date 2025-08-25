"""
Betting-related MCP tools for college football data.
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
GET_BETTING_LINES_QUERY = """
query GetBettingLines($season: smallint, $week: smallint, $teamId: Int) {
    bettingLines(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
        }
    ) {
        gameId
        season
        week
        spread
        overUnder
        moneylineHome
        moneylineAway
    }
}
"""

@mcp.tool() 
async def GetBettingLines(
    season: Optional[int] = None,
    week: Optional[int] = None,
    team_id: Optional[int] = None,
    ctx: Context = None
) -> str:
    """Get betting lines for games."""
    variables = build_query_variables(season=season, week=week, teamId=team_id)
    return await execute_graphql(GET_BETTING_LINES_QUERY, variables, ctx)