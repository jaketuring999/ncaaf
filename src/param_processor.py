"""
Parameter preprocessing utilities for MCP tools.

Automatically converts string parameters to appropriate types for better UX.
Users can pass "2024" or 2024 for season - both will work.
"""

from typing import Any, Optional, Union


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


def preprocess_team_params(
    team_id: Union[str, int, None] = None,
    limit: Union[str, int, None] = None,
    **kwargs
) -> dict:
    """
    Preprocess common team tool parameters.
    
    Args:
        team_id: Team ID (can be string or int)
        limit: Result limit (can be string or int)
        **kwargs: Other parameters to pass through
    
    Returns:
        Dictionary with processed parameters
    """
    params = {}
    
    if team_id is not None:
        params['team_id'] = safe_int_conversion(team_id, 'team_id')
    
    if limit is not None:
        params['limit'] = safe_int_conversion(limit, 'limit')
    
    # Pass through other parameters unchanged
    params.update(kwargs)
    
    return params


def preprocess_game_params(
    season: Union[str, int, None] = None,
    week: Union[str, int, None] = None,
    team_id: Union[str, int, None] = None,
    limit: Union[str, int, None] = None,
    include_betting_lines: Union[str, bool, None] = None,
    include_weather: Union[str, bool, None] = None,
    include_media: Union[str, bool, None] = None,
    **kwargs
) -> dict:
    """
    Preprocess game tool parameters.
    
    Args:
        season: Season year (can be string or int)
        week: Week number (can be string or int)
        team_id: Team ID (can be string or int)
        limit: Result limit (can be string or int)
        include_betting_lines: Include betting data (can be string or bool)
        include_weather: Include weather data (can be string or bool)
        include_media: Include media data (can be string or bool)
        **kwargs: Other parameters to pass through
    
    Returns:
        Dictionary with processed parameters
    """
    params = {}
    
    if season is not None:
        params['season'] = safe_int_conversion(season, 'season')
    
    if week is not None:
        params['week'] = safe_int_conversion(week, 'week')
    
    if team_id is not None:
        params['team_id'] = safe_int_conversion(team_id, 'team_id')
    
    if limit is not None:
        params['limit'] = safe_int_conversion(limit, 'limit')
    
    if include_betting_lines is not None:
        params['include_betting_lines'] = safe_bool_conversion(include_betting_lines, 'include_betting_lines')
    
    if include_weather is not None:
        params['include_weather'] = safe_bool_conversion(include_weather, 'include_weather')
    
    if include_media is not None:
        params['include_media'] = safe_bool_conversion(include_media, 'include_media')
    
    # Pass through other parameters unchanged
    params.update(kwargs)
    
    return params


def preprocess_ranking_params(
    season: Union[str, int, None] = None,
    week: Union[str, int, None] = None,
    **kwargs
) -> dict:
    """
    Preprocess ranking tool parameters.
    
    Args:
        season: Season year (can be string or int)
        week: Week number (can be string or int)
        **kwargs: Other parameters to pass through
    
    Returns:
        Dictionary with processed parameters
    """
    params = {}
    
    if season is not None:
        params['season'] = safe_int_conversion(season, 'season')
    
    if week is not None:
        params['week'] = safe_int_conversion(week, 'week')
    
    # Pass through other parameters unchanged
    params.update(kwargs)
    
    return params