"""
Schema exploration tool for NCAAF GraphQL API.
Provides intelligent search and exploration of the schema without large introspection queries.
"""

import os
import re
import json
from typing import Optional, Dict, List, Any, Tuple, Union, Annotated
from pathlib import Path

# Import from dedicated mcp module
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from utils.param_utils import safe_int_conversion, safe_bool_conversion


class SchemaParser:
    """Parse and index GraphQL schema from local file"""
    
    def __init__(self, schema_path: str = None):
        if schema_path is None:
            # Default to cfbd-schema.graphql in project root
            schema_path = Path(__file__).parent.parent / "cfbd-schema.graphql"
        
        self.schema_path = schema_path
        self.types = {}
        self.scalars = []
        self.enums = []
        self.query_fields = {}
        self.type_index = {}  # For fast searching
        self._parse_schema()
    
    def _parse_schema(self):
        """Parse the GraphQL schema file"""
        if not os.path.exists(self.schema_path):
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        with open(self.schema_path, 'r') as f:
            content = f.read()
        
        # Parse scalar types
        scalar_pattern = r'scalar\s+(\w+)'
        self.scalars = re.findall(scalar_pattern, content)
        
        # Parse enum types
        enum_pattern = r'enum\s+(\w+)\s*\{'
        self.enums = re.findall(enum_pattern, content)
        
        # Parse type definitions with their content
        type_pattern = r'"""([^"]*?)"""\s*type\s+(\w+)\s*\{([^}]+)\}'
        type_matches = re.finditer(type_pattern, content, re.DOTALL)
        
        # Also match types without descriptions
        type_no_desc_pattern = r'type\s+(\w+)\s*\{([^}]+)\}'
        type_no_desc_matches = re.finditer(type_no_desc_pattern, content, re.DOTALL)
        
        # Process types with descriptions
        for match in type_matches:
            description = match.group(1).strip()
            type_name = match.group(2)
            fields_content = match.group(3)
            
            self.types[type_name] = {
                'name': type_name,
                'kind': self._determine_kind(type_name),
                'description': description,
                'fields': self._parse_fields(fields_content),
                'is_aggregate': self._is_aggregate_type(type_name)
            }
            
            # Build search index
            self._index_type(type_name, description)
        
        # Process types without descriptions
        for match in type_no_desc_matches:
            type_name = match.group(1)
            if type_name not in self.types:  # Don't overwrite if already parsed with description
                fields_content = match.group(2)
                
                self.types[type_name] = {
                    'name': type_name,
                    'kind': self._determine_kind(type_name),
                    'description': '',
                    'fields': self._parse_fields(fields_content),
                    'is_aggregate': self._is_aggregate_type(type_name)
                }
                
                self._index_type(type_name, '')
        
        # Parse query_root separately
        query_root_pattern = r'type\s+query_root\s*\{([^}]+)\}'
        query_match = re.search(query_root_pattern, content, re.DOTALL)
        if query_match:
            self.query_fields = self._parse_query_fields(query_match.group(1))
    
    def _determine_kind(self, type_name: str) -> str:
        """Determine the GraphQL kind of a type"""
        if type_name in self.scalars:
            return 'SCALAR'
        elif type_name in self.enums:
            return 'ENUM'
        elif 'Input' in type_name or 'BoolExp' in type_name or 'OrderBy' in type_name:
            return 'INPUT_OBJECT'
        else:
            return 'OBJECT'
    
    def _is_aggregate_type(self, type_name: str) -> bool:
        """Check if type is an aggregate helper type"""
        aggregate_patterns = [
            'Aggregate', 'Fields', 'Avg', 'Max', 'Min',
            'Stddev', 'Sum', 'Var', 'Pop', 'Samp'
        ]
        return any(pattern in type_name for pattern in aggregate_patterns)
    
    def _parse_fields(self, fields_content: str) -> List[Dict]:
        """Parse fields from type content"""
        fields = []
        # Simple field parsing - can be enhanced
        field_pattern = r'(\w+)(?:\([^)]*\))?\s*:\s*([^!\n]+)(!)?'
        for match in re.finditer(field_pattern, fields_content):
            field_name = match.group(1)
            field_type = match.group(2).strip()
            is_required = bool(match.group(3))
            
            fields.append({
                'name': field_name,
                'type': field_type,
                'required': is_required
            })
        
        return fields
    
    def _parse_query_fields(self, query_content: str) -> Dict:
        """Parse query root fields"""
        fields = {}
        # Parse query fields with their descriptions
        field_pattern = r'"([^"]+)"\s+(\w+)\s*\([^)]*\)\s*:\s*([^!\n]+)'
        for match in re.finditer(field_pattern, query_content):
            description = match.group(1)
            field_name = match.group(2)
            return_type = match.group(3).strip()
            
            fields[field_name] = {
                'name': field_name,
                'description': description,
                'type': return_type
            }
        
        return fields
    
    def _index_type(self, type_name: str, description: str):
        """Build search index for a type"""
        # Index by lowercase for case-insensitive search
        key = type_name.lower()
        if key not in self.type_index:
            self.type_index[key] = []
        self.type_index[key].append(type_name)
        
        # Also index by words in description
        if description:
            words = re.findall(r'\w+', description.lower())
            for word in words:
                if len(word) > 2:  # Skip very short words
                    if word not in self.type_index:
                        self.type_index[word] = []
                    if type_name not in self.type_index[word]:
                        self.type_index[word].append(type_name)
    
    def search(self, query: str, use_regex: bool = False, exclude_aggregates: bool = False) -> List[Dict]:
        """Search for types matching query - case insensitive and smart matching"""
        results = []
        seen = set()
        
        if use_regex:
            # Regex search
            pattern = re.compile(query, re.IGNORECASE)
            for type_name, type_info in self.types.items():
                if pattern.search(type_name) or pattern.search(type_info.get('description', '')):
                    if type_name not in seen:
                        # Apply aggregate filter
                        if not exclude_aggregates or not type_info['is_aggregate']:
                            results.append(type_info)
                            seen.add(type_name)
        else:
            # Simple search - case insensitive
            query_lower = query.lower()
            
            # Smart matching patterns:
            # 1. Exact match (case insensitive)
            # 2. Prefix match (e.g., "Game" matches "GameLines", "GameMedia")
            # 3. Contains match (e.g., "team" matches "TeamTalent", "GameTeam")
            # 4. Word boundary match (e.g., "Game" matches "game" but also "GameTeam")
            
            for type_name, type_info in self.types.items():
                type_lower = type_name.lower()
                matched = False
                
                # Check various matching patterns
                if type_lower == query_lower:
                    # Exact match (highest priority)
                    matched = True
                elif type_lower.startswith(query_lower):
                    # Prefix match
                    matched = True
                elif query_lower in type_lower:
                    # Contains match
                    matched = True
                else:
                    # Check for word boundary match (camelCase aware)
                    # Split on capital letters for camelCase
                    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', type_name)
                    for word in words:
                        if word.lower() == query_lower:
                            matched = True
                            break
                
                if matched and type_name not in seen:
                    # Apply aggregate filter
                    if not exclude_aggregates or not type_info['is_aggregate']:
                        results.append(type_info)
                        seen.add(type_name)
            
            # Also search in description index
            if query_lower in self.type_index:
                for type_name in self.type_index[query_lower]:
                    if type_name not in seen:
                        type_info = self.types[type_name]
                        # Apply aggregate filter
                        if not exclude_aggregates or not type_info['is_aggregate']:
                            results.append(type_info)
                            seen.add(type_name)
        
        # Sort results by relevance (exact matches first, then prefix, then contains)
        def sort_key(item):
            name_lower = item['name'].lower()
            if name_lower == query_lower:
                return (0, item['name'])  # Exact match
            elif name_lower.startswith(query_lower):
                return (1, item['name'])  # Prefix match
            else:
                return (2, item['name'])  # Contains match
        
        results.sort(key=sort_key)
        return results
    
    def get_types(self, kind: Optional[str] = None, exclude_aggregates: bool = True) -> List[Dict]:
        """Get types filtered by kind"""
        results = []
        
        for type_name, type_info in self.types.items():
            # Apply filters
            if kind and type_info['kind'] != kind.upper():
                continue
            if exclude_aggregates and type_info['is_aggregate']:
                continue
            
            results.append(type_info)
        
        return sorted(results, key=lambda x: x['name'])
    
    def get_type_details(self, type_name: str) -> Optional[Dict]:
        """Get detailed information about a specific type"""
        # Try exact match first
        if type_name in self.types:
            return self.types[type_name]
        
        # Try case-insensitive match
        for name, info in self.types.items():
            if name.lower() == type_name.lower():
                return info
        
        return None
    
    def get_stats(self) -> Dict:
        """Get schema statistics"""
        stats = {
            'total_types': len(self.types),
            'scalars': len(self.scalars),
            'enums': len(self.enums),
            'query_fields': len(self.query_fields),
            'by_kind': {},
            'main_entities': 0,
            'aggregate_types': 0
        }
        
        # Count by kind
        for type_info in self.types.values():
            kind = type_info['kind']
            stats['by_kind'][kind] = stats['by_kind'].get(kind, 0) + 1
            
            if type_info['is_aggregate']:
                stats['aggregate_types'] += 1
            else:
                stats['main_entities'] += 1
        
        return stats


# Global schema parser instance
_schema_parser = None

def get_schema_parser() -> SchemaParser:
    """Get or create the global schema parser instance"""
    global _schema_parser
    if _schema_parser is None:
        _schema_parser = SchemaParser()
    return _schema_parser


@mcp.tool()
async def SchemaExplorer(
    operation: Annotated[str, "Operation to perform - 'search', 'types', 'fields', 'details', 'stats'"],
    query: Annotated[Optional[str], "Search query or type name (for search/details operations)"] = None,
    kind: Annotated[Optional[str], "Filter by type kind - OBJECT, SCALAR, ENUM, INPUT_OBJECT (for types operation)"] = None,
    limit: Annotated[Optional[Union[str, int]], "Maximum results to return"] = 25,
    offset: Annotated[Optional[Union[str, int]], "Pagination offset"] = 0,
    include_fields: Annotated[Union[str, bool], "Include field details in results"] = False,
    exclude_aggregates: Annotated[Union[str, bool], "Exclude aggregate helper types"] = True,
    use_regex: Annotated[Union[str, bool], "Use regex for search operation"] = False
) -> str:
    """
    Unified schema exploration tool for NCAAF GraphQL API.
    
    Args:
        operation: Operation to perform - "search", "types", "fields", "details", "stats"
        query: Search query or type name (for search/details operations)
        kind: Filter by type kind - OBJECT, SCALAR, ENUM, INPUT_OBJECT (for types operation)
        limit: Maximum results to return (default: 25)
        offset: Pagination offset (default: 0)
        include_fields: Include field details in results
        exclude_aggregates: Exclude aggregate helper types (default: True)
        use_regex: Use regex for search operation (default: False)
    
    Returns:
        JSON string with operation results
    
    Examples:
        - Search for game types: operation="search", query="game"
        - Get all object types: operation="types", kind="OBJECT"
        - Get type details: operation="details", query="Game"
        - Get schema stats: operation="stats"
        - List query fields: operation="fields"
    """
    try:
        # Convert string parameters to appropriate types
        limit = safe_int_conversion(limit, 'limit') if limit is not None else 25
        offset = safe_int_conversion(offset, 'offset') if offset is not None else 0
        include_fields = safe_bool_conversion(include_fields, 'include_fields')
        exclude_aggregates = safe_bool_conversion(exclude_aggregates, 'exclude_aggregates')
        use_regex = safe_bool_conversion(use_regex, 'use_regex')
        
        parser = get_schema_parser()
        
        if operation == "search":
            if not query:
                return json.dumps({"error": "Query parameter required for search operation"})
            
            pass  # Schema search
            
            results = parser.search(query, use_regex, exclude_aggregates)
            
            # Apply pagination
            total = len(results)
            start = offset
            end = min(start + limit, total)
            paginated = results[start:end]
            
            # Format results
            if not include_fields:
                # Simplified output without fields
                paginated = [
                    {
                        'name': t['name'],
                        'kind': t['kind'],
                        'description': t['description'][:100] if t['description'] else '',
                        'field_count': len(t['fields']),
                        'is_aggregate': t['is_aggregate']
                    }
                    for t in paginated
                ]
            
            return json.dumps({
                'operation': 'search',
                'query': query,
                'results': paginated,
                'pagination': {
                    'total': total,
                    'returned': len(paginated),
                    'limit': limit,
                    'offset': offset,
                    'has_more': end < total
                }
            }, indent=2)
        
        elif operation == "types":
            pass  # Getting types
            
            results = parser.get_types(kind, exclude_aggregates)
            
            # Apply pagination
            total = len(results)
            start = offset
            end = min(start + limit, total)
            paginated = results[start:end]
            
            # Format results
            if not include_fields:
                paginated = [
                    {
                        'name': t['name'],
                        'kind': t['kind'],
                        'description': t['description'][:100] if t['description'] else '',
                        'field_count': len(t['fields'])
                    }
                    for t in paginated
                ]
            
            return json.dumps({
                'operation': 'types',
                'filter': {'kind': kind, 'exclude_aggregates': exclude_aggregates},
                'results': paginated,
                'pagination': {
                    'total': total,
                    'returned': len(paginated),
                    'limit': limit,
                    'offset': offset,
                    'has_more': end < total
                }
            }, indent=2)
        
        elif operation == "fields":
            pass  # Getting query fields
            
            fields = list(parser.query_fields.values())
            
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                fields = [f for f in fields if query_lower in f['name'].lower()]
            
            # Apply pagination
            total = len(fields)
            start = offset
            end = min(start + limit, total)
            paginated = fields[start:end]
            
            return json.dumps({
                'operation': 'fields',
                'results': paginated,
                'pagination': {
                    'total': total,
                    'returned': len(paginated),
                    'limit': limit,
                    'offset': offset,
                    'has_more': end < total
                }
            }, indent=2)
        
        elif operation == "details":
            if not query:
                return json.dumps({"error": "Query parameter (type name) required for details operation"})
            
            pass  # Getting type details
            
            type_info = parser.get_type_details(query)
            
            if not type_info:
                return json.dumps({"error": f"Type '{query}' not found"})
            
            return json.dumps({
                'operation': 'details',
                'type': type_info
            }, indent=2)
        
        elif operation == "stats":
            pass  # Getting schema stats
            
            stats = parser.get_stats()
            
            return json.dumps({
                'operation': 'stats',
                'statistics': stats
            }, indent=2)
        
        else:
            return json.dumps({
                "error": f"Unknown operation: {operation}",
                "valid_operations": ["search", "types", "fields", "details", "stats"]
            })
    
    except Exception as e:
        pass  # Error handling
        return json.dumps({"error": str(e)})


