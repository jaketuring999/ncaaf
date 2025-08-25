"""
Game-related MCP tools for college football data.
"""

from typing import Optional
from fastmcp import Context

# Import from dedicated mcp module to avoid circular imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.mcp_server import mcp
from src.graphql_executor import execute_graphql, build_query_variables

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
            _and: [
                { season: { _eq: $season } }
                { week: { _eq: $week } }
                {
                    _or: [
                        { homeTeamId: { _eq: $teamId } }
                        { awayTeamId: { _eq: $teamId } }
                    ]
                }
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
            _and: [
                { season: { _eq: $season } }
                {
                    _or: [
                        { homeTeamId: { _eq: $teamId } }
                        { awayTeamId: { _eq: $teamId } }
                    ]
                }
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
            status: { _in: ["completed", "final"] }
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
    season: Optional[int] = None,
    week: Optional[int] = None,
    team_id: Optional[int] = None,
    include_betting_lines: bool = False,
    include_weather: bool = False,
    include_media: bool = False,
    limit: Optional[int] = None,
    ctx: Context = None
) -> str:
    """
    Get games with flexible filtering options.
    
    Args:
        season: Season year (e.g., 2024)
        week: Week number (1-15 for regular season)
        team_id: Get games for specific team
        include_betting_lines: Include betting line information
        include_weather: Include weather data
        include_media: Include media/TV information
        limit: Maximum number of games to return
    
    Returns:
        JSON string with game information
    """
    variables = build_query_variables(
        season=season,
        week=week,
        teamId=team_id,
        includeBettingLines=include_betting_lines,
        includeWeather=include_weather,
        includeMedia=include_media,
        limit=limit
    )
    return await execute_graphql(GET_GAMES_QUERY, variables, ctx)

@mcp.tool()
async def GetGamesByWeek(
    season: int,
    week: int,
    limit: Optional[int] = None,
    ctx: Context = None
) -> str:
    """
    Get all games for a specific week and season.
    
    Args:
        season: Season year (e.g., 2024)
        week: Week number (1-15 for regular season)
        limit: Maximum number of games to return
    
    Returns:
        JSON string with games for the specified week
    """
    variables = build_query_variables(season=season, week=week, limit=limit)
    return await execute_graphql(GET_GAMES_BY_WEEK_QUERY, variables, ctx)

@mcp.tool()
async def GetTeamGames(
    team_id: int,
    season: Optional[int] = None,
    limit: Optional[int] = None,
    ctx: Context = None
) -> str:
    """
    Get all games for a specific team.
    
    Args:
        team_id: Team ID number
        season: Season year (optional, defaults to current season)
        limit: Maximum number of games to return
    
    Returns:
        JSON string with team's games
    """
    variables = build_query_variables(teamId=team_id, season=season, limit=limit)
    return await execute_graphql(GET_TEAM_GAMES_QUERY, variables, ctx)

@mcp.tool()
async def GetRecentGames(
    limit: Optional[int] = 20,
    ctx: Context = None
) -> str:
    """
    Get recently completed games.
    
    Args:
        limit: Maximum number of recent games to return (default: 20)
    
    Returns:
        JSON string with recently completed games
    """
    variables = build_query_variables(limit=limit)
    return await execute_graphql(GET_RECENT_GAMES_QUERY, variables, ctx)