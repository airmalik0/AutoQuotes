from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from sqlalchemy import select

from bot.db.engine import async_session
from bot.db.models import RoleEnum, User
from bot.keyboards.inline import (
    my_requests_keyboard,
    request_detail_keyboard,
)
from bot.locales import t
from bot.services._helpers import format_offers_count, time_ago
from bot.services.offer_service import get_offer_with_seller
from bot.services.request_service import close_request, get_request_detail, get_user_requests

router = Router()


async def _get_user_lang(telegram_id: int) -> tuple[User | None, str]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        lang = user.language.value if user and user.language else "ru"
        return user, lang


# --- "Мои запросы" ---
@router.message(F.text.in_(["📋 Мои запросы", "📋 Mening so'rovlarim"]))
async def on_my_requests(message: Message):
    user, lang = await _get_user_lang(message.from_user.id)
    if not user:
        return

    async with async_session() as session:
        requests = await get_user_requests(session, user.id)

    if not requests:
        await message.answer(t("no_requests", lang))
        return

    lines = [t("my_requests_list", lang), ""]
    req_list = []
    for i, req in enumerate(requests, 1):
        offers_text = format_offers_count(req["offer_count"], lang)
        ago = time_ago(req["created_at"], lang)
        lines.append(
            t(
                "request_item",
                lang,
                num=i,
                brand=req["brand"],
                model=req["model"],
                year=req["year"],
                description=req["description"],
                offers_text=offers_text,
                time_ago=ago,
            )
        )
        req_list.append((req["id"], i))

    keyboard = my_requests_keyboard(req_list, lang)
    await message.answer("\n".join(lines), reply_markup=keyboard)


# --- Request detail ---
@router.callback_query(F.data.startswith("request_detail:"))
async def on_request_detail(callback: CallbackQuery):
    request_id = int(callback.data.split(":")[1])
    _, lang = await _get_user_lang(callback.from_user.id)

    async with async_session() as session:
        detail = await get_request_detail(session, request_id)

    if not detail:
        await callback.answer()
        return

    part_type_text = t(f"part_type_{detail['part_type']}", lang)
    ago = time_ago(detail["created_at"], lang)

    if detail["offers"]:
        lines = [
            t(
                "request_detail",
                lang,
                brand=detail["brand"],
                model=detail["model"],
                year=detail["year"],
                description=detail["description"],
                part_type=part_type_text,
                time_ago=ago,
                count=len(detail["offers"]),
            ),
            "",
        ]
        offer_btns = []
        for i, offer in enumerate(detail["offers"], 1):
            currency_label = t(f"currency_{offer['currency']}_label", lang)
            avail_label = t(f"availability_{offer['availability']}", lang)
            price_formatted = f"{offer['price']:,}".replace(",", " ")
            lines.append(
                t(
                    "offer_line",
                    lang,
                    num=i,
                    seller_name=offer["seller_name"],
                    price=price_formatted,
                    currency=currency_label,
                    availability=avail_label,
                )
            )
            offer_btns.append((offer["id"], offer["seller_name"]))

        keyboard = request_detail_keyboard(offer_btns, request_id, lang)
    else:
        lines = [
            t(
                "request_detail_no_offers",
                lang,
                brand=detail["brand"],
                model=detail["model"],
                year=detail["year"],
                description=detail["description"],
                part_type=part_type_text,
                time_ago=ago,
            )
        ]
        keyboard = request_detail_keyboard([], request_id, lang)

    await callback.message.edit_text("\n".join(lines), reply_markup=keyboard)
    await callback.answer()


# --- Contact seller ---
@router.callback_query(F.data.startswith("contact:"))
async def on_contact_seller(callback: CallbackQuery):
    offer_id = int(callback.data.split(":")[1])
    _, lang = await _get_user_lang(callback.from_user.id)

    async with async_session() as session:
        offer_data = await get_offer_with_seller(session, offer_id)

    if not offer_data:
        await callback.answer()
        return

    if offer_data["seller_username"]:
        tg_link = t("tg_link_username", lang, username=offer_data["seller_username"])
    else:
        tg_link = t(
            "tg_link_deeplink", lang, user_id=offer_data["seller_telegram_id"]
        )

    phone = offer_data["seller_phone"] or "—"
    text = t(
        "seller_contacts",
        lang,
        seller_name=offer_data["seller_name"],
        telegram_link=tg_link,
        phone=phone,
    )
    await callback.message.answer(text)
    await callback.answer()


# --- Close request ---
@router.callback_query(F.data.startswith("close_request:"))
async def on_close_request(callback: CallbackQuery):
    request_id = int(callback.data.split(":")[1])
    _, lang = await _get_user_lang(callback.from_user.id)

    async with async_session() as session:
        closed = await close_request(session, request_id)

    if closed:
        await callback.message.edit_text(
            t("request_closed", lang, request_id=request_id)
        )
    await callback.answer()
