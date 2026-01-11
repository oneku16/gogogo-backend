from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User, TelegramUser
from app.representations.dtos.user import (
    CreateUserDTO,
    UserDTO,
    CreateTelegramUserDTO,
    TelegramUserDTO,
)
from app.infrastructure.repositories.user import UserRepository, TelegramUserRepository


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        telegram_user_repo: TelegramUserRepository,
    ):
        self.session: AsyncSession = session
        self.user: UserRepository = user_repo
        self.telegram_user: TelegramUserRepository = telegram_user_repo

    async def register_user(self, dto: CreateUserDTO) -> UserDTO:
        existing_user = await self.user.find_by_phone(dto.phone_number)
        if existing_user:
            # Idempotent: Return existing user
            return self._map_to_user_dto(existing_user)

        user = await self.user.create(dto)
        await self.session.commit()
        await self.session.refresh(user)
        return self._map_to_user_dto(user)

    async def register_telegram_user(self, dto: CreateTelegramUserDTO) -> TelegramUserDTO:
        # Check if telegram user already exists
        existing_tg_user = await self.telegram_user.find_by_telegram_id(dto.telegram_id)
        if existing_tg_user:
             raise ValueError(f"Telegram user with ID {dto.telegram_id} already registered.")

        user_id_to_bind = dto.user_id

        # Binding Logic
        if user_id_to_bind:
            # Verify user exists
            user = await self.user.get_by_id(user_id_to_bind)
            if not user:
                raise ValueError(f"User with ID {user_id_to_bind} not found.")
        elif dto.phone_number:
            # Check if user with phone exists
            user = await self.user.find_by_phone(dto.phone_number)
            if user:
                user_id_to_bind = user.id
            else:
                # Create new user implicitly?
                # "2 registration... they will be binded".
                # If Telegram registration provides phone, and user doesn't exist, we probably should create one.
                new_user_dto = CreateUserDTO(
                    phone_number=dto.phone_number,
                    first_name=dto.username, # Default to username or similar
                    last_name=None
                )
                user = await self.user.create(new_user_dto)
                user_id_to_bind = user.id
        else:
             raise ValueError("Either user_id or phone_number must be provided to bind Telegram account.")

        if not user_id_to_bind:
             # Should be covered by above logic, but for safety
             raise ValueError("Failed to determine User ID for binding.")

        # Create Telegram User
        tg_user = await self.telegram_user.create(dto, user_id_to_bind)
        
        await self.session.commit()
        await self.session.refresh(tg_user)
        return self._map_to_telegram_user_dto(tg_user)

    def _map_to_user_dto(self, user: User) -> UserDTO:
        return UserDTO(
            id=user.id,
            phone_number=user.phone_number,
            first_name=user.first_name,
            last_name=user.last_name,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def get_telegram_user_by_id(self, telegram_id: int) -> Optional[TelegramUserDTO]:
        tg_user = await self.telegram_user.find_by_telegram_id(telegram_id)
        if tg_user:
            return self._map_to_telegram_user_dto(tg_user)
        return None

    def _map_to_telegram_user_dto(self, tg_user: TelegramUser) -> TelegramUserDTO:
        return TelegramUserDTO(
            id=tg_user.id,
            user_id=tg_user.user_id,
            telegram_id=tg_user.telegram_id,
            username=tg_user.username,
            language_code=tg_user.language_code,
            created_at=tg_user.created_at,
            updated_at=tg_user.updated_at
        )
