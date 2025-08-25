"""
Data models and configuration classes for the NCAAF GraphQL MCP Server.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ValidationError, Field, field_validator


class GraphQLError(Exception):
    """Custom GraphQL error with context"""
    def __init__(self, message: str, query: str = None, status_code: int = None):
        super().__init__(message)
        self.query = query
        self.status_code = status_code

class QueryInput(BaseModel):
    """GraphQL query input validation"""
    query: str = Field(..., min_length=1, description="GraphQL query string")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Query variables")
    operation_name: Optional[str] = Field(None, description="Operation name")


class SchemaField(BaseModel):
    """GraphQL schema field representation"""
    name: str
    type: str
    description: Optional[str] = None
    args: List[Dict[str, Any]] = Field(default_factory=list)


class SchemaType(BaseModel):
    """GraphQL schema type representation"""
    name: str
    kind: str
    description: Optional[str] = None
    fields: List[SchemaField] = Field(default_factory=list)