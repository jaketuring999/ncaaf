"""
GraphQL utilities for NCAAF MCP tools.

Provides shared fragments, query builders, and common GraphQL patterns
to reduce duplication across tools and ensure consistency.
"""

from typing import Dict, Any, Optional, List, Union


# =============================================================================
# GraphQL Fragments
# =============================================================================

TEAM_INFO_FRAGMENT = """
    teamId
    school
    conference
    conferenceId
    division
    classification
    abbreviation
"""

GAME_BASE_FRAGMENT = """
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
"""

TEAM_EXTENDED_FRAGMENT = """
    teamId
    school
    mascot
    conference
    conferenceId
    division
    classification
    abbreviation
    color
    alternateColor
"""

WEATHER_FRAGMENT = """
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
"""

MEDIA_FRAGMENT = """
    mediaType
    name
"""

BETTING_LINES_FRAGMENT = """
    spread
    spreadOpen
    overUnder
    overUnderOpen
    moneylineHome
    moneylineAway
"""

RANKING_FRAGMENT = """
    season
    week
    poll
    school
    conference
    firstPlaceVotes
    points
    rank
"""

ATHLETE_BASE_FRAGMENT = """
    id
    firstName
    lastName
    jersey
    position
    height
    weight
    year
    hometown
"""


# =============================================================================
# Query Builders
# =============================================================================

def build_query_variables(**kwargs) -> Dict[str, Any]:
    """
    Build GraphQL query variables dictionary, filtering out None values.
    
    Args:
        **kwargs: Variable name-value pairs
        
    Returns:
        Dictionary with non-None values
    """
    return {k: v for k, v in kwargs.items() if v is not None}


def build_team_info_fields(extended: bool = False) -> str:
    """
    Build team info fields for GraphQL queries.
    
    Args:
        extended: Whether to include extended team information
        
    Returns:
        GraphQL field string
    """
    return TEAM_EXTENDED_FRAGMENT if extended else TEAM_INFO_FRAGMENT


def build_conditional_fragments(
    include_weather: bool = False,
    include_media: bool = False, 
    include_betting_lines: bool = False
) -> Dict[str, str]:
    """
    Build conditional GraphQL fragments based on inclusion flags.
    
    Args:
        include_weather: Include weather fragment
        include_media: Include media fragment
        include_betting_lines: Include betting lines fragment
        
    Returns:
        Dictionary with fragment names and their conditional inclusions
    """
    fragments = {}
    
    if include_weather:
        fragments['weather'] = f"weather @include(if: $includeWeather) {{\n        {WEATHER_FRAGMENT}\n        }}"
    
    if include_media:
        fragments['media'] = f"mediaInfo @include(if: $includeMedia) {{\n        {MEDIA_FRAGMENT}\n        }}"
    
    if include_betting_lines:
        fragments['betting'] = f"lines @include(if: $includeBettingLines) {{\n        {BETTING_LINES_FRAGMENT}\n        }}"
    
    return fragments


def build_where_clause_for_teams(
    team_id: Optional[int] = None,
    conference: Optional[str] = None,
    division: Optional[str] = None,
    search: Optional[str] = None
) -> str:
    """
    Build WHERE clause for team queries based on filters.
    
    Args:
        team_id: Filter by specific team ID
        conference: Filter by conference
        division: Filter by division  
        search: Search in team names and abbreviations
        
    Returns:
        GraphQL WHERE clause string
    """
    conditions = []
    
    if team_id is not None:
        conditions.append("{ teamId: { _eq: $teamId } }")
    
    if conference is not None:
        conditions.append("{ conference: { _eq: $conference } }")
    
    if division is not None:
        conditions.append("{ division: { _eq: $division } }")
    
    if search is not None:
        conditions.append("""{ 
            _or: [
                { school: { _ilike: $search } }
                { abbreviation: { _ilike: $search } }
            ]
        }""")
    
    if not conditions:
        return ""
    
    if len(conditions) == 1:
        return f"where: {conditions[0]}"
    else:
        conditions_str = ",\n            ".join(conditions)
        return f"""where: {{
        _and: [
            {conditions_str}
        ]
    }}"""


def build_where_clause_for_games(
    season: Optional[int] = None,
    week: Optional[int] = None,
    team_id: Optional[int] = None
) -> str:
    """
    Build WHERE clause for game queries based on filters.
    
    Args:
        season: Filter by season
        week: Filter by week
        team_id: Filter by team involvement (home or away)
        
    Returns:
        GraphQL WHERE clause string
    """
    conditions = []
    
    if season is not None:
        conditions.append("{ season: { _eq: $season } }")
    
    if week is not None:
        conditions.append("{ week: { _eq: $week } }")
    
    if team_id is not None:
        conditions.append("""{
            _or: [
                { homeTeamId: { _eq: $teamId } }
                { awayTeamId: { _eq: $teamId } }
            ]
        }""")
    
    if not conditions:
        return ""
    
    if len(conditions) == 1:
        return f"where: {conditions[0]}"
    else:
        conditions_str = ",\n            ".join(conditions)
        return f"""where: {{
        _and: [
            {conditions_str}
        ]
    }}"""


def build_team_query(
    team_id: Optional[int] = None,
    conference: Optional[str] = None, 
    division: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
    extended_info: bool = False
) -> str:
    """
    Build complete team query with dynamic WHERE clause and fields.
    
    Args:
        team_id: Filter by specific team ID
        conference: Filter by conference
        division: Filter by division
        search: Search in team names/abbreviations  
        limit: Limit results
        extended_info: Include extended team information
        
    Returns:
        Complete GraphQL query string
    """
    where_clause = build_where_clause_for_teams(team_id, conference, division, search)
    team_fields = build_team_info_fields(extended=extended_info)
    limit_clause = "limit: $limit" if limit else ""
    
    return f"""
query GetTeams({build_team_query_params(team_id, conference, division, search, limit)}) {{
    currentTeams(
        {where_clause}
        orderBy: {{ school: ASC }}
        {limit_clause}
    ) {{
        {team_fields}
    }}
}}
""".strip()


def build_team_query_params(
    team_id: Optional[int] = None,
    conference: Optional[str] = None,
    division: Optional[str] = None, 
    search: Optional[str] = None,
    limit: Optional[int] = None
) -> str:
    """
    Build parameter definitions for team queries.
    
    Args:
        team_id: Team ID parameter
        conference: Conference parameter
        division: Division parameter
        search: Search parameter
        limit: Limit parameter
        
    Returns:
        GraphQL parameter definitions string
    """
    params = []
    
    if team_id is not None:
        params.append("$teamId: Int!")
    
    if conference is not None:
        params.append("$conference: String!")
    
    if division is not None:
        params.append("$division: String!")
    
    if search is not None:
        params.append("$search: String!")
    
    if limit is not None:
        params.append("$limit: Int")
    
    return ", ".join(params)


def build_game_query_with_enhancements(
    season: Optional[int] = None,
    week: Optional[int] = None,
    team_id: Optional[int] = None,
    limit: Optional[int] = None,
    include_weather: bool = False,
    include_media: bool = False,
    include_betting_lines: bool = False
) -> str:
    """
    Build complete game query with optional enhancements.
    
    Args:
        season: Filter by season
        week: Filter by week  
        team_id: Filter by team
        limit: Limit results
        include_weather: Include weather data
        include_media: Include media data
        include_betting_lines: Include betting data
        
    Returns:
        Complete GraphQL query string
    """
    # Build parameter definitions
    params = []
    if season is not None:
        params.append("$season: smallint!")
    if week is not None:
        params.append("$week: smallint!")
    if team_id is not None:
        params.append("$teamId: Int!")
    if limit is not None:
        params.append("$limit: Int")
    
    # Add boolean parameters for conditional fragments
    if include_weather:
        params.append("$includeWeather: Boolean = false")
    if include_media:
        params.append("$includeMedia: Boolean = false") 
    if include_betting_lines:
        params.append("$includeBettingLines: Boolean = false")
    
    param_string = ", ".join(params)
    where_clause = build_where_clause_for_games(season, week, team_id)
    limit_clause = "limit: $limit" if limit else ""
    
    # Build conditional fragments
    conditional_fragments = build_conditional_fragments(
        include_weather=include_weather,
        include_media=include_media,
        include_betting_lines=include_betting_lines
    )
    
    fragments_str = "\n        ".join(conditional_fragments.values())
    
    return f"""
query GetGames({param_string}) {{
    game(
        {where_clause}
        orderBy: [
            {{ startDate: ASC }}
            {{ id: ASC }}
        ]
        {limit_clause}
    ) {{
        {GAME_BASE_FRAGMENT}
        
        homeTeamInfo {{
            {TEAM_INFO_FRAGMENT}
        }}
        
        awayTeamInfo {{
            {TEAM_INFO_FRAGMENT}
        }}
        
        {fragments_str}
    }}
}}
""".strip()


def format_search_pattern(search_term: str) -> str:
    """
    Format a search term for GraphQL ILIKE operations.
    
    Args:
        search_term: Raw search term
        
    Returns:
        Formatted search pattern with wildcards
    """
    if not search_term:
        return ""
    
    # Add wildcards for partial matching if not already present
    if not search_term.startswith('%'):
        search_term = f"%{search_term}"
    if not search_term.endswith('%'):
        search_term = f"{search_term}%"
    
    return search_term


# =============================================================================
# Response Enhancers
# =============================================================================

def enhance_response_with_metadata(
    response_data: Dict[str, Any],
    query_params: Dict[str, Any],
    enhancements: Dict[str, bool]
) -> Dict[str, Any]:
    """
    Enhance GraphQL response with metadata about the query and enhancements applied.
    
    Args:
        response_data: Original GraphQL response data
        query_params: Parameters used in the query
        enhancements: Enhancement flags that were applied
        
    Returns:
        Enhanced response with metadata
    """
    # Count results
    total_results = 0
    if 'data' in response_data:
        for key, value in response_data['data'].items():
            if isinstance(value, list):
                total_results += len(value)
    
    response_data['metadata'] = {
        'total_results': total_results,
        'query_parameters': {k: v for k, v in query_params.items() if v is not None},
        'enhancements_applied': {k: v for k, v in enhancements.items() if v is True},
        'timestamp': None  # Could be added by caller
    }
    
    return response_data