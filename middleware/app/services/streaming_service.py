"""
Streaming service for processing NCAAF queries with Server-Sent Events
"""

import json
import logging
import asyncio
import time
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any
from agents import Runner, ItemHelpers
from pydantic import BaseModel

from .agent_service import agent_service
from .logging_service import get_logging_service
from ..config import settings


logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    """Request model for NCAAF queries"""
    query: str
    previous_response_id: Optional[str] = None


class StreamingService:
    """Service for streaming NCAAF query responses"""
    
    def __init__(self):
        self._active_requests = 0
        self._query_start_time = None
    
    async def stream_query(
        self,
        request: QueryRequest,
        user_id: str = "anonymous",
        client_ip: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process query and stream results using Server-Sent Events
        
        Args:
            request: Query request with message and optional conversation ID
            user_id: User identifier for logging
            client_ip: Client IP address for logging
            
        Yields:
            SSE formatted event strings
        """
        
        # Check concurrent request limit
        if self._active_requests >= settings.max_concurrent_requests:
            yield self._create_sse_event(
                "error", 
                {"error": "Too many concurrent requests", "code": "RATE_LIMITED"}
            )
            return
        
        self._active_requests += 1
        self._query_start_time = time.time()
        query_timestamp = datetime.now()
        response_id = None
        response_text = ""
        tool_call_count = 0
        success = False
        error_message = None
        stream_events_count = 0
        result = None
        streaming_result = None
        tool_data = []
        
        try:
            # Ensure agent is initialized and connected
            await agent_service.initialize()
            await agent_service.connect()
            
            logger.info(f"Processing query for user {user_id}: {request.query[:100]}...")
            
            # Start streaming query
            if request.previous_response_id:
                logger.info(f"Using previous_response_id for conversation threading: {request.previous_response_id}")
                result = Runner.run_streamed(
                    starting_agent=agent_service.agent,
                    input=request.query,
                    previous_response_id=request.previous_response_id
                )
            else:
                logger.info("Starting new conversation (no previous_response_id)")
                result = Runner.run_streamed(
                    starting_agent=agent_service.agent,
                    input=request.query
                )
            
            # Store reference to streaming result for token usage extraction
            streaming_result = result
            
            # Send start event - match SDQL format
            yield self._create_sse_event("stream.started", {
                "query": request.query,
                "timestamp": time.time()
            })
            await asyncio.sleep(0)  # Give event loop a chance
            
            # Track tool calls and responses
            tool_calls = {}
            
            # Process stream events
            async for event in result.stream_events():
                try:
                    stream_events_count += 1
                    
                    # Skip raw response events
                    if event.type == "raw_response_event":
                        continue
                    
                    # Handle agent updates
                    elif event.type == "agent_updated_stream_event":
                        logger.info(f"Agent updated: {event.new_agent.name}")
                        continue
                    
                    # Handle run item events - the main content
                    elif event.type == "run_item_stream_event":
                        async for sse_event in self._process_run_item_event(event, tool_calls, tool_data):
                            if sse_event.startswith('RESPONSE_TEXT:'):
                                response_text = sse_event[14:]  # Remove prefix
                            elif sse_event.startswith('TOOL_COUNT:'):
                                tool_call_count = int(sse_event[11:])  # Remove prefix
                            else:
                                yield sse_event
                                await asyncio.sleep(0.001)  # Small delay for streaming effect
                                
                except Exception as e:
                    logger.error(f"Error processing stream event: {e}")
                    error_message = str(e)
                    yield self._create_sse_event(
                        "error", 
                        {"error": "Event processing failed", "details": str(e)}
                    )
            
            # Extract response ID for conversation threading
            response_id = getattr(result, 'last_response_id', None)
            if response_id:
                logger.info(f"OpenAI response ID: {response_id}")
            
            # Mark as successful
            success = True
            
            # Send completion event - match SDQL format
            processing_time = time.time() - self._query_start_time
            completion_data = {
                "response": response_text,
                "response_id": response_id,
                "tool_data": tool_data,
                "processing_time": processing_time
            }
                
            yield self._create_sse_event("stream.completed", completion_data)
            
            # Send [DONE] event like SDQL
            yield "data: [DONE]\n\n"
            
        except asyncio.TimeoutError:
            logger.error(f"Query timeout for user {user_id}")
            error_message = "Query timeout"
            yield self._create_sse_event(
                "error",
                {"error": "Query timeout", "code": "TIMEOUT"}
            )
            
        except Exception as e:
            logger.error(f"Error processing query for user {user_id}: {e}")
            error_message = str(e)
            yield self._create_sse_event(
                "error",
                {"error": "Query processing failed", "details": str(e)}
            )
            
        finally:
            self._active_requests -= 1
            
            # Log usage data (fire and forget)
            logging_service = get_logging_service()
            if logging_service:
                processing_time_ms = int((time.time() - self._query_start_time) * 1000)
                
                # Extract token usage from streaming result if available
                token_usage = {}
                if streaming_result and hasattr(streaming_result, 'context_wrapper') and streaming_result.context_wrapper:
                    token_usage = logging_service.extract_token_usage(streaming_result.context_wrapper.usage)
                else:
                    # Fallback to empty token usage
                    token_usage = logging_service.extract_token_usage(None)
                
                # Log the usage asynchronously
                asyncio.create_task(logging_service.log_usage_async(
                    username=user_id,
                    query=request.query,
                    query_timestamp=query_timestamp,
                    response_text=response_text,
                    processing_time_ms=processing_time_ms,
                    tool_calls_count=len(tool_data),
                    tool_data=tool_data,
                    stream_events_count=stream_events_count,
                    success=success,
                    error_message=error_message,
                    client_ip=client_ip,
                    **token_usage
                ))
    
    async def _process_run_item_event(
        self,
        event: Any,
        tool_calls: Dict[Any, Dict[str, Any]],
        tool_data: list
    ) -> AsyncGenerator[str, None]:
        """Process run_item_stream_event and yield appropriate SSE events"""
        
        try:
            item = event.item
            logger.info(f"Processing run item: {item.type}")
            
            if item.type == "tool_call_item":
                # Tool call started
                tool_name, tool_id = self._extract_tool_info(item)
                logger.info(f"Tool call started: {tool_name}")
                
                # Store tool call for later matching
                call_key = tool_id if tool_id else len(tool_calls)
                tool_calls[call_key] = {
                    'tool_name': tool_name,
                    'output': None
                }
                
                yield f"TOOL_COUNT:{len(tool_calls)}"
                yield self._create_sse_event('response.tool.started', {
                    'tool': tool_name
                })
            
            elif item.type == "tool_call_output_item":
                # Tool call completed
                logger.info("Tool call completed")
                tool_output = getattr(item, 'output', None)
                
                # Find matching tool call
                matched_tool = self._match_tool_output(tool_calls, tool_output, tool_data)
                tool_name = matched_tool or 'unknown'
                
                logger.info(f"Tool completed: {tool_name}")
                yield self._create_sse_event('response.tool.completed', {
                    'tool': tool_name
                })
            
            elif item.type == "message_output_item":
                # Process message output - this contains the actual response text
                async for text_event in self._process_message_output(item):
                    if text_event.startswith('RESPONSE_TEXT:'):
                        yield text_event  # Pass through for completion event
                    else:
                        yield text_event
            
            else:
                logger.debug(f"Unhandled item type: {item.type}")
                
        except Exception as e:
            logger.error(f"Error processing run item event: {e}")
    
    def _extract_tool_info(self, item: Any) -> tuple[str, Optional[str]]:
        """Extract tool name and ID from a tool call item"""
        tool_name = "unknown"
        tool_id = None
        
        try:
            if hasattr(item, 'raw_item'):
                raw_item = item.raw_item
                
                if hasattr(raw_item, 'function'):
                    func = getattr(raw_item, 'function', None)
                    if func and hasattr(func, 'name'):
                        tool_name = func.name
                        tool_id = getattr(raw_item, 'id', None)
                elif hasattr(raw_item, 'name'):
                    tool_name = getattr(raw_item, 'name', 'unknown')
                    tool_id = getattr(raw_item, 'id', None)
        except Exception as e:
            logger.debug(f"Error extracting tool info: {e}")
        
        return tool_name, tool_id
    
    def _extract_tool_parameters(self, item: Any) -> Dict[str, Any]:
        """Extract tool parameters from tool call item"""
        try:
            if hasattr(item, 'raw_item') and hasattr(item.raw_item, 'function'):
                func = item.raw_item.function
                if hasattr(func, 'arguments'):
                    import json
                    return json.loads(func.arguments)
        except Exception as e:
            logger.debug(f"Error extracting tool parameters: {e}")
        
        return {}
    
    def _match_tool_output(
        self,
        tool_calls: Dict[Any, Dict[str, Any]],
        tool_output: Any,
        tool_data: list
    ) -> Optional[str]:
        """Match tool output with previous tool call"""
        
        # Find most recent tool call without output
        for call_key, call_info in reversed(list(tool_calls.items())):
            if call_info['output'] is None:
                call_info['output'] = tool_output
                
                # Add to tool data - match SDQL format
                tool_data.append({
                    'tool_name': call_info['tool_name'],
                    'response': self._parse_tool_output(tool_output)
                })
                
                return call_info['tool_name']
        
        return None
    
    def _parse_tool_output(self, tool_output: Any) -> Any:
        """Parse tool output, handling text and JSON"""
        try:
            # Extract text content if wrapped
            if hasattr(tool_output, 'text'):
                tool_output = getattr(tool_output, 'text', tool_output)
            
            # Try to parse as JSON
            if isinstance(tool_output, str):
                try:
                    return json.loads(tool_output)
                except json.JSONDecodeError:
                    return tool_output
            
            return tool_output
        except Exception:
            return str(tool_output)
    
    async def _process_message_output(self, item: Any) -> AsyncGenerator[str, None]:
        """Process message output item and stream text"""
        
        try:
            # Use ItemHelpers to extract text properly
            text = ItemHelpers.text_message_output(item)
            logger.info(f"Message output text length: {len(text) if text else 0}")
            
            if text and text.strip():
                # Store full response text
                yield f"RESPONSE_TEXT:{text}"
                
                # Stream text in small chunks for UI effect
                chunk_size = 5  # Characters per chunk
                for i in range(0, len(text), chunk_size):
                    chunk = text[i:i + chunk_size]
                    yield self._create_sse_event('response.text.delta', {'delta': chunk})
                    await asyncio.sleep(0.002)  # Small delay for streaming effect
                    
        except Exception as e:
            logger.error(f"Error processing message output: {e}")
    
    
    def _create_sse_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Create Server-Sent Event formatted string (SDQL format)"""
        try:
            # Embed event type in the data (like SDQL)
            event_data = {'type': event_type, **data}
            json_str = json.dumps(event_data, default=str)
            return f"data: {json_str}\n\n"
        except Exception as e:
            logger.error(f"Error creating SSE event: {e}")
            return f"data: {{\"type\": \"error\", \"error\": \"Event formatting failed\"}}\n\n"
    
    @property
    def active_requests(self) -> int:
        """Get number of currently active requests"""
        return self._active_requests


# Global streaming service instance
streaming_service = StreamingService()