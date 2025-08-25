"""
Team-related MCP tools for college football data.
"""

from typing import Optional, Union, Annotated
from fastmcp import Context

# Import from dedicated mcp module to avoid circular imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.mcp_server import mcp
from src.graphql_executor import execute_graphql, build_query_variables
from src.param_processor import safe_int_conversion

# GraphQL queries defined as Python strings
GET_TEAMS_SIMPLE_QUERY = """
query GetTeamsSimple($limit: Int) {
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

@mcp.tool()
async def GetTeamsSimple(
    limit: Annotated[Optional[Union[str, int]], "Maximum number of teams to return (default: 50, can be string or int)"] = 50,
    ctx: Context = None
) -> str:
    """
    Get basic information for all current college football teams.
    
    Args:
        limit: Maximum number of teams to return (default: 50, can be string or int)
    
    Returns:
        JSON string with team information including teamId, school, conference, etc.
    """
    # Convert string input to integer
    if limit is None:
        variables = {}
    else:
        limit_int = safe_int_conversion(limit, 'limit')
        variables = build_query_variables(limit=limit_int)
    return await execute_graphql(GET_TEAMS_SIMPLE_QUERY, variables, ctx)

@mcp.tool()
async def GetTeamsByConference(
    conference: Annotated[str, "Conference name (e.g., 'ACC', 'SEC', 'Big 12')"],
    limit: Annotated[Optional[Union[str, int]], "Maximum number of teams to return (default: 30, can be string or int)"] = 30,
    ctx: Context = None
) -> str:
    """
    Get all teams in a specific conference.
    
    Args:
        conference: Conference name (e.g., "ACC", "SEC", "Big 12")
        limit: Maximum number of teams to return (default: 30, can be string or int)
    
    Returns:
        JSON string with team information for the specified conference
    """
    # Convert string input to integer
    limit_int = safe_int_conversion(limit, 'limit') if limit is not None else None
    variables = build_query_variables(conference=conference, limit=limit_int)
    return await execute_graphql(GET_TEAMS_BY_CONFERENCE_QUERY, variables, ctx)

@mcp.tool()
async def GetTeamDetails(
    team_id: Annotated[Optional[Union[str, int]], "Team ID number (optional, can be string or int)"] = None,
    school_name: Annotated[Optional[str], "School name to search for (optional, supports partial matches)"] = None,
    ctx: Context = None
) -> str:
    """
    Get information for a specific team.
    
    Args:
        team_id: Team ID number (optional, can be string or int)
        school_name: School name to search for (optional, supports partial matches)
    
    Returns:
        JSON string with team details (teamId, school, conference, division, etc.)
    
    Note:
        Must provide either team_id or school_name
    """
    if not team_id and not school_name:
        return '{"error": "Must provide either team_id or school_name"}'
    
    # Use different queries based on which parameter is provided
    if team_id:
        team_id_int = safe_int_conversion(team_id, 'team_id')
        variables = build_query_variables(teamId=team_id_int)
        return await execute_graphql(GET_TEAM_DETAILS_QUERY_BY_ID, variables, ctx)
    else:
        variables = build_query_variables(school=f"%{school_name}%")
        return await execute_graphql(GET_TEAM_DETAILS_QUERY_BY_NAME, variables, ctx)

@mcp.tool()
async def SearchTeams(
    search_term: Annotated[str, "Text to search for in school names or abbreviations"],
    limit: Annotated[Optional[Union[str, int]], "Maximum number of results to return (default: 20, can be string or int)"] = 20,
    ctx: Context = None
) -> str:
    """
    Search for teams by school name or abbreviation.
    
    Args:
        search_term: Text to search for in school names or abbreviations
        limit: Maximum number of results to return (default: 20, can be string or int)
    
    Returns:
        JSON string with matching teams
    """
    # Convert string input to integer
    limit_int = safe_int_conversion(limit, 'limit') if limit is not None else 20
    # Add wildcards for partial matching
    search_pattern = f"%{search_term}%"
    variables = build_query_variables(searchTerm=search_pattern, limit=limit_int)
    return await execute_graphql(SEARCH_TEAMS_QUERY, variables, ctx)