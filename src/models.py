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


class ServerConfig(BaseModel):
    """Server configuration with validation"""
    endpoint: str = Field(..., description="GraphQL endpoint URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    cache_ttl: int = Field(300, description="Cache TTL in seconds")
    rate_limit: int = Field(100, description="Requests per minute limit")
    
    @field_validator('endpoint')
    @classmethod
    def validate_endpoint(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Endpoint must be a valid HTTP/HTTPS URL')
        return v
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        if v <= 0 or v > 300:
            raise ValueError('Timeout must be between 1 and 300 seconds')
        return v


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