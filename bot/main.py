import asyncio
import logging

import uvicorn

from bot.db.engine import async_session
from bot.handlers import register_routers
from bot.loader import bot, dp
from bot.services.request_service import expire_old_requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def expire_requests_loop():
    """Background task: expire old requests every hour."""
    while True:
        await asyncio.sleep(3600)
        try:
            async with async_session() as session:
                count = await expire_old_requests(session)
                if count:
                    logger.info("Expired %d requests", count)
        except Exception as e:
            logger.error("Error expiring requests: %s", e)


async def main():
    register_routers(dp)

    # Create FastAPI app
    from api.app import create_app

    app = create_app()

    # Configure uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    # Run expiry background task
    asyncio.create_task(expire_requests_loop())

    # Run bot polling and uvicorn concurrently
    await asyncio.gather(
        dp.start_polling(bot),
        server.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())
