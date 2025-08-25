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

# GraphQL queries for betting lines data
# Query with both season and week
GET_BETTING_LINES_WITH_SEASON_WEEK_QUERY = """
query GetBettingLines($season: smallint!, $week: smallint!, $limit: Int) {
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

# Query with only season
GET_BETTING_LINES_WITH_SEASON_QUERY = """
query GetBettingLines($season: smallint!, $limit: Int) {
    game(
        where: {
            season: { _eq: $season }
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

# Query with only week
GET_BETTING_LINES_WITH_WEEK_QUERY = """
query GetBettingLines($week: smallint!, $limit: Int) {
    game(
        where: {
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

# Query with team ID
GET_BETTING_LINES_WITH_TEAM_QUERY = """
query GetBettingLines($teamId: Int!, $season: smallint, $limit: Int) {
    game(
        where: {
            _and: [
                {
                    _or: [
                        { homeTeamId: { _eq: $teamId } }
                        { awayTeamId: { _eq: $teamId } }
                    ]
                }
                { season: { _eq: $season } }
                { lines: {} }
            ]
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

# Query with team ID but no season
GET_BETTING_LINES_WITH_TEAM_NO_SEASON_QUERY = """
query GetBettingLines($teamId: Int!, $limit: Int) {
    game(
        where: {
            _and: [
                {
                    _or: [
                        { homeTeamId: { _eq: $teamId } }
                        { awayTeamId: { _eq: $teamId } }
                    ]
                }
                { lines: {} }
            ]
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

# Query with no filters (all games with betting lines)
GET_ALL_BETTING_LINES_QUERY = """
query GetBettingLines($limit: Int) {
    game(
        where: {
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
    
    # Select appropriate query based on which parameters are provided
    if team_id_int is not None:
        # Team-specific queries
        if season_int is not None:
            query = GET_BETTING_LINES_WITH_TEAM_QUERY
            variables = build_query_variables(teamId=team_id_int, season=season_int, limit=limit_int)
        else:
            query = GET_BETTING_LINES_WITH_TEAM_NO_SEASON_QUERY
            variables = build_query_variables(teamId=team_id_int, limit=limit_int)
    elif season_int is not None and week_int is not None:
        # Both season and week
        query = GET_BETTING_LINES_WITH_SEASON_WEEK_QUERY
        variables = build_query_variables(season=season_int, week=week_int, limit=limit_int)
    elif season_int is not None:
        # Only season
        query = GET_BETTING_LINES_WITH_SEASON_QUERY
        variables = build_query_variables(season=season_int, limit=limit_int)
    elif week_int is not None:
        # Only week
        query = GET_BETTING_LINES_WITH_WEEK_QUERY
        variables = build_query_variables(week=week_int, limit=limit_int)
    else:
        # No filters - get all games with betting lines
        query = GET_ALL_BETTING_LINES_QUERY
        variables = build_query_variables(limit=limit_int)
    
    return await execute_graphql(query, variables, ctx)