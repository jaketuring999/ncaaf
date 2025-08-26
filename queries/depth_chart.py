"""
Depth Chart GraphQL queries for college football data.
"""

GET_DEPTH_CHART_QUERY = """
query GetDepthChart($teamId: Int, $season: smallint) {
    athlete(
        where: {
            athleteTeams: {
                teamId: { _eq: $teamId }
                startYear: { _lte: $season }
                endYear: { _gte: $season }
            }
        }
        limit: 150
    ) {
        id
        name
        firstName
        lastName
        weight
        height
        jersey
        positionId
        teamId
        
        athleteTeams(
            where: {
                teamId: { _eq: $teamId }
                startYear: { _lte: $season }
                endYear: { _gte: $season }
            }
        ) {
            teamId
            startYear
            endYear
            team {
                school
                abbreviation
                conference
            }
        }
        
        position {
            name
            abbreviation
        }
    }
}
"""