"""Calendar-specific handlers."""
import re
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.mcp_client import get_mcp_client
from utils.date_parser import RussianDateParser
from utils.formatters import format_events_list, format_event, format_datetime_ru

router = Router()
logger = logging.getLogger(__name__)

# Initialize date parser
date_parser = RussianDateParser(timezone='Europe/Moscow')

# Timezone for Moscow
MOSCOW_TZ = ZoneInfo('Europe/Moscow')


@router.message(Command("today"))
async def cmd_today(message: Message):
    """Show today's events."""
    # Get current time in Moscow timezone
    now_moscow = datetime.now(MOSCOW_TZ)
    logger.info(f"Current time in Moscow: {now_moscow}")
    await show_events_for_date(message, days_offset=0, label="сегодня")


@router.message(Command("tomorrow"))
async def cmd_tomorrow(message: Message):
    """Show tomorrow's events."""
    await show_events_for_date(message, days_offset=1, label="завтра")


@router.message(Command("week"))
async def cmd_week(message: Message):
    """Show this week's events."""
    now = datetime.now(MOSCOW_TZ)
    end_date = now + timedelta(days=7)
    
    logger.info(f"Fetching week events from {now} to {end_date}")
    await message.answer("🔍 Ищу события на неделю...")
    
    try:
        mcp_client = await get_mcp_client()
        events = await mcp_client.list_events(
            start_date=now.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            max_results=100
        )
        
        response = f"📅 <b>События на неделю</b>\n\n{format_events_list(events)}"
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error fetching week events: {e}")
        await message.answer("❌ Произошла ошибка при получении событий")


@router.message(Command("month"))
async def cmd_month(message: Message):
    """Show this month's events."""
    now = datetime.now(MOSCOW_TZ)
    end_date = now + timedelta(days=30)
    
    logger.info(f"Fetching month events from {now} to {end_date}")
    await message.answer("🔍 Ищу события на месяц...")
    
    try:
        mcp_client = await get_mcp_client()
        events = await mcp_client.list_events(
            start_date=now.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            max_results=250
        )
        
        response = f"📅 <b>События на месяц</b>\n\n{format_events_list(events)}"
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error fetching month events: {e}")
        await message.answer("❌ Произошла ошибка при получении событий")


@router.message(Command("all"))
async def cmd_all(message: Message):
    """Show all upcoming events."""
    now = datetime.now(MOSCOW_TZ)
    # Показать события за 2 года (включая прошлые повторяющиеся)
    start_date = now - timedelta(days=365)  # Год назад
    end_date = now + timedelta(days=730)  # 2 года вперёд
    
    logger.info(f"Fetching all events from {start_date} to {end_date}")
    await message.answer("🔍 Ищу все события...")
    
    try:
        mcp_client = await get_mcp_client()
        events = await mcp_client.list_events(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            max_results=500
        )
        
        logger.info(f"Found {len(events)} events")
        response = f"📅 <b>Все события</b>\n\n{format_events_list(events)}"
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error fetching all events: {e}")
        await message.answer("❌ Произошла ошибка при получении событий")


async def show_events_for_date(message: Message, days_offset: int, label: str):
    """Show events for a specific date offset."""
    target_date = datetime.now(MOSCOW_TZ) + timedelta(days=days_offset)
    
    logger.info(f"Fetching events for {label}: {target_date.strftime('%Y-%m-%d')}")
    await message.answer(f"🔍 Ищу события на {label}...")
    
    try:
        mcp_client = await get_mcp_client()
        events = await mcp_client.list_events(
            start_date=target_date.strftime('%Y-%m-%d'),
            end_date=target_date.strftime('%Y-%m-%d'),
            max_results=50
        )
        
        logger.info(f"Found {len(events)} events for {label}")
        response = f"📅 <b>События на {label}</b>\n\n{format_events_list(events)}"
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        await message.answer("❌ Произошла ошибка при получении событий")


@router.message()
async def handle_text_message(message: Message):
    """Handle text messages with natural language commands."""
    text = message.text.lower()
    
    # Check for "show events" commands
    if any(word in text for word in ['покажи', 'показать', 'события', 'что', 'список']):
        await handle_show_events(message)
    
    # Check for "create event" commands
    elif any(word in text for word in ['создай', 'создать', 'назначь', 'назначить', 'добавь', 'добавить', 'встреча', 'событие']):
        await handle_create_event(message)
    
    # Check for "delete event" commands
    elif any(word in text for word in ['удали', 'удалить', 'убери', 'убрать']):
        await handle_delete_event(message)
    
    # Check for "move/update event" commands
    elif any(word in text for word in ['перенеси', 'перенести', 'измени', 'изменить']):
        await handle_update_event(message)
    
    else:
        # Unknown command
        await message.answer(
            "🤔 Я не совсем понял, что вы хотите сделать.\n\n"
            "Используйте /help для просмотра доступных команд."
        )


async def handle_show_events(message: Message):
    """Handle show events command."""
    from bot.tasks_client import get_tasks_client
    from utils.tasks_formatter import combine_events_and_tasks
    
    text = message.text
    
    # Send "searching" message FIRST
    await message.answer(f"🔍 Ищу события и задачи...")
    
    # Parse date from message
    parsed_date = date_parser.parse_date(text)
    
    if parsed_date is None:
        # Default to today
        parsed_date = datetime.now(MOSCOW_TZ)
    
    # Make sure parsed_date is timezone-aware
    if parsed_date.tzinfo is None:
        parsed_date = MOSCOW_TZ.localize(parsed_date)
    
    # Determine date label
    now = datetime.now(MOSCOW_TZ)
    date_diff = (parsed_date.date() - now.date()).days
    
    logger.info(f"Date calculation: parsed_date={parsed_date.date()}, now={now.date()}, diff={date_diff}")
    
    if date_diff == 0:
        date_label = "Сегодня"
    elif date_diff == -1:
        date_label = "Вчера"
    elif date_diff == 1:
        date_label = "Завтра"
    elif date_diff == -2:
        date_label = "Позавчера"
    elif date_diff == 2:
        date_label = "Послезавтра"
    else:
        date_label = parsed_date.strftime('%d.%m.%Y')
    
    logger.info(f"Date label: {date_label}")
    
    # Check if user wants a week view
    if 'неделю' in text.lower() or 'недел' in text.lower():
        end_date = parsed_date + timedelta(days=7)
        date_label = "На неделю"
    else:
        end_date = parsed_date
    
    try:
        # Get events
        mcp_client = await get_mcp_client()
        events = await mcp_client.list_events(
            start_date=parsed_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            max_results=100
        )
        
        # Get tasks
        tasks_client = await get_tasks_client()
        all_tasks = await tasks_client.list_tasks()
        
        # Filter tasks for the date range
        filtered_tasks = []
        for task in all_tasks:
            due = task.get('due')
            if due:
                try:
                    due_dt = datetime.fromisoformat(due.replace('Z', '+00:00'))
                    due_date = due_dt.date()
                    if parsed_date.date() <= due_date <= end_date.date():
                        filtered_tasks.append(task)
                except Exception as e:
                    logger.warning(f"Could not parse task due date: {due}, error: {e}")
        
        response = f"📅 <b>{date_label} ({parsed_date.strftime('%d.%m.%Y')})</b>\n\n"
        response += combine_events_and_tasks(events, filtered_tasks)
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error showing events: {e}")
        await message.answer("❌ Произошла ошибка при получении событий")


async def handle_create_event(message: Message):
    """Handle create event command."""
    text = message.text
    
    # Extract event title (text in quotes or after certain keywords)
    title_match = re.search(r'[\'"]([^\'"]+)[\'"]', text)
    if title_match:
        title = title_match.group(1)
    else:
        # Try to extract title from context
        # Remove command words to get potential title
        cleaned = text.lower()
        for word in ['создай', 'создать', 'назначь', 'назначить', 'добавь', 'добавить', 'событие', 'встречу', 'встреча']:
            cleaned = cleaned.replace(word, '')
        
        # Get first meaningful phrase
        words = cleaned.strip().split()
        if words:
            # Take first 3-5 words as title
            title = ' '.join(words[:min(5, len(words))])
        else:
            title = "Новое событие"
    
    # Parse datetime
    try:
        start_dt, end_dt = date_parser.parse_datetime(text)
    except:
        await message.answer(
            "❌ Не удалось распознать дату и время.\n\n"
            "Пример: 'Создай встречу на завтра в 10:00'"
        )
        return
    
    # Parse duration if specified
    duration = date_parser.parse_duration(text)
    end_dt = start_dt + timedelta(minutes=duration)
    
    await message.answer(f"➕ Создаю событие '{title}'...")
    
    try:
        mcp_client = await get_mcp_client()
        event = await mcp_client.create_event(
            summary=title,
            start_time=start_dt.isoformat(),
            end_time=end_dt.isoformat()
        )
        
        if event:
            response = f"✅ <b>Событие создано!</b>\n\n"
            response += f"📅 {title}\n"
            response += f"🕐 {format_datetime_ru(start_dt)}\n"
            response += f"⏱ Длительность: {duration} минут"
            await message.answer(response)
        else:
            await message.answer("❌ Не удалось создать событие")
            
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        await message.answer("❌ Произошла ошибка при создании события")


async def handle_delete_event(message: Message):
    """Handle delete event command."""
    text = message.text
    
    # Extract event ID
    # Look for patterns like "event_id" or quoted strings
    id_match = re.search(r'([a-zA-Z0-9_-]{20,})', text)
    
    if not id_match:
        await message.answer(
            "❌ Не указан ID события.\n\n"
            "Сначала получите список событий, затем используйте:\n"
            "'Удали событие [ID]'"
        )
        return
    
    event_id = id_match.group(1)
    
    await message.answer(f"🗑 Удаляю событие...")
    
    try:
        mcp_client = await get_mcp_client()
        success = await mcp_client.delete_event(event_id)
        
        if success:
            await message.answer("✅ Событие успешно удалено")
        else:
            await message.answer("❌ Не удалось удалить событие. Проверьте ID.")
            
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        await message.answer("❌ Произошла ошибка при удалении события")


async def handle_update_event(message: Message):
    """Handle update/move event command."""
    text = message.text
    
    # Extract event ID
    id_match = re.search(r'([a-zA-Z0-9_-]{20,})', text)
    
    if not id_match:
        await message.answer(
            "❌ Не указан ID события.\n\n"
            "Используйте: 'Перенеси событие [ID] на [новая дата] в [время]'"
        )
        return
    
    event_id = id_match.group(1)
    
    # Parse new datetime
    try:
        start_dt, end_dt = date_parser.parse_datetime(text)
    except:
        await message.answer(
            "❌ Не удалось распознать новую дату и время.\n\n"
            "Пример: 'Перенеси событие [ID] на завтра в 15:00'"
        )
        return
    
    await message.answer(f"✏️ Переношу событие...")
    
    try:
        mcp_client = await get_mcp_client()
        success = await mcp_client.update_event(
            event_id=event_id,
            start_time=start_dt.isoformat(),
            end_time=end_dt.isoformat()
        )
        
        if success:
            response = f"✅ <b>Событие перенесено!</b>\n\n"
            response += f"🕐 Новое время: {format_datetime_ru(start_dt)}"
            await message.answer(response)
        else:
            await message.answer("❌ Не удалось перенести событие. Проверьте ID.")
            
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        await message.answer("❌ Произошла ошибка при переносе события")
