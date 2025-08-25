"""
Security validation for GraphQL queries in the NCAAF MCP Server.
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SecurityValidator:
    """GraphQL security validation"""
    
    # Patterns that could be potentially dangerous or should be logged
    DANGEROUS_PATTERNS = [
        r'__schema',      # Introspection (allowed but logged)
        r'__type',        # Introspection (allowed but logged)
        r'mutation.*delete',  # Dangerous mutations
        r'subscription'   # Subscriptions might not be supported
    ]
    
    # Security limits
    MAX_QUERY_DEPTH = 10
    MAX_QUERY_LENGTH = 5000
    MAX_ALIASES = 50
    
    @staticmethod
    def validate_query(query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate query for security issues.
        
        Args:
            query: The GraphQL query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check query length
        if len(query) > SecurityValidator.MAX_QUERY_LENGTH:
            return False, f"Query too long: {len(query)} characters (max {SecurityValidator.MAX_QUERY_LENGTH})"
        
        # Check for empty query
        if not query.strip():
            return False, "Query cannot be empty"
        
        # Check for basic GraphQL structure
        if '{' not in query or '}' not in query:
            return False, "Query appears to be malformed (missing braces)"
        
        # Check for balanced braces
        brace_diff = query.count('{') - query.count('}')
        if brace_diff != 0:
            return False, f"Unbalanced braces (difference: {brace_diff})"
        
        # Check nesting depth
        max_depth = SecurityValidator._calculate_query_depth(query)
        if max_depth > SecurityValidator.MAX_QUERY_DEPTH:
            return False, f"Query nesting too deep: {max_depth} levels (max {SecurityValidator.MAX_QUERY_DEPTH})"
        
        # Check for alias abuse
        alias_count = SecurityValidator._count_aliases(query)
        if alias_count > SecurityValidator.MAX_ALIASES:
            return False, f"Too many aliases: {alias_count} (max {SecurityValidator.MAX_ALIASES})"
        
        # Check for dangerous patterns
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                if pattern in [r'__schema', r'__type']:
                    # Allow introspection but log it
                    logger.info(f"Introspection query detected: {pattern}")
                    continue
                else:
                    return False, f"Potentially dangerous query pattern: {pattern}"
        
        # Check for potential DOS patterns
        if SecurityValidator._has_potential_dos_patterns(query):
            return False, "Query contains potential DoS patterns"
        
        return True, None
    
    @staticmethod
    def _calculate_query_depth(query: str) -> int:
        """Calculate the maximum nesting depth of a GraphQL query"""
        max_depth = 0
        current_depth = 0
        
        for char in query:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth -= 1
        
        return max_depth
    
    @staticmethod
    def _count_aliases(query: str) -> int:
        """Count the number of field aliases in a query"""
        # Simple regex to find aliases (field_name: actual_field)
        alias_pattern = r'\w+\s*:\s*\w+'
        matches = re.findall(alias_pattern, query)
        return len(matches)
    
    @staticmethod
    def _has_potential_dos_patterns(query: str) -> bool:
        """Check for patterns that could cause denial of service"""
        # Check for excessive repetition of the same field
        words = re.findall(r'\w+', query.lower())
        word_counts = {}
        
        for word in words:
            if len(word) > 2:  # Only check meaningful words
                word_counts[word] = word_counts.get(word, 0) + 1
                
                # If any word appears too many times, it might be abusive
                if word_counts[word] > 20:  # Reasonable threshold
                    logger.warning(f"Potential DoS pattern: '{word}' appears {word_counts[word]} times")
                    return True
        
        return False
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        Basic query sanitization (removes comments and normalizes whitespace).
        
        Args:
            query: The GraphQL query to sanitize
            
        Returns:
            Sanitized query string
        """
        # Remove GraphQL comments
        lines = query.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove comments (# at start of line or after whitespace)
            comment_pos = line.find('#')
            if comment_pos != -1:
                # Check if # is inside a string literal
                before_comment = line[:comment_pos]
                quote_count = before_comment.count('"') - before_comment.count('\\"')
                if quote_count % 2 == 0:  # Even number of quotes means # is outside string
                    line = line[:comment_pos]
            
            cleaned_lines.append(line)
        
        # Join lines and normalize whitespace
        sanitized = ' '.join(cleaned_lines)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized