"""
NCAAF Query API endpoints
"""

import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ..auth import get_current_user
from ..services.streaming_service import streaming_service, QueryRequest


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["NCAAF Analytics"])


@router.post("/query/stream")
async def stream_query(
    query_request: QueryRequest,
    http_request: Request,
    user: str = Depends(get_current_user)
) -> StreamingResponse:
    """
    Process NCAAF analytics query and stream results
    
    - **query**: Natural language query about NCAAF data
    - **previous_response_id**: Optional conversation ID for context
    
    Returns Server-Sent Events stream with query results
    """
    
    logger.info(f"Streaming query request from user {user}: {query_request.query[:100]}...")
    
    # Extract client IP from request headers (works with proxies)
    client_ip = None
    if http_request.client:
        client_ip = http_request.client.host
    # Also check X-Forwarded-For header if behind a proxy
    elif "x-forwarded-for" in http_request.headers:
        client_ip = http_request.headers["x-forwarded-for"].split(",")[0].strip()
    elif "x-real-ip" in http_request.headers:
        client_ip = http_request.headers["x-real-ip"]
    
    # Create async generator for streaming response
    async def generate_events():
        async for event in streaming_service.stream_query(query_request, user, client_ip=client_ip):
            yield event
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint - validates MCP server connectivity
    
    Returns service health status and MCP server information
    """
    
    from ..services.agent_service import agent_service
    
    try:
        # Get health info from agent service
        health_info = await agent_service.health_check()
        
        # Add minimal API-level health info
        health_info.update({
            "version": "1.0.0"
        })
        
        return health_info
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "version": "1.0.0"
        }