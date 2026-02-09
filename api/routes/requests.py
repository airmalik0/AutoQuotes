import logging
import pathlib

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, Request as FastAPIRequest, UploadFile

from api.auth import validate_init_data
from bot.config import settings
from bot.db.engine import async_session
from bot.db.models import (
    PartTypeEnum,
    Request,
    RequestPhoto,
    RequestStatusEnum,
    RoleEnum,
    User,
)

from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOADS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "uploads"


@router.post("/api/requests")
async def create_request(
    brand: str = Form(...),
    model: str = Form(...),
    year: int = Form(...),
    description: str = Form(...),
    part_type: str = Form(...),
    init_data: str = Form(default=""),
    photos: list[UploadFile] | None = File(default=None),
):
    photos = photos or []
    logger.info("Received request: brand=%s model=%s year=%s part_type=%s init_data_len=%d photos=%d",
                brand, model, year, part_type, len(init_data), len(photos))

    # Validate init_data
    if not init_data:
        raise HTTPException(status_code=403, detail="Empty init_data")

    user_data = validate_init_data(init_data, settings.BOT_TOKEN)
    if user_data is None:
        logger.error("Invalid init_data (len=%d): %s", len(init_data), init_data[:200])
        raise HTTPException(status_code=403, detail="Invalid init_data")

    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(status_code=403, detail="No user id in init_data")

    # Validate part_type
    try:
        pt = PartTypeEnum(part_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid part_type")

    async with async_session() as session:
        # Check user exists and is client
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != RoleEnum.client:
            raise HTTPException(status_code=403, detail="User not found or not a client")

        # Create request
        req = Request(
            client_id=user.id,
            brand=brand,
            model=model,
            year=year,
            description=description,
            part_type=pt,
            status=RequestStatusEnum.active,
        )
        session.add(req)
        await session.flush()

        # Save photos (up to 3)
        photo_files = photos[:3]
        req_dir = UPLOADS_DIR / str(req.id)
        if photo_files:
            req_dir.mkdir(parents=True, exist_ok=True)

        for i, photo in enumerate(photo_files):
            if not photo.filename:
                continue
            ext = pathlib.Path(photo.filename).suffix or ".jpg"
            file_name = f"{i + 1}{ext}"
            file_path = req_dir / file_name

            async with aiofiles.open(file_path, "wb") as f:
                content = await photo.read()
                await f.write(content)

            rp = RequestPhoto(
                request_id=req.id, file_path=str(file_path.relative_to(UPLOADS_DIR))
            )
            session.add(rp)

        await session.commit()
        request_id = req.id

    # Notify sellers (import here to avoid circular imports at module level)
    from bot.services.notification import notify_sellers

    await notify_sellers(request_id)

    return {"ok": True, "request_id": request_id}
