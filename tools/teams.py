"""
Team-related MCP tools for college football data.
"""

from typing import Optional
from fastmcp import Context

# Import from dedicated mcp module to avoid circular imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.mcp_server import mcp
from src.graphql_executor import execute_graphql, build_query_variables

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
        city
        state
        abbreviation
        altName1
        altName2
    }
}
"""

GET_TEAM_DETAILS_QUERY = """
query GetTeamDetails($teamId: Int, $school: String) {
    currentTeams(
        where: {
            _or: [
                { teamId: { _eq: $teamId } }
                { school: { _ilike: $school } }
            ]
        }
    ) {
        teamId
        school
        conference
        conferenceId
        division
        classification
        city
        state
        zip
        country
        abbreviation
        altName1
        altName2
        primaryColor
        secondaryColor
        website
        twitter
        logos
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
                { altName1: { _ilike: $searchTerm } }
                { altName2: { _ilike: $searchTerm } }
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
        altName1
        altName2
    }
}
"""

@mcp.tool()
async def GetTeamsSimple(
    limit: Optional[int] = None,
    ctx: Context = None
) -> str:
    """
    Get basic information for all current college football teams.
    
    Args:
        limit: Maximum number of teams to return (optional)
    
    Returns:
        JSON string with team information including teamId, school, conference, etc.
    """
    variables = build_query_variables(limit=limit)
    return await execute_graphql(GET_TEAMS_SIMPLE_QUERY, variables, ctx)

@mcp.tool()
async def GetTeamsByConference(
    conference: str,
    limit: Optional[int] = None,
    ctx: Context = None
) -> str:
    """
    Get all teams in a specific conference.
    
    Args:
        conference: Conference name (e.g., "ACC", "SEC", "Big 12")
        limit: Maximum number of teams to return (optional)
    
    Returns:
        JSON string with detailed team information for the specified conference
    """
    variables = build_query_variables(conference=conference, limit=limit)
    return await execute_graphql(GET_TEAMS_BY_CONFERENCE_QUERY, variables, ctx)

@mcp.tool()
async def GetTeamDetails(
    team_id: Optional[int] = None,
    school_name: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    Get detailed information for a specific team.
    
    Args:
        team_id: Team ID number (optional)
        school_name: School name to search for (optional, supports partial matches)
    
    Returns:
        JSON string with comprehensive team details including colors, logos, contact info
    
    Note:
        Must provide either team_id or school_name
    """
    if not team_id and not school_name:
        return '{"error": "Must provide either team_id or school_name"}'
    
    variables = build_query_variables(
        teamId=team_id,
        school=f"%{school_name}%" if school_name else None
    )
    return await execute_graphql(GET_TEAM_DETAILS_QUERY, variables, ctx)

@mcp.tool()
async def SearchTeams(
    search_term: str,
    limit: Optional[int] = 20,
    ctx: Context = None
) -> str:
    """
    Search for teams by name, abbreviation, or alternate names.
    
    Args:
        search_term: Text to search for in team names
        limit: Maximum number of results to return (default: 20)
    
    Returns:
        JSON string with matching teams
    """
    # Add wildcards for partial matching
    search_pattern = f"%{search_term}%"
    variables = build_query_variables(searchTerm=search_pattern, limit=limit)
    return await execute_graphql(SEARCH_TEAMS_QUERY, variables, ctx)