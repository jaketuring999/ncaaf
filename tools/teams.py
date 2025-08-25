"""
Team-related MCP tools for college football data.

Consolidated team tools with flexible filtering and optional enhancements.
"""

from typing import Optional, Union, Annotated
from fastmcp import Context

# Import from dedicated mcp module to avoid circular imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from src.graphql_executor import execute_graphql
from utils.param_utils import preprocess_team_params, validate_team_lookup_params, safe_int_conversion, safe_string_conversion, safe_bool_conversion
from utils.graphql_utils import build_query_variables, format_search_pattern
from utils.response_formatter import safe_format_response

# GraphQL queries for team operations
GET_TEAMS_QUERY = """
query GetTeams($conference: String, $division: String, $search: String, $limit: Int) {
    currentTeams(
        where: {where_clause}
        orderBy: { school: ASC }
        limit: $limit
    ) {
        teamId
        school
        conference
        conferenceId
        division
        classification
        abbreviation
    }
}
"""

GET_TEAMS_ALL_QUERY = """
query GetTeamsAll($limit: Int) {
    currentTeams(
        orderBy: { school: ASC }
        limit: $limit
    ) {
        teamId
        school
        conference
        conferenceId
        division
        classification
        abbreviation
    }
}
"""

GET_TEAMS_BY_CONFERENCE_QUERY = """
query GetTeamsByConference($conference: String!, $limit: Int) {
    currentTeams(
        where: { conference: { _eq: $conference } }
        orderBy: { school: ASC }
        limit: $limit
    ) {
        teamId
        school
        conference
        conferenceId
        division
        classification
        abbreviation
    }
}
"""

GET_TEAMS_BY_DIVISION_QUERY = """
query GetTeamsByDivision($division: String!, $limit: Int) {
    currentTeams(
        where: { division: { _eq: $division } }
        orderBy: { school: ASC }
        limit: $limit
    ) {
        teamId
        school
        conference
        conferenceId
        division
        classification
        abbreviation
    }
}
"""

SEARCH_TEAMS_QUERY = """
query SearchTeams($searchTerm: String!, $limit: Int) {
    currentTeams(
        where: {
            _or: [
                { school: { _ilike: $searchTerm } }
                { abbreviation: { _ilike: $searchTerm } }
            ]
        }
        orderBy: { school: ASC }
        limit: $limit
    ) {
        teamId
        school
        conference
        conferenceId
        division
        classification
        abbreviation
    }
}
"""

GET_TEAM_DETAILS_QUERY_BY_ID = """
query GetTeamDetailsById($teamId: Int!) {
    currentTeams(
        where: { teamId: { _eq: $teamId } }
    ) {
        teamId
        school
        conference
        conferenceId
        division
        classification
        abbreviation
    }
}
"""

GET_TEAM_DETAILS_QUERY_BY_NAME = """
query GetTeamDetailsByName($school: String!) {
    currentTeams(
        where: { school: { _ilike: $school } }
    ) {
        teamId
        school
        conference
        conferenceId
        division
        classification
        abbreviation
    }
}
"""

@mcp.tool()
async def GetTeams(
    conference: Annotated[Optional[str], "Conference name filter (e.g., 'ACC', 'SEC', 'Big 12')"] = None,
    division: Annotated[Optional[str], "Division name filter (e.g., 'FBS', 'FCS')"] = None,
    search: Annotated[Optional[str], "Search teams by name or abbreviation"] = None,
    limit: Annotated[Optional[Union[str, int]], "Maximum number of teams to return (default: 100, can be string or int)"] = 100,
    include_records: Annotated[Union[str, bool], "Include team records and season statistics (default: false)"] = False,
    include_roster: Annotated[Union[str, bool], "Include current roster information (default: false)"] = False,
    include_coaching: Annotated[Union[str, bool], "Include coaching staff details (default: false)"] = False,
    include_facilities: Annotated[Union[str, bool], "Include stadium and facility information (default: false)"] = False,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data (default: false)"] = False,
    ctx: Context = None
) -> str:
    """
    Get college football teams with flexible filtering and optional enhancements.
    
    This consolidated tool replaces GetTeamsSimple and GetTeamsByConference,
    providing a single interface for all team retrieval needs.
    
    Args:
        conference: Filter by conference name (e.g., "ACC", "SEC", "Big 12")
        division: Filter by division (e.g., "FBS", "FCS")
        search: Search teams by name or abbreviation
        limit: Maximum number of teams to return (default: 100)
        include_records: Include team records and statistics (future enhancement)
        include_roster: Include current roster information (future enhancement)
        include_coaching: Include coaching staff details (future enhancement) 
        include_facilities: Include stadium and facility information (future enhancement)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        JSON string with team information
    
    Examples:
        - GetTeams() -> All teams (up to 100)
        - GetTeams(conference="SEC") -> SEC teams only
        - GetTeams(search="Alabama") -> Teams matching "Alabama"
        - GetTeams(conference="ACC", limit=20) -> First 20 ACC teams
    """
    # Process and validate parameters
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    params = preprocess_team_params(
        conference=conference,
        division=division,
        search=search,
        limit=limit,
        include_records=include_records,
        include_roster=include_roster,
        include_coaching=include_coaching,
        include_facilities=include_facilities
    )
    
    # Select appropriate query based on filters provided
    if params.get('search'):
        # Search query
        search_pattern = format_search_pattern(params['search'])
        variables = build_query_variables(searchTerm=search_pattern, limit=params['limit'])
        query = SEARCH_TEAMS_QUERY
        await ctx.info(f"Searching teams with pattern: {params['search']}")
    elif params.get('conference'):
        # Conference filter
        variables = build_query_variables(conference=params['conference'], limit=params['limit'])
        query = GET_TEAMS_BY_CONFERENCE_QUERY
        await ctx.info(f"Fetching teams from conference: {params['conference']}")
    elif params.get('division'):
        # Division filter
        variables = build_query_variables(division=params['division'], limit=params['limit'])
        query = GET_TEAMS_BY_DIVISION_QUERY
        await ctx.info(f"Fetching teams from division: {params['division']}")
    else:
        # All teams
        variables = build_query_variables(limit=params['limit'])
        query = GET_TEAMS_ALL_QUERY
        await ctx.info(f"Fetching all teams (limit: {params['limit']})")
    
    # Execute the GraphQL query
    result = await execute_graphql(query, variables, ctx)
    
    # Future enhancement: Add additional data based on include_* flags
    # This is where we would enhance the response with records, roster, etc.
    if any([params['include_records'], params['include_roster'], 
            params['include_coaching'], params['include_facilities']]):
        await ctx.info("Enhancement flags detected - future feature")
        # TODO: Implement enhancements using utils functions
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'teams', include_raw_data_bool)

@mcp.tool()
async def GetTeamDetails(
    team_id: Annotated[Optional[Union[str, int]], "Team ID number (optional, can be string or int)"] = None,
    school_name: Annotated[Optional[str], "School name to search for (optional, supports partial matches)"] = None,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data (default: false)"] = False,
    ctx: Context = None
) -> str:
    """
    Get detailed information for a specific team.
    
    Args:
        team_id: Team ID number (optional, can be string or int)
        school_name: School name to search for (optional, supports partial matches)
    
    Returns:
        JSON string with team details (teamId, school, conference, division, etc.)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Note:
        Must provide either team_id or school_name
    """
    # Validate that at least one parameter is provided
    team_id_int = safe_int_conversion(team_id, 'team_id') if team_id else None
    school_name_clean = safe_string_conversion(school_name, 'school_name') if school_name else None
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    validate_team_lookup_params(team_id_int, school_name_clean, None)
    
    # Use different queries based on which parameter is provided
    if team_id_int:
        variables = build_query_variables(teamId=team_id_int)
        result = await execute_graphql(GET_TEAM_DETAILS_QUERY_BY_ID, variables, ctx)
        await ctx.info(f"Fetching team details by ID: {team_id_int}")
    else:
        # Format school name for partial matching
        school_pattern = f"%{school_name_clean}%"
        variables = build_query_variables(school=school_pattern)
        result = await execute_graphql(GET_TEAM_DETAILS_QUERY_BY_NAME, variables, ctx)
        await ctx.info(f"Fetching team details by name: {school_name_clean}")
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'teams', include_raw_data_bool)

@mcp.tool()
async def SearchTeams(
    search_term: Annotated[str, "Text to search for in school names or abbreviations"],
    limit: Annotated[Optional[Union[str, int]], "Maximum number of results to return (default: 20, can be string or int)"] = 20,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data (default: false)"] = False,
    ctx: Context = None
) -> str:
    """
    Search for teams by school name or abbreviation.
    
    Args:
        search_term: Text to search for in school names or abbreviations
        limit: Maximum number of results to return (default: 20, can be string or int)
    
    Returns:
        JSON string with matching teams
        include_raw_data: Include raw GraphQL response data (default: false)
    """
    # Process parameters
    limit_int = safe_int_conversion(limit, 'limit') if limit is not None else 20
    search_pattern = format_search_pattern(search_term)
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    variables = build_query_variables(searchTerm=search_pattern, limit=limit_int)
    result = await execute_graphql(SEARCH_TEAMS_QUERY, variables, ctx)
    
    await ctx.info(f"Searching teams with term: '{search_term}' (limit: {limit_int})")
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'teams', include_raw_data_bool)