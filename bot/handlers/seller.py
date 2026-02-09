from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.db.engine import async_session
from bot.db.models import (
    AvailabilityEnum,
    CurrencyEnum,
    Offer,
    Request,
    RequestStatusEnum,
    SellerBrand,
    User,
)
from bot.keyboards.inline import (
    availability_keyboard,
    contact_seller_keyboard,
    currency_keyboard,
    seller_active_requests_keyboard,
    skip_comment_keyboard,
)
from bot.locales import t
from bot.services.offer_service import create_offer
from bot.states import SellerResponseState

router = Router()


async def _get_user_lang(telegram_id: int) -> tuple[User | None, str]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        lang = user.language.value if user and user.language else "ru"
        return user, lang


# --- "Ответить ценой" ---
@router.callback_query(F.data.startswith("respond:"))
async def on_respond_price(callback: CallbackQuery, state: FSMContext):
    request_id = int(callback.data.split(":")[1])
    user, lang = await _get_user_lang(callback.from_user.id)
    if not user:
        await callback.answer()
        return

    async with async_session() as session:
        # Check request is active
        result = await session.execute(
            select(Request).where(Request.id == request_id)
        )
        req = result.scalar_one_or_none()
        if not req or req.status != RequestStatusEnum.active:
            await callback.answer(t("request_not_active", lang), show_alert=True)
            return

        # Check not already responded
        result = await session.execute(
            select(Offer).where(
                Offer.request_id == request_id, Offer.seller_id == user.id
            )
        )
        if result.scalar_one_or_none():
            await callback.answer(t("already_responded", lang), show_alert=True)
            return

    await state.set_state(SellerResponseState.waiting_price)
    await state.update_data(request_id=request_id)
    await callback.message.answer(t("enter_price", lang))
    await callback.answer()


@router.message(SellerResponseState.waiting_price)
async def on_price_entered(message: Message, state: FSMContext):
    _, lang = await _get_user_lang(message.from_user.id)

    text = message.text.strip() if message.text else ""
    if not text.isdigit() or int(text) <= 0:
        await message.answer(t("invalid_price", lang))
        return

    await state.update_data(price=int(text))
    await state.set_state(SellerResponseState.waiting_currency)
    await message.answer(t("choose_currency", lang), reply_markup=currency_keyboard(lang))


@router.callback_query(
    SellerResponseState.waiting_currency, F.data.startswith("currency:")
)
async def on_currency_chosen(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split(":")[1]
    _, lang = await _get_user_lang(callback.from_user.id)

    await state.update_data(currency=currency)
    await state.set_state(SellerResponseState.waiting_availability)
    await callback.message.edit_text(
        t("choose_availability", lang), reply_markup=availability_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(
    SellerResponseState.waiting_availability, F.data.startswith("availability:")
)
async def on_availability_chosen(callback: CallbackQuery, state: FSMContext):
    availability = callback.data.split(":")[1]
    _, lang = await _get_user_lang(callback.from_user.id)

    await state.update_data(availability=availability)
    await state.set_state(SellerResponseState.waiting_comment)
    await callback.message.edit_text(
        t("enter_comment", lang), reply_markup=skip_comment_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(SellerResponseState.waiting_comment, F.data == "skip_comment")
async def on_skip_comment(callback: CallbackQuery, state: FSMContext):
    await _save_offer(callback.from_user.id, state, comment=None)
    await callback.answer()


@router.message(SellerResponseState.waiting_comment)
async def on_comment_entered(message: Message, state: FSMContext):
    await _save_offer(message.from_user.id, state, comment=message.text)


async def _save_offer(
    telegram_id: int, state: FSMContext, comment: str | None
):
    from bot.loader import bot

    data = await state.get_data()
    await state.clear()

    user, lang = await _get_user_lang(telegram_id)
    if not user:
        return

    async with async_session() as session:
        offer = await create_offer(
            session=session,
            request_id=data["request_id"],
            seller_id=user.id,
            price=data["price"],
            currency=CurrencyEnum(data["currency"]),
            availability=AvailabilityEnum(data["availability"]),
            comment=comment,
        )

        if not offer:
            await bot.send_message(telegram_id, t("already_responded", lang))
            return

        # Format offer confirmation for seller
        currency_label = t(f"currency_{offer.currency.value}_label", lang)
        availability_label = t(f"availability_{offer.availability.value}", lang)
        comment_line = f"💬 {comment}" if comment else ""
        price_formatted = f"{offer.price:,}".replace(",", " ")

        await bot.send_message(
            telegram_id,
            t(
                "offer_sent",
                lang,
                price=price_formatted,
                currency=currency_label,
                availability=availability_label,
                comment_line=comment_line,
            ),
        )

        # Notify client about the new offer
        result = await session.execute(
            select(Request)
            .options(selectinload(Request.client))
            .where(Request.id == data["request_id"])
        )
        req = result.scalar_one_or_none()
        if req and req.client:
            client = req.client
            client_lang = client.language.value if client.language else "ru"
            client_currency = t(f"currency_{offer.currency.value}_label", client_lang)
            client_availability = t(
                f"availability_{offer.availability.value}", client_lang
            )
            client_comment_line = f"💬 {comment}" if comment else ""
            client_price = f"{offer.price:,}".replace(",", " ")

            notification_text = t(
                "new_offer",
                client_lang,
                request_id=req.id,
                brand=req.brand,
                model=req.model,
                year=req.year,
                description=req.description,
                seller_name=user.first_name or "Seller",
                price=client_price,
                currency=client_currency,
                availability=client_availability,
                comment_line=client_comment_line,
            )

            await bot.send_message(
                client.telegram_id,
                notification_text,
                reply_markup=contact_seller_keyboard(offer.id, client_lang),
            )


# --- "Пропустить" ---
@router.callback_query(F.data.startswith("skip:"))
async def on_skip_request(callback: CallbackQuery):
    _, lang = await _get_user_lang(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply(t("skipped", lang))
    await callback.answer()


# --- "Активные запросы" ---
@router.message(F.text.in_(["📋 Активные запросы", "📋 Faol so'rovlar"]))
async def on_active_requests(message: Message):
    user, lang = await _get_user_lang(message.from_user.id)
    if not user:
        return

    async with async_session() as session:
        # Get seller's brands
        result = await session.execute(
            select(SellerBrand.brand).where(SellerBrand.seller_id == user.id)
        )
        brands = [row[0] for row in result.all()]

        if not brands:
            await message.answer(t("no_seller_requests", lang))
            return

        # Get active requests for those brands not already answered
        from sqlalchemy import and_, not_, exists

        answered_subq = (
            select(Offer.id)
            .where(
                and_(Offer.request_id == Request.id, Offer.seller_id == user.id)
            )
            .correlate(Request)
            .exists()
        )

        result = await session.execute(
            select(Request)
            .where(
                Request.brand.in_(brands),
                Request.status == RequestStatusEnum.active,
                ~answered_subq,
            )
            .order_by(Request.created_at.desc())
        )
        requests = result.scalars().all()

    if not requests:
        await message.answer(t("no_seller_requests", lang))
        return

    from bot.services._helpers import time_ago

    lines = [t("seller_requests_list", lang), ""]
    req_list = []
    for i, req in enumerate(requests, 1):
        part_type_text = t(f"part_type_{req.part_type.value}", lang)
        ago = time_ago(req.created_at, lang)
        lines.append(
            t(
                "seller_request_item",
                lang,
                num=i,
                brand=req.brand,
                model=req.model,
                year=req.year,
                description=req.description,
                part_type=part_type_text,
                time_ago=ago,
            )
        )
        req_list.append((req.id, i))

    keyboard = seller_active_requests_keyboard(req_list, lang)
    await message.answer("\n".join(lines), reply_markup=keyboard)
