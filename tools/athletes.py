"""
Athlete/Player-related MCP tools for college football data.
"""

from typing import Optional, Union, Annotated
from fastmcp import Context

# Import from server module at package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from src.graphql_executor import execute_graphql, build_query_variables
from src.param_processor import safe_int_conversion

# GraphQL query for athlete data
GET_ATHLETES_QUERY = """
query GetAthletes($teamId: Int, $season: smallint) {
    athlete(
        where: {
            athleteTeams: {
                teamId: { _eq: $teamId }
                startYear: { _lte: $season }
                endYear: { _gte: $season }
            }
        }
        limit: 100
    ) {
        id
        name
        firstName
        lastName
        weight
        height
        jersey
        positionId
        teamId
        
        athleteTeams {
            teamId
            startYear
            endYear
            team {
                school
                abbreviation
                conference
            }
        }
    }
}
"""

GET_ATHLETES_QUERY_NO_SEASON = """
query GetAthletes($teamId: Int) {
    athlete(
        where: {
            athleteTeams: {
                teamId: { _eq: $teamId }
            }
        }
        limit: 100
    ) {
        id
        name
        firstName
        lastName
        weight
        height
        jersey
        positionId
        teamId
        
        athleteTeams {
            teamId
            startYear
            endYear
            team {
                school
                abbreviation
                conference
            }
        }
    }
}
"""

@mcp.tool()
async def GetAthletes(
    team_id: Annotated[Optional[Union[str, int]], "Team ID (can be string or int)"] = None,
    season: Annotated[Optional[Union[str, int]], "Season year (e.g., 2024 or '2024')"] = None,
    ctx: Context = None
) -> str:
    """
    Get athlete information for a team.
    
    Args:
        team_id: Team ID (can be string or int)
        season: Season year (e.g., 2024 or "2024")
    
    Returns:
        JSON string with athlete data
    """
    # Convert string inputs to integers
    team_id_int = safe_int_conversion(team_id, 'team_id') if team_id is not None else None
    season_int = safe_int_conversion(season, 'season') if season is not None else None
    
    # Use different query based on whether season filtering is needed
    if season_int is not None:
        query = GET_ATHLETES_QUERY
        variables = build_query_variables(teamId=team_id_int, season=season_int)
    else:
        query = GET_ATHLETES_QUERY_NO_SEASON
        variables = build_query_variables(teamId=team_id_int)
    
    return await execute_graphql(query, variables, ctx)