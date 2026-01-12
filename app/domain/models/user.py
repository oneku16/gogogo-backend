import uuid

from sqlalchemy import String, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    phone_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str] = mapped_column(String(64), nullable=True)


class TelegramUser(BaseModel):
    __tablename__ = "telegram_users"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), type_=UUID(as_uuid=True), nullable=False, unique=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    username: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    language_code: Mapped[str] = mapped_column(String(64), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=True)
    