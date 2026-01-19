"""Main entry point for the Telegram bot."""
import asyncio
import logging

from bot.bot_instance import start_bot, stop_bot

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot."""
    try:
        await start_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        await stop_bot()


if __name__ == "__main__":
    asyncio.run(main())
