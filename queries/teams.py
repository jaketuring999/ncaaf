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

GET_TEAM_RATINGS_QUERY = """
query GetTeamRatings($teamId: Int, $season: smallint) {
    ratings(
        where: {
            _and: [
                { teamId: { _eq: $teamId } }
                { year: { _eq: $season } }
            ]
        }
    ) {
        teamId
        year
        team
        conference
        
        # ELO Rating
        elo
        
        # FPI Ratings
        fpi
        fpiOffensiveEfficiency
        fpiDefensiveEfficiency
        fpiSpecialTeamsEfficiency
        fpiOverallEfficiency
        fpiSosRank
        fpiRemainingSosRank
        fpiGameControlRank
        fpiResumeRank
        fpiStrengthOfRecordRank
        fpiAvgWinProbabilityRank
        
        # SP+ Ratings
        spOverall
        spOffense
        spDefense
        spSpecialTeams
        
        # SRS Rating
        srs
    }
}
"""

GET_TEAM_TALENT_QUERY = """
query GetTeamTalent($teamId: Int, $season: smallint) {
    teamTalent(
        where: {
            _and: [
                { team: { teamId: { _eq: $teamId } } }
                { year: { _eq: $season } }
            ]
        }
    ) {
        year
        talent
        team {
            teamId
            school
            conference
        }
    }
}
"""

GET_TEAM_WITH_RATINGS_QUERY = """
query GetTeamWithRatings($teamId: Int!, $season: smallint!) {
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
        
        # Team Ratings
        ratings(where: { year: { _eq: $season } }) {
            year
            elo
            fpi
            fpiOffensiveEfficiency
            fpiDefensiveEfficiency
            fpiSpecialTeamsEfficiency
            spOverall
            spOffense
            spDefense
            spSpecialTeams
            srs
        }
        
        # Team Talent
        talent(where: { year: { _eq: $season } }) {
            year
            talent
        }
    }
}
"""