"""Google Tasks API Client."""
import logging
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Thread pool for running sync Google API calls
_executor = ThreadPoolExecutor(max_workers=3)


class GoogleTasksClient:
    """Client for interacting with Google Tasks API."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    async def connect(self):
        """Connect to Google Tasks API using separate Tasks tokens."""
        try:
            import json
            
            # Read tokens from separate Tasks token file
            tokens_path = os.path.expanduser('~/.config/google-calendar-mcp/tasks_token.json')
            
            if not os.path.exists(tokens_path):
                logger.error(f"Tasks tokens not found at {tokens_path}")
                raise FileNotFoundError("Tasks tokens not found. Please run reauth_tasks_only.py first.")
            
            with open(tokens_path, 'r') as f:
                tokens_data = json.load(f)
            
            # Tokens are in google_auth_oauthlib format (not MCP format)
            # Load credentials directly
            self.credentials = Credentials.from_authorized_user_info(tokens_data)
            
            # Refresh token if needed
            if self.credentials.expired:
                self.credentials.refresh(Request())
            
            # Build service
            self.service = build('tasks', 'v1', credentials=self.credentials)
            
            logger.info("Successfully connected to Google Tasks API")
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Tasks API: {e}")
            # Don't raise - just log the error and continue without Tasks support
            self.service = None
    
    def _list_tasks_sync(self, due_min: Optional[str] = None, due_max: Optional[str] = None, show_completed: bool = False) -> List[Dict[str, Any]]:
        """Synchronous version of list_tasks - runs in thread pool."""
        if not self.service:
            logger.warning("Tasks service not initialized")
            return []
        
        try:
            all_tasks = []
            
            # Get all task lists
            task_lists = self.service.tasklists().list().execute()
            
            for task_list in task_lists.get('items', []):
                list_id = task_list['id']
                list_title = task_list.get('title', 'Unnamed List')
                
                # Get tasks from this list
                params = {
                    'tasklist': list_id,
                    'showCompleted': show_completed,
                    'showHidden': False
                }
                
                if due_min:
                    params['dueMin'] = due_min
                if due_max:
                    params['dueMax'] = due_max
                
                try:
                    result = self.service.tasks().list(**params).execute()
                    tasks = result.get('items', [])
                    
                    # Add list title to each task
                    for task in tasks:
                        task['taskListTitle'] = list_title
                        all_tasks.append(task)
                    
                    logger.info(f"Found {len(tasks)} tasks in list '{list_title}'")
                    
                except HttpError as e:
                    logger.error(f"Error fetching tasks from list '{list_title}': {e}")
                    continue
            
            logger.info(f"Total tasks found: {len(all_tasks)}")
            return all_tasks
            
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return []
    
    async def list_tasks(self, due_min: Optional[str] = None, due_max: Optional[str] = None, show_completed: bool = False) -> List[Dict[str, Any]]:
        """List tasks from all task lists.
        
        Args:
            due_min: Minimum due date in RFC3339 format
            due_max: Maximum due date in RFC3339 format
            show_completed: Include completed tasks (default: False)
            
        Returns:
            List of task dictionaries
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._list_tasks_sync, due_min, due_max, show_completed)
    
    async def get_tasks_for_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Get tasks due on a specific date.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            
        Returns:
            List of task dictionaries
        """
        # Convert to RFC3339 format
        due_min = f"{date_str}T00:00:00Z"
        due_max = f"{date_str}T23:59:59Z"
        
        return await self.list_tasks(due_min=due_min, due_max=due_max)
    
    def _create_task_sync(self, title: str, due_date: Optional[datetime] = None, tasklist_id: str = '@default') -> Optional[Dict[str, Any]]:
        """Synchronous version of create_task - runs in thread pool."""
        if not self.service:
            logger.warning("Tasks service not initialized")
            return None
        
        task_body = {
            'title': title,
            'status': 'needsAction'
        }
        
        if due_date:
            # Google Tasks API expects RFC3339 format
            task_body['due'] = due_date.isoformat()
        
        try:
            result = self.service.tasks().insert(tasklist=tasklist_id, body=task_body).execute()
            logger.info(f"Task '{title}' created: {result.get('id')}")
            return result
        except HttpError as e:
            logger.error(f"Error creating task '{title}': {e}")
            return None
    
    async def create_task(self, title: str, due_date: Optional[datetime] = None, tasklist_id: str = '@default') -> Optional[Dict[str, Any]]:
        """Create a new task.
        
        Args:
            title: Task title
            due_date: Optional due date
            tasklist_id: Task list ID (default: '@default')
            
        Returns:
            Created task dictionary or None
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._create_task_sync, title, due_date, tasklist_id)
    
    def _complete_task_sync(self, task_id: str, tasklist_id: str = '@default') -> bool:
        """Synchronous version of complete_task - runs in thread pool."""
        if not self.service:
            logger.warning("Tasks service not initialized")
            return False
        
        try:
            task = self.service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
            task['status'] = 'completed'
            self.service.tasks().update(tasklist=tasklist_id, task=task_id, body=task).execute()
            logger.info(f"Task '{task_id}' completed")
            return True
        except HttpError as e:
            logger.error(f"Error completing task '{task_id}': {e}")
            return False
    
    async def complete_task(self, task_id: str, tasklist_id: str = '@default') -> bool:
        """Mark a task as completed.
        
        Args:
            task_id: Task ID
            tasklist_id: Task list ID (default: '@default')
            
        Returns:
            True if successful
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._complete_task_sync, task_id, tasklist_id)
    
    def _delete_task_sync(self, task_id: str, tasklist_id: str = '@default') -> bool:
        """Synchronous version of delete_task - runs in thread pool."""
        if not self.service:
            logger.warning("Tasks service not initialized")
            return False
        
        try:
            self.service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
            logger.info(f"Task '{task_id}' deleted")
            return True
        except HttpError as e:
            logger.error(f"Error deleting task '{task_id}': {e}")
            return False
    
    async def delete_task(self, task_id: str, tasklist_id: str = '@default') -> bool:
        """Delete a task.
        
        Args:
            task_id: Task ID
            tasklist_id: Task list ID (default: '@default')
            
        Returns:
            True if successful
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._delete_task_sync, task_id, tasklist_id)


# Global Tasks client instance
_tasks_client: Optional[GoogleTasksClient] = None


async def get_tasks_client() -> GoogleTasksClient:
    """Get or create the global Tasks client instance."""
    global _tasks_client
    
    if _tasks_client is None:
        _tasks_client = GoogleTasksClient()
        await _tasks_client.connect()
    
    return _tasks_client
