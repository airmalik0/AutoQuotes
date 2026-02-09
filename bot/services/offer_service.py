from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    AvailabilityEnum,
    CurrencyEnum,
    Offer,
    Request,
    RequestStatusEnum,
    User,
)


async def create_offer(
    session: AsyncSession,
    request_id: int,
    seller_id: int,
    price: int,
    currency: CurrencyEnum,
    availability: AvailabilityEnum,
    comment: str | None = None,
) -> Offer | None:
    # Check request is active
    result = await session.execute(
        select(Request).where(Request.id == request_id)
    )
    req = result.scalar_one_or_none()
    if not req or req.status != RequestStatusEnum.active:
        return None

    # Check seller hasn't already responded
    result = await session.execute(
        select(Offer).where(
            Offer.request_id == request_id, Offer.seller_id == seller_id
        )
    )
    if result.scalar_one_or_none():
        return None

    offer = Offer(
        request_id=request_id,
        seller_id=seller_id,
        price=price,
        currency=currency,
        availability=availability,
        comment=comment,
    )
    session.add(offer)
    await session.commit()
    await session.refresh(offer)
    return offer


async def get_offer_with_seller(
    session: AsyncSession, offer_id: int
) -> dict | None:
    result = await session.execute(
        select(Offer, User)
        .join(User, Offer.seller_id == User.id)
        .where(Offer.id == offer_id)
    )
    row = result.one_or_none()
    if not row:
        return None
    offer, seller = row
    return {
        "id": offer.id,
        "seller_name": seller.first_name or "Seller",
        "seller_telegram_id": seller.telegram_id,
        "seller_username": seller.username,
        "seller_phone": seller.phone_number,
        "price": offer.price,
        "currency": offer.currency.value,
        "availability": offer.availability.value,
        "comment": offer.comment,
    }
