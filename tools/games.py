"""
Game-related MCP tools for college football data.
"""

from typing import Optional, Union
from fastmcp import Context

# Import from dedicated mcp module to avoid circular imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.mcp_server import mcp
from src.graphql_executor import execute_graphql, build_query_variables
from src.param_processor import preprocess_game_params, safe_int_conversion

# GraphQL queries for game data
GET_GAMES_QUERY = """
query GetGames(
    $season: smallint
    $week: smallint
    $teamId: Int
    $includeBettingLines: Boolean = false
    $includeWeather: Boolean = false
    $includeMedia: Boolean = false
    $limit: Int
) {
    game(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
        }
        orderBy: [
            { startDate: ASC }
            { id: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        venueId
        homePoints
        awayPoints
        notes
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        weather @include(if: $includeWeather) {
            condition {
                id
                description
            }
            temperature
            dewpoint
            humidity
            precipitation
            pressure
            snowfall
            windDirection
            windGust
            windSpeed
            weatherConditionCode
        }
        
        mediaInfo @include(if: $includeMedia) {
            mediaType
            name
        }
        
        lines @include(if: $includeBettingLines) {
            spread
            spreadOpen
            moneylineHome
            moneylineAway
            overUnder
            overUnderOpen
        }
    }
}
"""

GET_GAMES_BY_WEEK_QUERY = """
query GetGamesByWeek(
    $season: smallint!
    $week: smallint!
    $limit: Int
) {
    game(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
        }
        orderBy: [
            { startDate: ASC }
            { id: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        homePoints
        awayPoints
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
    }
}
"""

GET_TEAM_GAMES_QUERY = """
query GetTeamGames(
    $teamId: Int!
    $season: smallint
    $limit: Int
) {
    game(
        where: {
            season: { _eq: $season }
            _or: [
                { homeTeamId: { _eq: $teamId } }
                { awayTeamId: { _eq: $teamId } }
            ]
        }
        orderBy: [
            { startDate: ASC }
            { id: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        homePoints
        awayPoints
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
    }
}
"""

GET_RECENT_GAMES_QUERY = """
query GetRecentGames($limit: Int) {
    game(
        where: {
            status: { _eq: "completed" }
        }
        orderBy: { startDate: DESC }
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        status
        homePoints
        awayPoints
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
    }
}
"""

@mcp.tool()
async def GetGames(
    season: Optional[Union[str, int]] = None,
    week: Optional[Union[str, int]] = None,
    team_id: Optional[Union[str, int]] = None,
    include_betting_lines: Union[str, bool] = False,
    include_weather: Union[str, bool] = False,
    include_media: Union[str, bool] = False,
    limit: Optional[Union[str, int]] = None,
    ctx: Context = None
) -> str:
    """
    Get games with flexible filtering options.
    
    Args:
        season: Season year (e.g., 2024 or "2024")
        week: Week number (1-15 for regular season, can be string or int)
        team_id: Get games for specific team (can be string or int)
        include_betting_lines: Include betting line information (can be string or bool)
        include_weather: Include weather data (can be string or bool)
        include_media: Include media/TV information (can be string or bool)
        limit: Maximum number of games to return (can be string or int)
    
    Returns:
        JSON string with game information
    """
    # Preprocess parameters to handle string inputs
    processed = preprocess_game_params(
        season=season,
        week=week,
        team_id=team_id,
        limit=limit,
        include_betting_lines=include_betting_lines,
        include_weather=include_weather,
        include_media=include_media
    )
    
    # If team_id is provided, use the team games query to avoid null issues
    if processed.get('team_id'):
        variables = build_query_variables(
            teamId=processed.get('team_id'),
            season=processed.get('season'),
            limit=processed.get('limit')
        )
        return await execute_graphql(GET_TEAM_GAMES_QUERY, variables, ctx)
    else:
        # Use regular games query for season/week filtering
        variables = build_query_variables(
            season=processed.get('season'),
            week=processed.get('week'),
            includeBettingLines=processed.get('include_betting_lines', False),
            includeWeather=processed.get('include_weather', False),
            includeMedia=processed.get('include_media', False),
            limit=processed.get('limit')
        )
        return await execute_graphql(GET_GAMES_QUERY, variables, ctx)

@mcp.tool()
async def GetGamesByWeek(
    season: Union[str, int],
    week: Union[str, int],
    limit: Optional[Union[str, int]] = None,
    ctx: Context = None
) -> str:
    """
    Get all games for a specific week and season.
    
    Args:
        season: Season year (e.g., 2024 or "2024")
        week: Week number (1-15 for regular season, can be string or int)
        limit: Maximum number of games to return (can be string or int)
    
    Returns:
        JSON string with games for the specified week
    """
    # Convert string inputs to integers
    season_int = safe_int_conversion(season, 'season')
    week_int = safe_int_conversion(week, 'week')
    limit_int = safe_int_conversion(limit, 'limit') if limit is not None else None
    
    variables = build_query_variables(season=season_int, week=week_int, limit=limit_int)
    return await execute_graphql(GET_GAMES_BY_WEEK_QUERY, variables, ctx)

@mcp.tool()
async def GetTeamGames(
    team_id: Union[str, int],
    season: Optional[Union[str, int]] = None,
    limit: Optional[Union[str, int]] = None,
    ctx: Context = None
) -> str:
    """
    Get all games for a specific team.
    
    Args:
        team_id: Team ID number (can be string or int)
        season: Season year (optional, can be string or int)
        limit: Maximum number of games to return (can be string or int)
    
    Returns:
        JSON string with team's games
    """
    # Convert string inputs to integers
    team_id_int = safe_int_conversion(team_id, 'team_id')
    season_int = safe_int_conversion(season, 'season') if season is not None else None
    limit_int = safe_int_conversion(limit, 'limit') if limit is not None else None
    
    variables = build_query_variables(teamId=team_id_int, season=season_int, limit=limit_int)
    return await execute_graphql(GET_TEAM_GAMES_QUERY, variables, ctx)

@mcp.tool()
async def GetRecentGames(
    limit: Optional[Union[str, int]] = 20,
    ctx: Context = None
) -> str:
    """
    Get recently completed games.
    
    Args:
        limit: Maximum number of recent games to return (default: 20, can be string or int)
    
    Returns:
        JSON string with recently completed games
    """
    # Convert string input to integer
    limit_int = safe_int_conversion(limit, 'limit') if limit is not None else 20
    
    variables = build_query_variables(limit=limit_int)
    return await execute_graphql(GET_RECENT_GAMES_QUERY, variables, ctx)