import pathlib

from aiogram.types import FSInputFile, InputMediaPhoto
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.db.engine import async_session
from bot.db.models import (
    Request,
    RequestPhoto,
    SellerBrand,
    User,
)
from bot.keyboards.inline import request_notification_keyboard
from bot.locales import t

UPLOADS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "uploads"


async def notify_sellers(request_id: int) -> int:
    """Send notification to sellers matching the request brand.
    Returns the number of sellers notified.
    """
    from bot.loader import bot

    async with async_session() as session:
        # Load request with photos
        result = await session.execute(
            select(Request)
            .options(selectinload(Request.photos), selectinload(Request.client))
            .where(Request.id == request_id)
        )
        req = result.scalar_one_or_none()
        if not req:
            return 0

        # Find sellers for this brand
        result = await session.execute(
            select(User)
            .join(SellerBrand, SellerBrand.seller_id == User.id)
            .where(SellerBrand.brand == req.brand)
        )
        sellers = result.scalars().all()

        # Send confirmation to client
        client = req.client
        lang = client.language.value if client.language else "ru"
        part_type_text = t(f"part_type_{req.part_type.value}", lang)

        if sellers:
            text = t(
                "request_created",
                lang,
                request_id=req.id,
                brand=req.brand,
                model=req.model,
                year=req.year,
                description=req.description,
                part_type=part_type_text,
            )
        else:
            text = t(
                "request_created_no_sellers",
                lang,
                request_id=req.id,
                brand=req.brand,
                model=req.model,
                year=req.year,
                description=req.description,
                part_type=part_type_text,
            )

        await bot.send_message(client.telegram_id, text)

        # Notify each seller
        notified = 0
        for seller in sellers:
            seller_lang = seller.language.value if seller.language else "ru"
            seller_part_type = t(f"part_type_{req.part_type.value}", seller_lang)
            notification_text = t(
                "new_request_notification",
                seller_lang,
                request_id=req.id,
                brand=req.brand,
                model=req.model,
                year=req.year,
                description=req.description,
                part_type=seller_part_type,
            )
            keyboard = request_notification_keyboard(req.id, seller_lang)

            try:
                # Send photos as media group if any
                if req.photos:
                    media = []
                    for photo in req.photos:
                        photo_path = UPLOADS_DIR / photo.file_path
                        if photo_path.exists():
                            media.append(InputMediaPhoto(media=FSInputFile(photo_path)))
                    if media:
                        await bot.send_media_group(seller.telegram_id, media)

                await bot.send_message(
                    seller.telegram_id,
                    notification_text,
                    reply_markup=keyboard,
                )
                notified += 1
            except Exception:
                pass

        return notified
