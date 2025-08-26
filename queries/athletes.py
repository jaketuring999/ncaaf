"""
Athlete/Player-related GraphQL queries for college football data.
"""

GET_ATHLETES_QUERY = """
query GetAthletes($teamId: Int, $season: smallint) {
    athlete(
        where: {
            athleteTeams: {
                teamId: { _eq: $teamId }
                startYear: { _lte: $season }
                endYear: { _gte: $season }
            }
        }
        limit: 100
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
        
        athleteTeams {
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