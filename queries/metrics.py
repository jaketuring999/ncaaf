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
        
        # Overall EPA and Success
        epa
        epaAllowed
        success
        successAllowed
        
        # Offensive Metrics
        rushingEpa
        passingEpa
        explosiveness
        lineYards
        secondLevelYards
        openFieldYards
        highlightYards
        standardDownsSuccess
        passingDownsSuccess
        
        # Defensive Metrics (Allowed)
        rushingEpaAllowed
        passingEpaAllowed
        explosivenessAllowed
        lineYardsAllowed
        secondLevelYardsAllowed
        openFieldYardsAllowed
        highlightYardsAllowed
        standardDownsSuccessAllowed
        passingDownsSuccessAllowed
        
        team {
            school
            abbreviation
            conference
        }
    }
}
"""