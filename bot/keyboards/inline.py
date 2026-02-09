import json

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.config import settings
from bot.locales import t

_BRANDS: list[str] = []


def _get_brands() -> list[str]:
    global _BRANDS
    if not _BRANDS:
        import pathlib

        cars_path = pathlib.Path(__file__).resolve().parent.parent.parent / "data" / "cars.json"
        with open(cars_path) as f:
            _BRANDS = list(json.load(f).keys())
    return _BRANDS


def webapp_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("find_part", lang),
                    web_app=WebAppInfo(url=settings.WEBAPP_URL),
                )
            ]
        ]
    )


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
            ]
        ]
    )


def role_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("role_client", lang), callback_data="role:client")],
            [InlineKeyboardButton(text=t("role_seller", lang), callback_data="role:seller")],
        ]
    )


def brands_keyboard(
    selected: set[str] | None = None, lang: str = "ru"
) -> InlineKeyboardMarkup:
    selected = selected or set()
    brands = _get_brands()
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for brand in brands:
        check = "☑" if brand in selected else "☐"
        btn = InlineKeyboardButton(
            text=f"{check} {brand}", callback_data=f"toggle_brand:{brand}"
        )
        row.append(btn)
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(text=t("done", lang), callback_data="brands_done")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def request_notification_keyboard(
    request_id: int, lang: str = "ru"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("respond_price", lang),
                    callback_data=f"respond:{request_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("skip", lang), callback_data=f"skip:{request_id}"
                )
            ],
        ]
    )


def currency_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("currency_sum", lang), callback_data="currency:sum"
                ),
                InlineKeyboardButton(
                    text=t("currency_usd", lang), callback_data="currency:usd"
                ),
            ]
        ]
    )


def availability_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("in_stock", lang), callback_data="availability:in_stock"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("order_1_3", lang), callback_data="availability:order_1_3"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("order_3_7", lang), callback_data="availability:order_3_7"
                )
            ],
        ]
    )


def skip_comment_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("skip_comment", lang), callback_data="skip_comment"
                )
            ]
        ]
    )


def contact_seller_keyboard(
    offer_id: int, lang: str = "ru"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("contact_seller", lang),
                    callback_data=f"contact:{offer_id}",
                )
            ]
        ]
    )


def request_detail_keyboard(
    offers: list[tuple[int, str]], request_id: int, lang: str = "ru"
) -> InlineKeyboardMarkup:
    """offers: list of (offer_id, seller_name)"""
    rows: list[list[InlineKeyboardButton]] = []
    for offer_id, seller_name in offers:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("contact_btn", lang, seller_name=seller_name),
                    callback_data=f"contact:{offer_id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t("close_request_btn", lang),
                callback_data=f"close_request:{request_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_requests_keyboard(
    requests: list[tuple[int, int]], lang: str = "ru"
) -> InlineKeyboardMarkup:
    """requests: list of (request_id, display_num)"""
    rows = [
        [
            InlineKeyboardButton(
                text=t("detail_btn", lang, request_id=req_id),
                callback_data=f"request_detail:{req_id}",
            )
        ]
        for req_id, _ in requests
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def seller_active_requests_keyboard(
    requests: list[tuple[int, int]], lang: str = "ru"
) -> InlineKeyboardMarkup:
    """requests: list of (request_id, display_num)"""
    rows = [
        [
            InlineKeyboardButton(
                text=t("respond_btn", lang, request_id=req_id),
                callback_data=f"respond:{req_id}",
            )
        ]
        for req_id, _ in requests
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_keyboard(is_seller: bool = False, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t("change_language", lang), callback_data="settings:language"
            )
        ]
    ]
    if is_seller:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("change_brands", lang), callback_data="settings:brands"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)
