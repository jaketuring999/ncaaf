"""
Team-related GraphQL queries for college football data.
"""

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