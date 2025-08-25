"""
Betting-related MCP tools for college football data.
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

# GraphQL query for betting lines data
GET_BETTING_LINES_QUERY = """
query GetBettingLines($season: smallint, $week: smallint, $teamId: Int, $limit: Int) {
    game(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
            lines: {}
        }
        orderBy: { startDate: DESC }
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

@mcp.tool() 
async def GetBettingLines(
    season: Optional[Union[str, int]] = None,
    week: Optional[Union[str, int]] = None,
    team_id: Optional[Union[str, int]] = None,
    limit: Optional[Union[str, int]] = 50,
    ctx: Context = None
) -> str:
    """
    Get betting lines for games.
    
    Args:
        season: Season year (e.g., 2024 or "2024")
        week: Week number (can be string or int)
        team_id: Team ID (can be string or int)
        limit: Maximum number of games to return (default: 50, can be string or int)
    
    Returns:
        JSON string with betting lines data
    """
    # Convert string inputs to integers
    season_int = safe_int_conversion(season, 'season') if season is not None else None
    week_int = safe_int_conversion(week, 'week') if week is not None else None
    team_id_int = safe_int_conversion(team_id, 'team_id') if team_id is not None else None
    limit_int = safe_int_conversion(limit, 'limit') if limit is not None else 50
    
    variables = build_query_variables(season=season_int, week=week_int, teamId=team_id_int, limit=limit_int)
    return await execute_graphql(GET_BETTING_LINES_QUERY, variables, ctx)