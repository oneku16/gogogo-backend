from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class UserDTO:
    id: UUID
    phone_number: str
    first_name: str | None
    last_name: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateUserDTO:
    phone_number: str
    first_name: str | None = None
    last_name: str | None = None


@dataclass
class TelegramUserDTO:
    id: UUID
    user_id: UUID
    telegram_id: int
    chat_id: int | None
    username: str | None
    language_code: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateTelegramUserDTO:
    telegram_id: int
    chat_id: int | None = None
    user_id: UUID | None = None
    username: str | None = None
    language_code: str | None = None
    phone_number: str | None = None
