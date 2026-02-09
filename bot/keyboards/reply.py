from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from bot.config import settings
from bot.locales import t


def contact_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("share_contact_btn", lang), request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def client_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=t("find_part", lang),
                    web_app=WebAppInfo(url=settings.WEBAPP_URL),
                )
            ],
            [
                KeyboardButton(text=t("my_requests", lang)),
                KeyboardButton(text=t("settings", lang)),
            ],
        ],
        resize_keyboard=True,
    )


def seller_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("active_requests", lang))],
            [KeyboardButton(text=t("settings", lang))],
        ],
        resize_keyboard=True,
    )
