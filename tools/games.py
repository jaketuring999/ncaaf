"""
Game-related MCP tools for college football data.
"""

from typing import Optional, Union, Annotated

# Import from dedicated mcp module to avoid circular imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from src.graphql_executor import execute_graphql
from utils.param_utils import preprocess_game_params, safe_int_conversion, safe_bool_conversion
from utils.graphql_utils import build_query_variables
from utils.response_formatter import safe_format_response
from utils.team_resolver import resolve_optional_team_id

# GraphQL queries for game data
# Query for games with both season and week
GET_GAMES_WITH_SEASON_WEEK_QUERY = """
query GetGames(
    $season: smallint!
    $week: smallint!
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

# Query for games with only season
GET_GAMES_WITH_SEASON_QUERY = """
query GetGames(
    $season: smallint!
    $includeBettingLines: Boolean = false
    $includeWeather: Boolean = false
    $includeMedia: Boolean = false
    $limit: Int
) {
    game(
        where: {
            season: { _eq: $season }
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

# Query for games with only week
GET_GAMES_WITH_WEEK_QUERY = """
query GetGames(
    $week: smallint!
    $includeBettingLines: Boolean = false
    $includeWeather: Boolean = false
    $includeMedia: Boolean = false
    $limit: Int
) {
    game(
        where: {
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

# Query for all games (no season/week filter)
GET_ALL_GAMES_QUERY = """
query GetGames(
    $includeBettingLines: Boolean = false
    $includeWeather: Boolean = false
    $includeMedia: Boolean = false
    $limit: Int
) {
    game(
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

# Query for team games with season filter
GET_TEAM_GAMES_WITH_SEASON_QUERY = """
query GetTeamGames(
    $teamId: Int!
    $season: smallint!
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

# Query for team games without season filter
GET_TEAM_GAMES_QUERY = """
query GetTeamGames(
    $teamId: Int!
    $limit: Int
) {
    game(
        where: {
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
    season: Annotated[Optional[Union[str, int]], "Season year (e.g., 2024 or '2024')"] = None,
    week: Annotated[Optional[Union[str, int]], "Week number (1-15 for regular season, can be string or int)"] = None,
    team: Annotated[Optional[str], "Team name, abbreviation, or ID (e.g., 'Alabama', 'BAMA', '333')"] = None,
    include_betting_lines: Annotated[Union[str, bool], "Include betting line information (can be string or bool)"] = False,
    include_weather: Annotated[Union[str, bool], "Include weather data (can be string or bool)"] = False,
    include_media: Annotated[Union[str, bool], "Include media/TV information (can be string or bool)"] = False,
    limit: Annotated[Optional[Union[str, int]], "Maximum number of games to return (can be string or int)"] = None,
    calculate_stats: Annotated[Union[str, bool], "Calculate game statistics and trends (default: false)"] = False,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data (default: false)"] = False
) -> str:
    """
    Get games with flexible filtering options.
    
    Args:
        season: Season year (e.g., 2024 or "2024")
        week: Week number (1-15 for regular season, can be string or int)
        team: Team name, abbreviation, or ID (e.g., "Alabama", "BAMA", "333")
        include_betting_lines: Include betting line information (can be string or bool)
        include_weather: Include weather data (can be string or bool)
        include_media: Include media/TV information (can be string or bool)
        limit: Maximum number of games to return (can be string or int)
        calculate_stats: Calculate game statistics and trends (default: false)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        JSON string with game information, optionally enhanced with statistical analysis
    """
    # Preprocess parameters to handle string inputs
    calculate_stats_bool = safe_bool_conversion(calculate_stats, 'calculate_stats')
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    # Resolve team to ID if provided
    team_id = await resolve_optional_team_id(team)
    
    processed = preprocess_game_params(
        season=season,
        week=week,
        team_id=team_id,
        limit=limit,
        include_betting_lines=include_betting_lines,
        include_weather=include_weather,
        include_media=include_media
    )
    
    # If team is provided, use the appropriate team games query
    if processed.get('team_id'):
        if processed.get('season') is not None:
            # Use team games query with season filter
            variables = build_query_variables(
                teamId=processed.get('team_id'),
                season=processed.get('season'),
                limit=processed.get('limit')
            )
            result = await execute_graphql(GET_TEAM_GAMES_WITH_SEASON_QUERY, variables)
        else:
            # Use team games query without season filter
            variables = build_query_variables(
                teamId=processed.get('team_id'),
                limit=processed.get('limit')
            )
            result = await execute_graphql(GET_TEAM_GAMES_QUERY, variables)
        
        # Format response based on include_raw_data flag
        if include_raw_data_bool:
            return result
        else:
            return safe_format_response(result, 'games', include_raw_data_bool)
    
    # Select appropriate query based on which parameters are provided
    season = processed.get('season')
    week = processed.get('week')
    
    if season is not None and week is not None:
        # Both season and week provided
        query = GET_GAMES_WITH_SEASON_WEEK_QUERY
        variables = build_query_variables(
            season=season,
            week=week,
            includeBettingLines=processed.get('include_betting_lines', False),
            includeWeather=processed.get('include_weather', False),
            includeMedia=processed.get('include_media', False),
            limit=processed.get('limit')
        )
    elif season is not None:
        # Only season provided
        query = GET_GAMES_WITH_SEASON_QUERY
        variables = build_query_variables(
            season=season,
            includeBettingLines=processed.get('include_betting_lines', False),
            includeWeather=processed.get('include_weather', False),
            includeMedia=processed.get('include_media', False),
            limit=processed.get('limit')
        )
    elif week is not None:
        # Only week provided
        query = GET_GAMES_WITH_WEEK_QUERY
        variables = build_query_variables(
            week=week,
            includeBettingLines=processed.get('include_betting_lines', False),
            includeWeather=processed.get('include_weather', False),
            includeMedia=processed.get('include_media', False),
            limit=processed.get('limit')
        )
    else:
        # No season or week filters
        query = GET_ALL_GAMES_QUERY
        variables = build_query_variables(
            includeBettingLines=processed.get('include_betting_lines', False),
            includeWeather=processed.get('include_weather', False),
            includeMedia=processed.get('include_media', False),
            limit=processed.get('limit')
        )
    
    # Execute the GraphQL query
    result = await execute_graphql(query, variables)
    
    # Add game statistics if requested
    if calculate_stats_bool:
        try:
            # Import game utilities
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from utils.game_utils import calculate_game_stats_from_graphql
            
            # Calculate game statistics
            game_stats = calculate_game_stats_from_graphql(result, "comprehensive")
            
            if game_stats and 'error' not in game_stats:
                # Parse the result to add game statistics
                import json
                result_data = json.loads(result)
                result_data['game_statistics'] = game_stats
                result = json.dumps(result_data, indent=2)
            elif game_stats and 'error' in game_stats:
                # Add error info but don't fail the whole query
                result_data = json.loads(result)
                result_data['game_statistics_error'] = game_stats['error']
                result = json.dumps(result_data, indent=2)
                
        except Exception:
            # Don't fail the main query if statistics calculation fails
            pass
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'games', include_raw_data_bool)

@mcp.tool()
async def GetGamesByWeek(
    season: Annotated[Union[str, int], "Season year (e.g., 2024 or '2024')"],
    week: Annotated[Union[str, int], "Week number (1-15 for regular season, can be string or int)"],
    limit: Annotated[Optional[Union[str, int]], "Maximum number of games to return (can be string or int)"] = None,
    calculate_weekly_trends: Annotated[Union[str, bool], "Calculate weekly betting and scoring trends (default: false)"] = False,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data (default: false)"] = False
) -> str:
    """
    Get all games for a specific week and season.
    
    Args:
        season: Season year (e.g., 2024 or "2024")
        week: Week number (1-15 for regular season, can be string or int)
        limit: Maximum number of games to return (can be string or int)
        calculate_weekly_trends: Calculate weekly betting and scoring trends (default: false)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        JSON string with games for the specified week, optionally enhanced with weekly trends
    """
    # Convert string inputs to appropriate types
    season_int = safe_int_conversion(season, 'season')
    week_int = safe_int_conversion(week, 'week')
    limit_int = safe_int_conversion(limit, 'limit') if limit is not None else None
    calculate_weekly_trends_bool = safe_bool_conversion(calculate_weekly_trends, 'calculate_weekly_trends')
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    variables = build_query_variables(season=season_int, week=week_int, limit=limit_int)
    
    # Execute the GraphQL query
    result = await execute_graphql(GET_GAMES_BY_WEEK_QUERY, variables)
    
    # Add weekly trends analysis if requested
    if calculate_weekly_trends_bool:
        try:
            # Import game utilities
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from utils.game_utils import calculate_game_stats_from_graphql
            
            # Calculate weekly trends
            weekly_trends = calculate_game_stats_from_graphql(result, "weekly")
            
            if weekly_trends and 'error' not in weekly_trends:
                # Parse the result to add weekly trends
                import json
                result_data = json.loads(result)
                result_data['weekly_trends'] = weekly_trends
                result = json.dumps(result_data, indent=2)
            elif weekly_trends and 'error' in weekly_trends:
                # Add error info but don't fail the whole query
                result_data = json.loads(result)
                result_data['weekly_trends_error'] = weekly_trends['error']
                result = json.dumps(result_data, indent=2)
                
        except Exception:
            # Don't fail the main query if trends calculation fails
            pass
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'games', include_raw_data_bool)

@mcp.tool()
async def GetTeamGames(
    team: Annotated[str, "Team name, abbreviation, or ID (e.g., 'Alabama', 'BAMA', '333')"],
    season: Annotated[Optional[Union[str, int]], "Season year (optional, can be string or int)"] = None,
    limit: Annotated[Optional[Union[str, int]], "Maximum number of games to return (can be string or int)"] = None,
    calculate_performance: Annotated[Union[str, bool], "Calculate team performance metrics (default: false)"] = False,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data (default: false)"] = False
) -> str:
    """
    Get all games for a specific team.
    
    Args:
        team: Team name, abbreviation, or ID (e.g., "Alabama", "BAMA", "333")
        season: Season year (optional, can be string or int)
        limit: Maximum number of games to return (can be string or int)
        calculate_performance: Calculate team performance metrics (default: false)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        JSON string with team's games, optionally enhanced with performance analysis
    """
    # Convert string inputs to appropriate types and resolve team
    from utils.team_resolver import resolve_team_id
    team_id_int = await resolve_team_id(team)
    season_int = safe_int_conversion(season, 'season') if season is not None else None
    limit_int = safe_int_conversion(limit, 'limit') if limit is not None else None
    calculate_performance_bool = safe_bool_conversion(calculate_performance, 'calculate_performance')
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    # Select appropriate query based on whether season is provided
    if season_int is not None:
        query = GET_TEAM_GAMES_WITH_SEASON_QUERY
        variables = build_query_variables(teamId=team_id_int, season=season_int, limit=limit_int)
    else:
        query = GET_TEAM_GAMES_QUERY
        variables = build_query_variables(teamId=team_id_int, limit=limit_int)
    
    # Execute the GraphQL query
    result = await execute_graphql(query, variables)
    
    # Add team performance analysis if requested
    if calculate_performance_bool:
        try:
            # Import team utilities
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from utils.team_utils import calculate_team_performance_from_graphql
            
            # Calculate team performance
            team_performance = calculate_team_performance_from_graphql(result, team_id_int)
            
            if team_performance and 'error' not in team_performance:
                # Parse the result to add team performance analysis
                import json
                result_data = json.loads(result)
                result_data['team_performance'] = team_performance
                result = json.dumps(result_data, indent=2)
            elif team_performance and 'error' in team_performance:
                # Add error info but don't fail the whole query
                result_data = json.loads(result)
                result_data['team_performance_error'] = team_performance['error']
                result = json.dumps(result_data, indent=2)
                
        except Exception:
            # Don't fail the main query if performance analysis fails
            pass
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'games', include_raw_data_bool)

@mcp.tool()
async def GetRecentGames(
    limit: Annotated[Optional[Union[str, int]], "Maximum number of recent games to return (default: 20, can be string or int)"] = 20,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data (default: false)"] = False
) -> str:
    """
    Get recently completed games.
    
    Args:
        limit: Maximum number of recent games to return (default: 20, can be string or int)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        JSON string with recently completed games
    """
    # Convert string input to integer
    limit_int = safe_int_conversion(limit, 'limit') if limit is not None else 20
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    variables = build_query_variables(limit=limit_int)
    result = await execute_graphql(GET_RECENT_GAMES_QUERY, variables)
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'games', include_raw_data_bool)