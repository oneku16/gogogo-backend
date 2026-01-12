from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    phone_number: str = Field(..., description="User's phone number")
    first_name: str | None = Field(None, description="User's first name")
    last_name: str | None = Field(None, description="User's last name")


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelegramUserBase(BaseModel):
    telegram_id: int = Field(..., description="Telegram User ID")
    username: str | None = Field(None, description="Telegram username")
    chat_id: int | None = Field(None, description="Telegram Chat ID")
    language_code: str | None = Field(None, description="Language code")
    role: str | None = Field(None, description="User role (driver/passenger)")
    language: str | None = Field(None, description="Preferred language")

class TelegramUserUpdate(BaseModel):
     role: str | None = Field(None, description="User role")
     language: str | None = Field(None, description="Preferred language")


class TelegramUserCreate(TelegramUserBase):
    phone_number: str | None = Field(None, description="Phone number for binding to a user")


class TelegramUserLink(TelegramUserBase):
    user_id: UUID = Field(..., description="ID of the user to link the telegram account to")
    language: str | None = Field(None, description="Language code (client alias)")


class TelegramUserRegisterRequest(TelegramUserBase):
    user_id: UUID | None = Field(None, description="ID of the user to link if known")
    phone_number: str | None = Field(None, description="Phone number to find/create user")
    language: str | None = Field(None, description="Language code (client alias)")


class TelegramUserRead(TelegramUserBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
