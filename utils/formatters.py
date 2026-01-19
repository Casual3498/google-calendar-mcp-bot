"""Formatting utilities for bot responses."""
from datetime import datetime
from typing import List, Dict, Any
import pytz


def format_event(event: Dict[str, Any]) -> str:
    """Format a single event for display.
    
    Args:
        event: Event dictionary from Google Calendar
        
    Returns:
        Formatted event string
    """
    summary = event.get('summary', 'Без названия')
    
    # Parse start time
    start = event.get('start', {})
    start_time = start.get('dateTime', start.get('date', ''))
    
    # Parse end time
    end = event.get('end', {})
    end_time = end.get('dateTime', end.get('date', ''))
    
    # Format times
    try:
        if 'T' in start_time:  # DateTime format
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
            date_str = start_dt.strftime('%d.%m.%Y')
        else:  # Date only
            start_dt = datetime.fromisoformat(start_time)
            date_str = start_dt.strftime('%d.%m.%Y')
            time_str = "Весь день"
    except:
        time_str = "Время не указано"
        date_str = "Дата не указана"
    
    description = event.get('description', '')
    location = event.get('location', '')
    event_id = event.get('id', '')
    
    result = f"📅 <b>{summary}</b>\n"
    result += f"🗓 {date_str}\n"
    result += f"🕐 {time_str}\n"
    
    if location:
        result += f"📍 {location}\n"
    if description:
        result += f"📝 {description}\n"
    if event_id:
        result += f"🔑 ID: <code>{event_id}</code>\n"
    
    return result


def format_events_list(events: List[Dict[str, Any]]) -> str:
    """Format a list of events for display.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        Formatted events list string
    """
    if not events:
        return "📭 Событий не найдено"
    
    result = f"📋 <b>Найдено событий: {len(events)}</b>\n\n"
    
    for i, event in enumerate(events, 1):
        result += f"{i}. {format_event(event)}\n"
    
    return result


def format_date_range(start_date: datetime, end_date: datetime) -> str:
    """Format a date range for display.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Formatted date range string
    """
    if start_date.date() == end_date.date():
        return start_date.strftime('%d.%m.%Y')
    else:
        return f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"


MONTH_NAMES = [
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
]


def format_datetime_ru(dt: datetime) -> str:
    """Format datetime in Russian format.
    
    Args:
        dt: Datetime object
        
    Returns:
        Formatted string like "15 января 2024, 10:00"
    """
    day = dt.day
    month = MONTH_NAMES[dt.month - 1]
    year = dt.year
    time = dt.strftime('%H:%M')
    
    return f"{day} {month} {year}, {time}"
