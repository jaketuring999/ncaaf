"""
Advanced metrics GraphQL queries for college football data.
"""

GET_ADVANCED_METRICS_QUERY = """
query GetAdvancedMetrics($teamId: Int, $season: smallint) {
    adjustedTeamMetrics(
        where: {
            teamId: { _eq: $teamId }
            year: { _eq: $season }
        }
    ) {
        teamId
        year
        epa
        epaAllowed
        explosiveness
        success
        team {
            school
        }
    }
}
"""