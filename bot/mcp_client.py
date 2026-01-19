"""MCP Client for Google Calendar integration."""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config.settings import MCP_SERVER_COMMAND, MCP_SERVER_ARGS

logger = logging.getLogger(__name__)


class GoogleCalendarMCPClient:
    """Client for interacting with Google Calendar via MCP."""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._stdio_context = None
        
    async def connect(self):
        """Connect to the MCP server."""
        try:
            import os
            # Prepare environment variables for MCP server
            mcp_env = os.environ.copy()
            
            # Ensure GOOGLE_OAUTH_CREDENTIALS is set
            if "GOOGLE_OAUTH_CREDENTIALS" not in mcp_env:
                from config.settings import PROJECT_ROOT
                credentials_path = os.path.join(PROJECT_ROOT, "credentials", "google_credentials.json")
                if os.path.exists(credentials_path):
                    mcp_env["GOOGLE_OAUTH_CREDENTIALS"] = credentials_path
            
            server_params = StdioServerParameters(
                command=MCP_SERVER_COMMAND,
                args=MCP_SERVER_ARGS,
                env=mcp_env
            )
            
            # stdio_client returns an async context manager
            self._stdio_context = stdio_client(server_params)
            self._read_stream, self._write_stream = await self._stdio_context.__aenter__()
            self.session = ClientSession(self._read_stream, self._write_stream)
            
            await self.session.__aenter__()
            
            # Initialize the session
            await self.session.initialize()
            
            logger.info("Successfully connected to Google Calendar MCP server")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error disconnecting session: {e}")
        
        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
                logger.info("Disconnected from Google Calendar MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server: {e}")
    
    async def list_events(self, start_date: str, end_date: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """List calendar events in a date range.
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            max_results: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        if not self.session:
            raise RuntimeError("MCP client not connected")
        
        try:
            arguments = {
                "calendarId": "primary",  # Required parameter
                "timeMin": f"{start_date}T00:00:00Z",
                "timeMax": f"{end_date}T23:59:59Z",
                "maxResults": max_results,
                "singleEvents": True  # Expand recurring events into instances
            }
            
            logger.info(f"Requesting events with arguments: {arguments}")
            
            result = await self.session.call_tool(
                "list-events",  # Use hyphenated name
                arguments=arguments
            )
            
            # Parse the result
            events = []
            if result.content and len(result.content) > 0:
                content = result.content[0]
                
                if hasattr(content, 'text'):
                    text_content = content.text
                    
                    # Parse the text response
                    import json
                    try:
                        events_data = json.loads(text_content)
                        # MCP server returns {"events": [...], "totalCount": N}
                        if isinstance(events_data, dict) and 'events' in events_data:
                            events = events_data['events']
                        elif isinstance(events_data, dict) and 'items' in events_data:
                            events = events_data['items']
                        elif isinstance(events_data, list):
                            events = events_data
                        else:
                            logger.warning(f"Unexpected events_data format: {type(events_data)}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Could not parse events as JSON: {e}")
                        logger.error(f"Raw text: {text_content[:500]}")
            
            logger.info(f"Parsed {len(events)} events from MCP")
            return events
            
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            return []
    
    async def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new calendar event.
        
        Args:
            summary: Event title
            start_time: Start time in ISO format
            end_time: End time in ISO format
            description: Event description (optional)
            location: Event location (optional)
            
        Returns:
            Created event dictionary or None if failed
        """
        if not self.session:
            raise RuntimeError("MCP client not connected")
        
        try:
            event_data = {
                "summary": summary,
                "start": {"dateTime": start_time, "timeZone": "UTC"},
                "end": {"dateTime": end_time, "timeZone": "UTC"}
            }
            
            if description:
                event_data["description"] = description
            if location:
                event_data["location"] = location
            
            result = await self.session.call_tool(
                "create-event",  # Use hyphenated name
                arguments={
                    "calendarId": "primary",  # Required parameter
                    "event": event_data
                }
            )
            
            logger.info(f"Event created: {summary}")
            return event_data
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return None
    
    async def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """Update an existing calendar event.
        
        Args:
            event_id: ID of the event to update
            summary: New event title (optional)
            start_time: New start time in ISO format (optional)
            end_time: New end time in ISO format (optional)
            description: New description (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.session:
            raise RuntimeError("MCP client not connected")
        
        try:
            updates = {}
            if summary:
                updates["summary"] = summary
            if start_time:
                updates["start"] = {"dateTime": start_time, "timeZone": "UTC"}
            if end_time:
                updates["end"] = {"dateTime": end_time, "timeZone": "UTC"}
            if description:
                updates["description"] = description
            
            result = await self.session.call_tool(
                "update-event",  # Use hyphenated name
                arguments={
                    "calendarId": "primary",  # Required parameter
                    "eventId": event_id,
                    "event": updates
                }
            )
            
            logger.info(f"Event updated: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return False
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event.
        
        Args:
            event_id: ID of the event to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.session:
            raise RuntimeError("MCP client not connected")
        
        try:
            result = await self.session.call_tool(
                "delete-event",  # Use hyphenated name
                arguments={
                    "calendarId": "primary",  # Required parameter
                    "eventId": event_id
                }
            )
            
            logger.info(f"Event deleted: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False


# Global MCP client instance
_mcp_client: Optional[GoogleCalendarMCPClient] = None


async def get_mcp_client() -> GoogleCalendarMCPClient:
    """Get or create the global MCP client instance."""
    global _mcp_client
    
    if _mcp_client is None:
        _mcp_client = GoogleCalendarMCPClient()
        await _mcp_client.connect()
    
    return _mcp_client
