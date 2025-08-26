"""
Team resolution utilities for NCAAF MCP tools.

Provides simple, query-time resolution of team names/abbreviations to team IDs
using the existing GraphQL infrastructure.
"""

import json
import logging
from typing import Optional

# Import from dedicated module to avoid circular imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.graphql_executor import execute_graphql

logger = logging.getLogger(__name__)

# GraphQL query for team resolution
TEAM_RESOLUTION_QUERY = """
query GetTeamByName($search: String!) {
    currentTeams(
        where: {
            _or: [
                { school: { _ilike: $search } }
                { abbreviation: { _ilike: $search } }
            ]
        }
        orderBy: { school: ASC }
        limit: 3
    ) {
        teamId
        school
        abbreviation
        conference
    }
}
"""


async def resolve_team_id(team_identifier: str) -> int:
    """
    Convert team name, abbreviation, or ID string to integer team ID.
    
    This function provides simple, query-time resolution using the existing
    GraphQL schema. It handles:
    - Numeric IDs: "333" -> 333
    - School names: "Alabama" -> 333
    - Abbreviations: "BAMA" -> 333
    - Partial matches: "Alab" -> 333
    
    Args:
        team_identifier: Team name, abbreviation, or ID as string
        
    Returns:
        Integer team ID
        
    Raises:
        ValueError: If team cannot be found or identifier is invalid
        
    Examples:
        >>> await resolve_team_id("Alabama")
        333
        >>> await resolve_team_id("BAMA") 
        333
        >>> await resolve_team_id("333")
        333
    """
    if not team_identifier or not isinstance(team_identifier, str):
        raise ValueError("Team identifier must be a non-empty string")
    
    # Clean the identifier
    team_identifier = team_identifier.strip()
    
    # Handle numeric IDs - just validate and convert
    if team_identifier.isdigit():
        team_id = int(team_identifier)
        if team_id <= 0:
            raise ValueError(f"Invalid team ID: {team_id}")
        return team_id
    
    # Search for team by name/abbreviation using GraphQL
    try:
        search_pattern = f"%{team_identifier}%"
        result = await execute_graphql(TEAM_RESOLUTION_QUERY, {"search": search_pattern})
        
        # Parse the result
        result_data = json.loads(result)
        teams = result_data.get('data', {}).get('currentTeams', [])
        
        if not teams:
            raise ValueError(f"No teams found matching '{team_identifier}'")
        
        # If multiple matches, prefer exact matches
        exact_matches = []
        for team in teams:
            school_name = (team.get('school') or '').lower()
            abbreviation = (team.get('abbreviation') or '').lower()
            team_identifier_lower = team_identifier.lower()
            
            if (school_name == team_identifier_lower or abbreviation == team_identifier_lower):
                exact_matches.append(team)
        
        # Use exact match if found, otherwise first result
        best_match = exact_matches[0] if exact_matches else teams[0]
        
        logger.info(f"Resolved '{team_identifier}' to {best_match['school']} (ID: {best_match['teamId']})")
        return best_match['teamId']
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse team search results: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to resolve team '{team_identifier}': {str(e)}")


async def resolve_optional_team_id(team_identifier: Optional[str]) -> Optional[int]:
    """
    Resolve team identifier to ID, handling None values.
    
    Args:
        team_identifier: Optional team name, abbreviation, or ID
        
    Returns:
        Integer team ID or None if identifier was None
        
    Raises:
        ValueError: If identifier is provided but invalid
    """
    if team_identifier is None:
        return None
    
    return await resolve_team_id(team_identifier)