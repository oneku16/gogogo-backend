from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User, TelegramUser
from app.representations.dtos.user import CreateUserDTO, CreateTelegramUserDTO


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_phone(self, phone_number: str) -> User | None:
        query = select(User).where(User.phone_number == phone_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_dto: CreateUserDTO) -> User:
        user = User(
            phone_number=user_dto.phone_number,
            first_name=user_dto.first_name,
            last_name=user_dto.last_name,
        )
        self.session.add(user)
        await self.session.flush() # Flush to get ID, commit should be handled by service
        return user

class TelegramUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_telegram_id(self, telegram_id: int) -> TelegramUser | None:
        query = select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def find_by_user_id(self, user_id: UUID) -> TelegramUser | None:
        query = select(TelegramUser).where(TelegramUser.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, telegram_user_dto: CreateTelegramUserDTO, user_id: UUID) -> TelegramUser:
        telegram_user = TelegramUser(
            user_id=user_id,
            telegram_id=telegram_user_dto.telegram_id,
            chat_id=telegram_user_dto.chat_id,
            username=telegram_user_dto.username,
            language_code=telegram_user_dto.language_code,
            role=telegram_user_dto.role,
            language=telegram_user_dto.language,
        )
        self.session.add(telegram_user)
        # Flush or let commit handle it. 
        # Since we might need the object immediately, flush is safe.
        await self.session.flush() 
        return telegram_user
