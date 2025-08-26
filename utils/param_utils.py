"""
Parameter processing utilities for NCAAF MCP tools.

Centralizes parameter validation, type conversion, and preprocessing
to reduce duplication and ensure consistent behavior across all tools.
"""

from typing import Any, Optional, Union, Dict


def safe_int_conversion(value: Union[str, int, None], param_name: str = None) -> Optional[int]:
    """
    Safely convert a value to int, handling strings and None.
    
    Args:
        value: The value to convert (string, int, or None)
        param_name: Optional parameter name for better error messages
    
    Returns:
        Converted integer or None if input was None
    
    Raises:
        ValueError: If conversion fails and value is not None
    """
    if value is None:
        return None
    
    if isinstance(value, int):
        return value
    
    if isinstance(value, str):
        try:
            # Strip whitespace and quotes, then convert
            cleaned = value.strip().strip('"').strip("'")
            return int(cleaned)
        except ValueError:
            # Provide helpful error message
            if param_name:
                raise ValueError(f"Parameter '{param_name}' must be a valid integer, got '{value}'")
            else:
                raise ValueError(f"Invalid integer value: '{value}'")
    
    # For other types, try direct conversion
    try:
        return int(value)
    except (ValueError, TypeError):
        if param_name:
            raise ValueError(f"Parameter '{param_name}' must be convertible to integer, got {type(value).__name__}")
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to integer")


def safe_bool_conversion(value: Union[str, bool, None], param_name: str = None) -> Optional[bool]:
    """
    Safely convert a value to bool, handling strings and None.
    
    Args:
        value: The value to convert (string, bool, or None)
        param_name: Optional parameter name for better error messages
    
    Returns:
        Converted boolean or None if input was None
    """
    if value is None:
        return None
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        # Strip quotes and whitespace
        cleaned = value.strip().strip('"').strip("'")
        lower_val = cleaned.lower()
        if lower_val in ('true', '1', 'yes', 'on'):
            return True
        elif lower_val in ('false', '0', 'no', 'off'):
            return False
        else:
            if param_name:
                raise ValueError(f"Parameter '{param_name}' must be a valid boolean, got '{value}'")
            else:
                raise ValueError(f"Invalid boolean value: '{value}'")
    
    # For other types, use Python's truthiness
    return bool(value)


def safe_string_conversion(value: Union[str, None], param_name: str = None) -> Optional[str]:
    """
    Safely convert a value to string, handling None and cleaning whitespace.
    
    Args:
        value: The value to convert 
        param_name: Optional parameter name for better error messages
    
    Returns:
        Cleaned string or None if input was None
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        # Strip whitespace and quotes, return empty string as None
        cleaned = value.strip().strip('"').strip("'")
        return cleaned if cleaned else None
    
    # Convert other types to string
    return str(value).strip()


def validate_limit(limit: Union[str, int, None], default: int = 100, max_limit: int = 500) -> int:
    """
    Validate and convert limit parameter with bounds checking.
    
    Args:
        limit: Limit value to validate
        default: Default limit if None provided
        max_limit: Maximum allowed limit
        
    Returns:
        Validated limit value
        
    Raises:
        ValueError: If limit is invalid or exceeds max_limit
    """
    if limit is None:
        return default
    
    limit_int = safe_int_conversion(limit, 'limit')
    
    if limit_int <= 0:
        raise ValueError(f"Limit must be positive, got {limit_int}")
    
    if limit_int > max_limit:
        raise ValueError(f"Limit cannot exceed {max_limit}, got {limit_int}")
    
    return limit_int


def preprocess_team_params(
    team_id: Union[str, int, None] = None,
    conference: Union[str, None] = None,
    division: Union[str, None] = None,
    search: Union[str, None] = None,
    limit: Union[str, int, None] = None,
    include_records: Union[str, bool] = False,
    include_roster: Union[str, bool] = False,
    include_coaching: Union[str, bool] = False,
    include_facilities: Union[str, bool] = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Preprocess team tool parameters with validation and type conversion.
    
    Note: team_id should be resolved from team name before calling this function.
    
    Args:
        team_id: Resolved team ID (integer from team resolver)
        conference: Conference name filter
        division: Division name filter  
        search: Search query for team names/abbreviations
        limit: Result limit (can be string or int)
        include_records: Include team records and statistics
        include_roster: Include current roster information
        include_coaching: Include coaching staff details
        include_facilities: Include stadium and facility information
        **kwargs: Other parameters to pass through
    
    Returns:
        Dictionary with processed parameters
    """
    params = {}
    
    # Core filtering parameters
    if team_id is not None:
        params['team_id'] = safe_int_conversion(team_id, 'team_id')
    else:
        params['team_id'] = None
    
    if conference is not None:
        params['conference'] = safe_string_conversion(conference, 'conference')
    else:
        params['conference'] = None
    
    if division is not None:
        params['division'] = safe_string_conversion(division, 'division')
    else:
        params['division'] = None
    
    if search is not None:
        params['search'] = safe_string_conversion(search, 'search')
    else:
        params['search'] = None
    
    # Limit with validation
    params['limit'] = validate_limit(limit, default=100, max_limit=500)
    
    # Enhancement flags
    params['include_records'] = safe_bool_conversion(include_records, 'include_records')
    params['include_roster'] = safe_bool_conversion(include_roster, 'include_roster')  
    params['include_coaching'] = safe_bool_conversion(include_coaching, 'include_coaching')
    params['include_facilities'] = safe_bool_conversion(include_facilities, 'include_facilities')
    
    # Pass through other parameters unchanged
    params.update(kwargs)
    
    return params


def preprocess_game_params(
    season: Union[str, int, None] = None,
    week: Union[str, int, None] = None,
    team_id: Union[str, int, None] = None,
    limit: Union[str, int, None] = None,
    include_betting_lines: Union[str, bool] = False,
    include_weather: Union[str, bool] = False,
    include_media: Union[str, bool] = False,
    calculate_stats: Union[str, bool] = False,
    calculate_trends: Union[str, bool] = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Preprocess game tool parameters with validation and type conversion.
    
    Note: team_id should be resolved from team name before calling this function.
    
    Args:
        season: Season year (can be string or int)
        week: Week number (can be string or int)
        team_id: Resolved team ID (integer from team resolver)
        limit: Result limit (can be string or int)
        include_betting_lines: Include betting data (can be string or bool)
        include_weather: Include weather data (can be string or bool)
        include_media: Include media data (can be string or bool)
        calculate_stats: Calculate game statistics (can be string or bool)
        calculate_trends: Calculate trend analysis (can be string or bool)
        **kwargs: Other parameters to pass through
    
    Returns:
        Dictionary with processed parameters
    """
    params = {}
    
    # Core filtering parameters
    if season is not None:
        params['season'] = safe_int_conversion(season, 'season')
    
    if week is not None:
        params['week'] = safe_int_conversion(week, 'week')
    
    if team_id is not None:
        params['team_id'] = safe_int_conversion(team_id, 'team_id')
    
    # Limit with validation
    params['limit'] = validate_limit(limit, default=100, max_limit=1000)
    
    # Data inclusion flags
    params['include_betting_lines'] = safe_bool_conversion(include_betting_lines, 'include_betting_lines')
    params['include_weather'] = safe_bool_conversion(include_weather, 'include_weather')
    params['include_media'] = safe_bool_conversion(include_media, 'include_media')
    
    # Calculation flags
    params['calculate_stats'] = safe_bool_conversion(calculate_stats, 'calculate_stats')
    params['calculate_trends'] = safe_bool_conversion(calculate_trends, 'calculate_trends')
    
    # Pass through other parameters unchanged
    params.update(kwargs)
    
    return params


def preprocess_betting_params(
    season: Union[str, int, None] = None,
    week: Union[str, int, None] = None,
    team_id: Union[str, int, None] = None,
    limit: Union[str, int, None] = None,
    calculate_records: Union[str, bool] = False,
    calculate_trends: Union[str, bool] = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Preprocess betting tool parameters with validation and type conversion.
    
    Note: team_id should be resolved from team name before calling this function.
    
    Args:
        season: Season year (can be string or int)
        week: Week number (can be string or int)
        team_id: Resolved team ID (integer from team resolver)
        limit: Result limit (can be string or int)
        calculate_records: Calculate betting records (can be string or bool)
        calculate_trends: Calculate betting trends (can be string or bool)
        **kwargs: Other parameters to pass through
    
    Returns:
        Dictionary with processed parameters
    """
    params = {}
    
    # Core filtering parameters
    if season is not None:
        params['season'] = safe_int_conversion(season, 'season')
    
    if week is not None:
        params['week'] = safe_int_conversion(week, 'week')
    
    if team_id is not None:
        params['team_id'] = safe_int_conversion(team_id, 'team_id')
    
    # Limit with validation
    params['limit'] = validate_limit(limit, default=50, max_limit=500)
    
    # Calculation flags
    params['calculate_records'] = safe_bool_conversion(calculate_records, 'calculate_records')
    params['calculate_trends'] = safe_bool_conversion(calculate_trends, 'calculate_trends')
    
    # Pass through other parameters unchanged
    params.update(kwargs)
    
    return params


def preprocess_ranking_params(
    season: Union[str, int, None] = None,
    week: Union[str, int, None] = None,
    calculate_movement: Union[str, bool] = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Preprocess ranking tool parameters with validation and type conversion.
    
    Args:
        season: Season year (can be string or int)
        week: Week number (can be string or int)
        calculate_movement: Calculate ranking movement (can be string or bool)
        **kwargs: Other parameters to pass through
    
    Returns:
        Dictionary with processed parameters
    """
    params = {}
    
    # Core filtering parameters
    if season is not None:
        params['season'] = safe_int_conversion(season, 'season')
    
    if week is not None:
        params['week'] = safe_int_conversion(week, 'week')
    
    # Calculation flags
    params['calculate_movement'] = safe_bool_conversion(calculate_movement, 'calculate_movement')
    
    # Pass through other parameters unchanged
    params.update(kwargs)
    
    return params


def validate_team_lookup_params(team_id: Optional[int], school_name: Optional[str], search_query: Optional[str]) -> None:
    """
    Validate that at least one team lookup parameter is provided.
    
    Args:
        team_id: Team ID
        school_name: School name
        search_query: Search query
        
    Raises:
        ValueError: If no lookup parameters provided
    """
    if not any([team_id, school_name, search_query]):
        raise ValueError("Must provide at least one of: team_id, school_name, or search_query")