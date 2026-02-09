from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from sqlalchemy import delete, select

from bot.db.engine import async_session
from bot.db.models import LanguageEnum, RoleEnum, SellerBrand, User
from bot.keyboards.inline import brands_keyboard, language_keyboard, settings_keyboard
from bot.keyboards.reply import client_menu, seller_menu
from bot.locales import t

router = Router()


async def _get_user(telegram_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


# --- Settings menu ---
@router.message(F.text.in_(["⚙️ Настройки", "⚙️ Sozlamalar"]))
async def on_settings(message: Message):
    user = await _get_user(message.from_user.id)
    if not user:
        return
    lang = user.language.value if user.language else "ru"
    is_seller = user.role == RoleEnum.seller
    await message.answer(
        t("settings_title", lang),
        reply_markup=settings_keyboard(is_seller, lang),
    )


# --- Change language ---
@router.callback_query(F.data == "settings:language")
async def on_settings_language(callback: CallbackQuery):
    await callback.message.edit_text(
        t("choose_language_setting"), reply_markup=language_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def on_language_changed(callback: CallbackQuery, state: FSMContext):
    # This also handles language selection during registration (RegistrationState)
    # If there's FSM state active, let the start handler handle it
    current_state = await state.get_state()
    if current_state:
        return  # Let the registration handler process this

    lang = callback.data.split(":")[1]

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await callback.answer()
            return

        user.language = LanguageEnum(lang)
        await session.commit()
        role = user.role

    await callback.message.edit_text(t("language_changed", lang))

    # Update reply keyboard with new language
    if role == RoleEnum.client:
        await callback.message.answer("✅", reply_markup=client_menu(lang))
    elif role == RoleEnum.seller:
        await callback.message.answer("✅", reply_markup=seller_menu(lang))

    await callback.answer()


# --- Change brands (seller only) ---
@router.callback_query(F.data == "settings:brands")
async def on_settings_brands(callback: CallbackQuery, state: FSMContext):
    user = await _get_user(callback.from_user.id)
    if not user or user.role != RoleEnum.seller:
        await callback.answer()
        return

    lang = user.language.value if user.language else "ru"

    # Load current brands
    async with async_session() as session:
        result = await session.execute(
            select(SellerBrand.brand).where(SellerBrand.seller_id == user.id)
        )
        current_brands = {row[0] for row in result.all()}

    await state.set_data({"editing_brands": True, "selected_brands": current_brands, "language": lang})
    await callback.message.edit_text(
        t("choose_brands", lang),
        reply_markup=brands_keyboard(current_brands, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_brand:"))
async def on_brand_toggle_settings(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("editing_brands"):
        return  # Let registration handler handle it

    brand = callback.data.split(":", 1)[1]
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


@router.callback_query(F.data == "brands_done")
async def on_brands_done_settings(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("editing_brands"):
        return  # Let registration handler handle it

    lang = data.get("language", "ru")
    selected: set = data.get("selected_brands", set())

    if not selected:
        await callback.answer(t("select_at_least_one", lang), show_alert=True)
        return

    user = await _get_user(callback.from_user.id)
    if not user:
        await callback.answer()
        return

    async with async_session() as session:
        # Delete old brands
        await session.execute(
            delete(SellerBrand).where(SellerBrand.seller_id == user.id)
        )
        # Add new brands
        for brand in selected:
            session.add(SellerBrand(seller_id=user.id, brand=brand))
        await session.commit()

    await state.clear()
    brands_str = ", ".join(sorted(selected))
    await callback.message.edit_text(t("brands_updated", lang, brands=brands_str))
    await callback.answer()
