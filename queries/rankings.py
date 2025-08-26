"""
Rankings-related GraphQL queries for college football data.
"""

def build_rankings_query(season: int = None, week: int = None, poll_type: str = None, team: str = None, top_n: int = 25) -> tuple[str, dict]:
    """
    Build dynamic rankings query based on provided parameters.
    
    Args:
        season: Season year to filter by
        week: Week number to filter by
        poll_type: Poll type name to filter by (e.g., "AP Top 25")
        team: Team name to search for specific ranking
        top_n: Number of teams to return (default: 25)
        
    Returns:
        Tuple of (query_string, variables_dict)
    """
    # Build parameter definitions and where conditions dynamically
    params = []
    where_conditions = []
    ranking_where_conditions = []
    variables = {}
    
    if season is not None:
        params.append("$season: Int!")
        where_conditions.append("season: { _eq: $season }")
        variables["season"] = season
        
    if week is not None:
        params.append("$week: smallint!")
        where_conditions.append("week: { _eq: $week }")
        variables["week"] = week
        
    if poll_type is not None:
        params.append("$poll_type: String!")
        where_conditions.append("pollType: { name: { _eq: $poll_type } }")
        variables["poll_type"] = poll_type
        
    if team is not None:
        params.append("$team: String!")
        ranking_where_conditions.append("team: { school: { _ilike: $team } }")
        variables["team"] = f"%{team}%"
    
    # Build the where clauses
    where_clause = ""
    if where_conditions:
        where_clause = f"where: {{ {', '.join(where_conditions)} }}"
        
    ranking_where_clause = ""
    if ranking_where_conditions:
        ranking_where_clause = f"where: {{ {', '.join(ranking_where_conditions)} }}"
    
    # Build parameter string
    param_string = ", ".join(params) if params else ""
    
    query = f"""
query GetRankings({param_string}) {{
    poll(
        {where_clause}
        orderBy: {{ week: ASC }}
    ) {{
        season
        seasonType
        week
        pollType {{
            name
            abbreviation
        }}
        rankings(
            {ranking_where_clause}
            orderBy: {{ rank: ASC }}
            limit: {top_n}
        ) {{
            rank
            firstPlaceVotes
            points
            team {{
                teamId
                school
                conference
                abbreviation
            }}
        }}
    }}
}}
""".strip()
    
    return query, variables

