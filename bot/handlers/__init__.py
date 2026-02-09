from aiogram import Dispatcher


def register_routers(dp: Dispatcher) -> None:
    from bot.handlers.start import router as start_router
    from bot.handlers.client import router as client_router
    from bot.handlers.seller import router as seller_router
    from bot.handlers.settings import router as settings_router

    dp.include_router(start_router)
    dp.include_router(client_router)
    dp.include_router(seller_router)
    dp.include_router(settings_router)
