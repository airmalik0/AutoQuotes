from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.engine import async_session
from bot.db.models import LanguageEnum, RoleEnum, SellerBrand, User
from bot.keyboards.inline import brands_keyboard, language_keyboard, role_keyboard
from bot.keyboards.reply import client_menu, contact_keyboard, seller_menu
from bot.locales import t
from bot.states import RegistrationState

from sqlalchemy import select

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    # Check if user already registered
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if user and user.role:
        lang = user.language.value if user.language else "ru"
        if user.role == RoleEnum.client:
            await message.answer(
                t("client_registered", lang), reply_markup=client_menu(lang)
            )
        else:
            async with async_session() as session:
                result = await session.execute(
                    select(SellerBrand.brand).where(SellerBrand.seller_id == user.id)
                )
                brands = [row[0] for row in result.all()]
            await message.answer(
                t("seller_registered", lang, brands=", ".join(brands)),
                reply_markup=seller_menu(lang),
            )
        return

    await state.set_state(RegistrationState.waiting_language)
    await message.answer(
        t("choose_language"), reply_markup=language_keyboard()
    )


@router.callback_query(RegistrationState.waiting_language, F.data.startswith("lang:"))
async def on_language_chosen(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    await state.update_data(language=lang)

    # Create or update user with language
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                language=LanguageEnum(lang),
            )
            session.add(user)
        else:
            user.language = LanguageEnum(lang)
        await session.commit()

    await state.set_state(RegistrationState.waiting_contact)
    await callback.message.edit_text(t("choose_language") + " ✅")
    await callback.message.answer(
        t("share_contact", lang), reply_markup=contact_keyboard(lang)
    )
    await callback.answer()


@router.message(RegistrationState.waiting_contact, F.contact)
async def on_contact_shared(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "ru")

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.phone_number = message.contact.phone_number
            user.first_name = message.contact.first_name or message.from_user.first_name
            user.username = message.from_user.username
            await session.commit()

    first_name = message.contact.first_name or message.from_user.first_name or ""
    await state.update_data(first_name=first_name)
    await state.set_state(RegistrationState.waiting_role)
    await message.answer(
        t("choose_role", lang, first_name=first_name),
        reply_markup=role_keyboard(lang),
    )


@router.callback_query(RegistrationState.waiting_role, F.data.startswith("role:"))
async def on_role_chosen(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("language", "ru")

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.role = RoleEnum(role)
            await session.commit()

    if role == "client":
        await state.clear()
        await callback.message.edit_text(t("choose_role", lang, first_name=data.get("first_name", "")) + " ✅")
        await callback.message.answer(
            t("client_registered", lang), reply_markup=client_menu(lang)
        )
    else:
        await state.set_state(RegistrationState.waiting_brands)
        await state.update_data(selected_brands=set())
        await callback.message.edit_text(
            t("choose_brands", lang), reply_markup=brands_keyboard(set(), lang)
        )
    await callback.answer()


@router.callback_query(
    RegistrationState.waiting_brands, F.data.startswith("toggle_brand:")
)
async def on_brand_toggle(callback: CallbackQuery, state: FSMContext):
    brand = callback.data.split(":", 1)[1]
    data = await state.get_data()
    lang = data.get("language", "ru")
    selected: set = data.get("selected_brands", set())

    if brand in selected:
        selected.discard(brand)
    else:
        selected.add(brand)

    await state.update_data(selected_brands=selected)
    await callback.message.edit_reply_markup(
        reply_markup=brands_keyboard(selected, lang)
    )
    await callback.answer()


@router.callback_query(RegistrationState.waiting_brands, F.data == "brands_done")
async def on_brands_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "ru")
    selected: set = data.get("selected_brands", set())

    if not selected:
        await callback.answer(t("select_at_least_one", lang), show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            for brand in selected:
                session.add(SellerBrand(seller_id=user.id, brand=brand))
            await session.commit()

    await state.clear()
    brands_str = ", ".join(sorted(selected))
    await callback.message.edit_text(t("choose_brands", lang) + " ✅")
    await callback.message.answer(
        t("seller_registered", lang, brands=brands_str),
        reply_markup=seller_menu(lang),
    )
    await callback.answer()
