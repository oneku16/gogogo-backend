from fastapi import APIRouter, Depends, HTTPException, status

from app.infrastructure.dependencies.providers import get_user_service
from app.representations.dtos.user import CreateTelegramUserDTO
from app.representations.schemas.user import TelegramUserLink, TelegramUserRead, TelegramUserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/", response_model=TelegramUserRead, status_code=status.HTTP_201_CREATED)
async def create_telegram_user(
    link_data: TelegramUserLink,
    service: UserService = Depends(get_user_service),
):
    """
    Register a Telegram account and link it to an existing User.
    """
    # Map Schema to DTO
    lang = link_data.language or link_data.language_code
    
    dto = CreateTelegramUserDTO(
        telegram_id=link_data.telegram_id,
        chat_id=link_data.chat_id,
        user_id=link_data.user_id,
        username=link_data.username,
        language_code=lang, # Telegram language code
        language=link_data.language, # User selected language
        role=link_data.role,
        phone_number=None, # Not used in this flow
    )

    try:
        tg_user_dto = await service.register_telegram_user(dto)
        return tg_user_dto
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{telegram_id}", response_model=TelegramUserRead)
async def get_telegram_user(
    telegram_id: int,
    service: UserService = Depends(get_user_service),
):
    tg_user = await service.get_telegram_user_by_id(telegram_id)
    if not tg_user:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telegram user not found")
    return tg_user


@router.patch("/{telegram_id}", response_model=TelegramUserRead)
async def update_telegram_user(
    telegram_id: int,
    update_data: TelegramUserUpdate,
    service: UserService = Depends(get_user_service),
):
    try:
        return await service.update_telegram_user(telegram_id, role=update_data.role, language=update_data.language)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
