"""Combined handlers for events and tasks."""
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.mcp_client import get_mcp_client
from bot.tasks_client import get_tasks_client
from utils.tasks_formatter import combine_events_and_tasks

router = Router()
logger = logging.getLogger(__name__)

MOSCOW_TZ = ZoneInfo('Europe/Moscow')


@router.message(Command("tasks"))
async def cmd_tasks(message: Message):
    """Show all tasks."""
    await message.answer("🔍 Ищу задачи...")
    
    try:
        tasks_client = await get_tasks_client()
        tasks = await tasks_client.list_tasks()
        
        from utils.tasks_formatter import format_tasks_list
        response = f"✅ <b>Все задачи</b>\n\n{format_tasks_list(tasks)}"
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        await message.answer("❌ Произошла ошибка при получении задач")


@router.message(Command("today_all"))
async def cmd_today_all(message: Message):
    """Show today's events AND tasks."""
    await message.answer("🔍 Ищу события и задачи на сегодня...")
    
    now = datetime.now(MOSCOW_TZ)
    date_str = now.strftime('%Y-%m-%d')
    
    logger.info(f"Fetching events and tasks for {date_str}")
    
    try:
        # Get events
        mcp_client = await get_mcp_client()
        events = await mcp_client.list_events(
            start_date=date_str,
            end_date=date_str,
            max_results=50
        )
        
        # Get ALL tasks (including completed) and filter locally
        tasks_client = await get_tasks_client()
        all_tasks = await tasks_client.list_tasks(show_completed=True)
        
        # Filter tasks for today
        today_tasks = []
        for task in all_tasks:
            due = task.get('due')
            if due:
                try:
                    # Parse due date (format: 2026-01-17T00:00:00.000Z)
                    due_dt = datetime.fromisoformat(due.replace('Z', '+00:00'))
                    due_date = due_dt.date()
                    logger.info(f"Task '{task.get('title', 'Untitled')}' due: {due_date}, today: {now.date()}, match: {due_date == now.date()}")
                    if due_date == now.date():
                        today_tasks.append(task)
                except Exception as e:
                    logger.warning(f"Could not parse task due date: {due}, error: {e}")
        
        logger.info(f"Found {len(events)} events and {len(today_tasks)} tasks for today")
        
        response = f"📅 <b>Сегодня ({now.strftime('%d.%m.%Y')})</b>\n\n"
        response += combine_events_and_tasks(events, today_tasks)
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error fetching today's events and tasks: {e}")
        await message.answer("❌ Произошла ошибка при получении данных")


@router.message(Command("week_all"))
async def cmd_week_all(message: Message):
    """Show this week's events AND tasks."""
    await message.answer("🔍 Ищу события и задачи на неделю...")
    
    now = datetime.now(MOSCOW_TZ)
    end_date = now + timedelta(days=7)
    
    logger.info(f"Fetching events and tasks for week")
    
    try:
        # Get events
        mcp_client = await get_mcp_client()
        events = await mcp_client.list_events(
            start_date=now.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            max_results=100
        )
        
        # Get ALL tasks (including completed) and filter locally
        tasks_client = await get_tasks_client()
        all_tasks = await tasks_client.list_tasks(show_completed=True)
        
        # Filter tasks for this week
        week_tasks = []
        for task in all_tasks:
            due = task.get('due')
            if due:
                try:
                    # Parse due date
                    due_dt = datetime.fromisoformat(due.replace('Z', '+00:00'))
                    due_date = due_dt.date()
                    if now.date() <= due_date <= end_date.date():
                        week_tasks.append(task)
                except Exception as e:
                    logger.warning(f"Could not parse task due date: {due}, error: {e}")
        
        logger.info(f"Found {len(events)} events and {len(week_tasks)} tasks for week")
        
        response = f"📅 <b>На неделю</b>\n\n"
        response += combine_events_and_tasks(events, week_tasks)
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error fetching week's events and tasks: {e}")
        await message.answer("❌ Произошла ошибка при получении данных")
