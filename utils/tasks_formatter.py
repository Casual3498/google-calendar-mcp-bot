"""Formatters for Google Tasks."""
from datetime import datetime
from typing import List, Dict, Any


def format_task(task: Dict[str, Any]) -> str:
    """Format a single task for display.
    
    Args:
        task: Task dictionary from Google Tasks API
        
    Returns:
        Formatted task string
    """
    title = task.get('title', 'Без названия')
    due = task.get('due')
    notes = task.get('notes', '')
    list_title = task.get('taskListTitle', 'My Tasks')
    
    # Format due date
    due_str = ""
    if due:
        try:
            due_date = datetime.fromisoformat(due.replace('Z', '+00:00'))
            due_str = f"\n   🗓 {due_date.strftime('%d.%m.%Y %H:%M')}"
        except:
            due_str = f"\n   🗓 {due}"
    
    # Format notes
    notes_str = ""
    if notes:
        notes_preview = notes[:50] + "..." if len(notes) > 50 else notes
        notes_str = f"\n   📝 {notes_preview}"
    
    result = f"✅ <b>{title}</b>"
    result += f"\n   📋 {list_title}"
    if due_str:
        result += due_str
    if notes_str:
        result += notes_str
    
    return result


def format_tasks_list(tasks: List[Dict[str, Any]]) -> str:
    """Format a list of tasks for display.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        Formatted tasks string
    """
    if not tasks:
        return "Задач не найдено"
    
    result = []
    for i, task in enumerate(tasks, 1):
        result.append(f"{i}. {format_task(task)}")
    
    result.append(f"\n<b>Всего задач:</b> {len(tasks)}")
    return "\n\n".join(result)


def combine_events_and_tasks(events: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> str:
    """Combine events and tasks into a single formatted string.
    
    Args:
        events: List of calendar events
        tasks: List of tasks
        
    Returns:
        Combined formatted string
    """
    from utils.formatters import format_event
    
    result = []
    
    # Add events
    if events:
        result.append("<b>📅 События:</b>\n")
        for i, event in enumerate(events, 1):
            result.append(f"{i}. {format_event(event)}")
    
    # Add tasks
    if tasks:
        if events:
            result.append("\n" + "─" * 30 + "\n")
        result.append("<b>✅ Задачи:</b>\n")
        for i, task in enumerate(tasks, 1):
            result.append(f"{i}. {format_task(task)}")
    
    if not events and not tasks:
        return "Событий и задач не найдено"
    
    # Add totals
    result.append(f"\n<b>Итого:</b> {len(events)} событий, {len(tasks)} задач")
    
    return "\n\n".join(result)
