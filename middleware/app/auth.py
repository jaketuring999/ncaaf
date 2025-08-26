"""
Authentication middleware for NCAAF API
"""

import secrets
from typing import Optional
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .config import settings


security = HTTPBasic(auto_error=False)


class AuthenticationError(HTTPException):
    """Authentication error exception"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Basic"}
        )


def verify_credentials(username: str, password: str) -> bool:
    """Verify username and password using constant-time comparison"""
    if not settings.auth_username or not settings.auth_password:
        return True  # No credentials configured, allow access
    
    # Constant-time comparison to prevent timing attacks
    correct_username = secrets.compare_digest(username, settings.auth_username)
    correct_password = secrets.compare_digest(password, settings.auth_password)
    
    return correct_username and correct_password


def get_current_user(
    credentials: Optional[HTTPBasicCredentials] = Security(security)
) -> str:
    """Extract and validate username/password from Authorization header"""
    
    # If authentication is disabled, allow access
    if not settings.require_auth:
        return "anonymous"
    
    # If no credentials provided and auth is required
    if not credentials:
        raise AuthenticationError("Missing credentials in Authorization header")
    
    # Verify the credentials
    if not verify_credentials(credentials.username, credentials.password):
        raise AuthenticationError("Invalid username or password")
    
    return credentials.username


# Optional authentication dependency (for endpoints that can work without auth)
def optional_auth(
    credentials: Optional[HTTPBasicCredentials] = Security(security)
) -> Optional[str]:
    """Optional authentication - allows both authenticated and anonymous access"""
    
    if not credentials:
        return "anonymous"
    
    try:
        return get_current_user(credentials)
    except AuthenticationError:
        return "anonymous"