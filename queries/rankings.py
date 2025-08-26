"""
Rankings-related GraphQL queries for college football data.
"""

GET_RANKINGS_QUERY = """
query GetRankings($season: Int, $week: smallint) {
    poll(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
        }
        orderBy: { week: ASC }
    ) {
        season
        seasonType
        week
        pollType {
            name
            abbreviation
        }
        rankings(
            orderBy: { rank: ASC }
        ) {
            rank
            firstPlaceVotes
            points
            team {
                teamId
                school
                conference
                abbreviation
            }
        }
    }
}
"""