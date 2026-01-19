"""Main bot instance and initialization."""
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config.settings import TELEGRAM_BOT_TOKEN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create bot instance
bot = Bot(
    token=TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Create dispatcher
dp = Dispatcher()


async def setup_bot():
    """Setup bot and register handlers."""
    from handlers import calendar_handlers, common_handlers, combined_handlers, tasks_handlers
    
    # Register handlers
    dp.include_router(common_handlers.router)
    dp.include_router(tasks_handlers.router)  # Tasks commands
    dp.include_router(combined_handlers.router)  # Combined view
    dp.include_router(calendar_handlers.router)  # Calendar with natural language
    
    logger.info("Bot handlers registered")


async def start_bot():
    """Start the bot."""
    await setup_bot()
    
    # Initialize MCP client for Google Calendar
    from bot.mcp_client import get_mcp_client
    await get_mcp_client()
    
    # Initialize Tasks client (optional - won't fail if not available)
    try:
        from bot.tasks_client import get_tasks_client
        await get_tasks_client()
        logger.info("Google Tasks client initialized")
    except Exception as e:
        logger.warning(f"Google Tasks client not available: {e}")
        logger.info("Bot will work without Tasks support")
    
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


async def stop_bot():
    """Stop the bot and cleanup."""
    from bot.mcp_client import _mcp_client
    
    if _mcp_client:
        await _mcp_client.disconnect()
    
    await bot.session.close()
    logger.info("Bot stopped")
