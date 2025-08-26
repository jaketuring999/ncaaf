"""
Configuration for NCAAF MCP API Middleware
"""

import os
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    api_title: str = "NCAAF Analytics API"
    api_description: str = "College Football Analytics API powered by FastMCP"
    api_version: str = "1.0.0"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8346
    debug: bool = False
    
    # Authentication
    auth_username: str = ""
    auth_password: str = ""
    require_auth: bool = True
    
    # MCP Server Configuration
    mcp_server_url: str = "http://localhost:8345/mcp"
    mcp_server_timeout: int = 60
    
    # OpenAI Configuration
    openai_model: str = "gpt-5-mini"
    
    # Performance Settings
    max_concurrent_requests: int = 100
    request_timeout: int = 300
    
    # Logging Settings
    logging_enabled: bool = True
    logging_timeout_ms: int = 1000
    
    class Config:
        env_file = ".env"
        env_prefix = "NCAAF_API_"


class SystemPromptLoader:
    """Load system prompt for NCAAF analytics agent"""
    
    @staticmethod
    def load_prompt() -> str:
        """Load system prompt from file or return default"""
        prompt_paths = [
            "./prompts/ncaaf-systemprompt-v1.md",
            "../prompts/ncaaf-systemprompt-v1.md",
            "/Users/Jake/PycharmProjects/mcp-spider/prompts/ncaaf-systemprompt-v1.md"
        ]
        
        for path in prompt_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception:
                    continue
        
        # Fallback system prompt
        return """You are an NCAAF analytics assistant with access to comprehensive college football data.
        
You have access to tools that can:
- Query NCAAF statistics, team performance, and player data
- Analyze betting odds and outcomes for college football
- Search for specific teams, players, games, and conferences
- Provide comprehensive college football insights and analysis
- Execute GraphQL queries against the college football database

Always provide accurate, data-driven insights based on the available information.
Focus on college football context including conferences, rankings, recruiting, and playoff implications.
Be concise and focus on the specific question asked."""


# Global settings instance
settings = Settings()