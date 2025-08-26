"""
Search and discovery GraphQL queries for college football data.
"""

SEARCH_ENTITIES_QUERY = """
query SearchEntities($searchTerm: String!) {
    currentTeams(
        where: {
            school: { _ilike: $searchTerm }
        }
        limit: 10
    ) {
        teamId
        school
        conference
    }
}
"""