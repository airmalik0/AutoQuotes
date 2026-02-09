from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db.models import Offer, Request, RequestStatusEnum


async def get_user_requests(
    session: AsyncSession, user_id: int
) -> list[dict]:
    result = await session.execute(
        select(Request)
        .where(Request.client_id == user_id, Request.status == RequestStatusEnum.active)
        .order_by(Request.created_at.desc())
    )
    requests = result.scalars().all()

    items = []
    for req in requests:
        offer_count_result = await session.execute(
            select(func.count()).select_from(Offer).where(Offer.request_id == req.id)
        )
        offer_count = offer_count_result.scalar() or 0
        items.append(
            {
                "id": req.id,
                "brand": req.brand,
                "model": req.model,
                "year": req.year,
                "description": req.description,
                "offer_count": offer_count,
                "created_at": req.created_at,
            }
        )
    return items


async def get_request_detail(
    session: AsyncSession, request_id: int
) -> dict | None:
    result = await session.execute(
        select(Request)
        .options(selectinload(Request.offers).selectinload(Offer.seller))
        .where(Request.id == request_id)
    )
    req = result.scalar_one_or_none()
    if not req:
        return None

    offers = []
    for offer in req.offers:
        offers.append(
            {
                "id": offer.id,
                "seller_name": offer.seller.first_name or "Seller",
                "seller_telegram_id": offer.seller.telegram_id,
                "seller_username": offer.seller.username,
                "seller_phone": offer.seller.phone_number,
                "price": offer.price,
                "currency": offer.currency.value,
                "availability": offer.availability.value,
                "comment": offer.comment,
            }
        )

    return {
        "id": req.id,
        "brand": req.brand,
        "model": req.model,
        "year": req.year,
        "description": req.description,
        "part_type": req.part_type.value,
        "status": req.status.value,
        "created_at": req.created_at,
        "offers": offers,
    }


async def close_request(session: AsyncSession, request_id: int) -> bool:
    result = await session.execute(
        select(Request).where(Request.id == request_id)
    )
    req = result.scalar_one_or_none()
    if not req or req.status != RequestStatusEnum.active:
        return False
    req.status = RequestStatusEnum.closed
    await session.commit()
    return True


async def expire_old_requests(session: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Request).where(
            Request.status == RequestStatusEnum.active,
            Request.expires_at < now,
        )
    )
    expired = result.scalars().all()
    for req in expired:
        req.status = RequestStatusEnum.expired
    await session.commit()
    return len(expired)
