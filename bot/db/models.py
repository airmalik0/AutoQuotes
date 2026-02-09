import enum
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RoleEnum(str, enum.Enum):
    client = "client"
    seller = "seller"


class LanguageEnum(str, enum.Enum):
    ru = "ru"
    uz = "uz"


class PartTypeEnum(str, enum.Enum):
    original = "original"
    duplicate = "duplicate"
    used = "used"


class RequestStatusEnum(str, enum.Enum):
    active = "active"
    closed = "closed"
    expired = "expired"


class CurrencyEnum(str, enum.Enum):
    sum = "sum"
    usd = "usd"


class AvailabilityEnum(str, enum.Enum):
    in_stock = "in_stock"
    order_1_3 = "order_1_3"
    order_3_7 = "order_3_7"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String)
    first_name: Mapped[str | None] = mapped_column(String)
    username: Mapped[str | None] = mapped_column(String)
    role: Mapped[RoleEnum | None] = mapped_column(Enum(RoleEnum))
    language: Mapped[LanguageEnum] = mapped_column(
        Enum(LanguageEnum), default=LanguageEnum.ru
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    seller_brands: Mapped[list["SellerBrand"]] = relationship(
        back_populates="seller", cascade="all, delete-orphan"
    )
    requests: Mapped[list["Request"]] = relationship(back_populates="client")
    offers: Mapped[list["Offer"]] = relationship(back_populates="seller")


class SellerBrand(Base):
    __tablename__ = "seller_brands"
    __table_args__ = (UniqueConstraint("seller_id", "brand"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    brand: Mapped[str] = mapped_column(String, nullable=False)

    seller: Mapped["User"] = relationship(back_populates="seller_brands")


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    brand: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    part_type: Mapped[PartTypeEnum] = mapped_column(Enum(PartTypeEnum), nullable=False)
    status: Mapped[RequestStatusEnum] = mapped_column(
        Enum(RequestStatusEnum), default=RequestStatusEnum.active
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc) + timedelta(hours=48)
    )

    client: Mapped["User"] = relationship(back_populates="requests")
    photos: Mapped[list["RequestPhoto"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
    offers: Mapped[list["Offer"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class RequestPhoto(Base):
    __tablename__ = "request_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("requests.id", ondelete="CASCADE")
    )
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    request: Mapped["Request"] = relationship(back_populates="photos")


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (UniqueConstraint("request_id", "seller_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(Enum(CurrencyEnum), nullable=False)
    availability: Mapped[AvailabilityEnum] = mapped_column(
        Enum(AvailabilityEnum), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    request: Mapped["Request"] = relationship(back_populates="offers")
    seller: Mapped["User"] = relationship(back_populates="offers")
