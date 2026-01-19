"""Handlers for Google Tasks commands."""
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.tasks_client import get_tasks_client
from utils.tasks_formatter import format_tasks_list, format_task
from utils.date_parser import RussianDateParser

router = Router()
logger = logging.getLogger(__name__)

date_parser = RussianDateParser(timezone='Europe/Moscow')
MOSCOW_TZ = ZoneInfo('Europe/Moscow')


@router.message(Command("tasks"))
async def cmd_tasks(message: Message):
    """Show all tasks."""
    await message.answer("🔍 Ищу задачи...")
    
    try:
        tasks_client = await get_tasks_client()
        tasks = await tasks_client.list_tasks()
        
        response = f"✅ <b>Все задачи</b>\n\n{format_tasks_list(tasks)}"
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        await message.answer("❌ Произошла ошибка при получении задач")


@router.message(Command("create_task"))
async def cmd_create_task(message: Message):
    """Create a new task.
    
    Usage: /create_task Название задачи | дата | время (опционально)
    Examples:
        /create_task Купить молоко | завтра
        /create_task Встреча с клиентом | 20.01.2026 | 15:00
        /create_task Позвонить маме | сегодня
    """
    text = message.text
    
    # Remove command
    text = text.replace('/create_task', '').strip()
    
    if not text:
        await message.answer(
            "❌ Укажите название задачи!\n\n"
            "<b>Использование:</b>\n"
            "/create_task Название | дата | время (опционально)\n\n"
            "<b>Примеры:</b>\n"
            "• /create_task Купить молоко | завтра\n"
            "• /create_task Встреча | 20.01 | 15:00\n"
            "• /create_task Позвонить маме | сегодня"
        )
        return
    
    # Parse task parts
    parts = [p.strip() for p in text.split('|')]
    
    title = parts[0]
    
    # Parse date
    due_date = None
    if len(parts) > 1:
        date_text = parts[1]
        parsed_date = date_parser.parse_date(date_text)
        
        logger.info(f"Parsing task date: text='{date_text}', parsed={parsed_date}")
        
        if parsed_date:
            # Google Tasks API only supports dates, not times
            # Set to noon (12:00) to avoid timezone issues
            due_date = parsed_date.replace(hour=12, minute=0, second=0, microsecond=0)
    
    await message.answer(f"➕ Создаю задачу '{title}'...")
    
    try:
        tasks_client = await get_tasks_client()
        
        # Create task via direct API call
        from googleapiclient.errors import HttpError
        
        task_body = {
            'title': title,
            'status': 'needsAction'
        }
        
        if due_date:
            # Make sure it's timezone-aware
            if due_date.tzinfo is None:
                due_date = MOSCOW_TZ.localize(due_date)
            # Convert to RFC3339 format
            task_body['due'] = due_date.isoformat()
            logger.info(f"Task due date set to: {due_date.isoformat()}")
        
        # Create task in default list
        task = tasks_client.service.tasks().insert(
            tasklist='@default',
            body=task_body
        ).execute()
        
        response = f"✅ <b>Задача создана!</b>\n\n{format_task(task)}"
        
        # Warn user if time was specified (Google Tasks API doesn't support time)
        if len(parts) > 2:
            response += "\n\n⚠️ <i>Примечание: Google Tasks API не поддерживает время для задач, сохранена только дата.</i>"
        
        await message.answer(response)
        
    except HttpError as e:
        logger.error(f"HTTP Error creating task: {e}")
        await message.answer(f"❌ Ошибка API: {e}")
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        await message.answer("❌ Произошла ошибка при создании задачи")


@router.message(Command("complete_task"))
async def cmd_complete_task(message: Message):
    """Mark task as completed.
    
    Usage: /complete_task <номер задачи из списка>
    Example: /complete_task 1
    """
    text = message.text.replace('/complete_task', '').strip()
    
    if not text or not text.isdigit():
        await message.answer(
            "❌ Укажите номер задачи!\n\n"
            "<b>Использование:</b>\n"
            "/complete_task <номер>\n\n"
            "Сначала получите список задач командой /tasks"
        )
        return
    
    task_number = int(text)
    
    try:
        tasks_client = await get_tasks_client()
        tasks = await tasks_client.list_tasks()
        
        if task_number < 1 or task_number > len(tasks):
            await message.answer(f"❌ Задача #{task_number} не найдена. Всего задач: {len(tasks)}")
            return
        
        task = tasks[task_number - 1]
        task_id = task['id']
        task_list_id = '@default'  # We need to find the correct list
        
        # Find task list ID (we stored it in taskListTitle, but need the actual ID)
        # For now, try default list
        
        # Update task status
        task['status'] = 'completed'
        
        updated_task = tasks_client.service.tasks().update(
            tasklist=task_list_id,
            task=task_id,
            body=task
        ).execute()
        
        await message.answer(f"✅ Задача '{task['title']}' отмечена как выполненная!")
        
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        await message.answer("❌ Произошла ошибка при выполнении задачи")


@router.message(Command("delete_task"))
async def cmd_delete_task(message: Message):
    """Delete a task.
    
    Usage: /delete_task <номер задачи из списка>
    Example: /delete_task 1
    """
    text = message.text.replace('/delete_task', '').strip()
    
    if not text or not text.isdigit():
        await message.answer(
            "❌ Укажите номер задачи!\n\n"
            "<b>Использование:</b>\n"
            "/delete_task <номер>\n\n"
            "Сначала получите список задач командой /tasks"
        )
        return
    
    task_number = int(text)
    
    try:
        tasks_client = await get_tasks_client()
        tasks = await tasks_client.list_tasks()
        
        if task_number < 1 or task_number > len(tasks):
            await message.answer(f"❌ Задача #{task_number} не найдена. Всего задач: {len(tasks)}")
            return
        
        task = tasks[task_number - 1]
        task_id = task['id']
        task_list_id = '@default'
        
        # Delete task
        tasks_client.service.tasks().delete(
            tasklist=task_list_id,
            task=task_id
        ).execute()
        
        await message.answer(f"✅ Задача '{task['title']}' удалена!")
        
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        await message.answer("❌ Произошла ошибка при удалении задачи")
