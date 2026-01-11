from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.connections.database.session import get_session
from app.infrastructure.repositories.user import UserRepository, TelegramUserRepository
from app.infrastructure.repositories.ride import RideOfferRepository, RideRequestRepository, CarPhotoRepository
from app.services.user_service import UserService
from app.services.ride_service import RideService
from app.domain.interfaces.media_service import IMediaService
from app.infrastructure.services.cloudinary import CloudinaryService



async def get_media_service() -> AsyncGenerator[IMediaService, None]:
    service = CloudinaryService()
    try:
        yield service
    finally:
        await service.close()


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)


async def get_telegram_user_repository(
    session: AsyncSession = Depends(get_session),
) -> TelegramUserRepository:
    return TelegramUserRepository(session)


async def get_ride_offer_repository(
    session: AsyncSession = Depends(get_session),
) -> RideOfferRepository:
    return RideOfferRepository(session)


async def get_ride_request_repository(
    session: AsyncSession = Depends(get_session),
) -> RideRequestRepository:
    return RideRequestRepository(session)


async def get_car_photo_repository(
    session: AsyncSession = Depends(get_session),
) -> CarPhotoRepository:
    return CarPhotoRepository(session)


async def get_user_service(
    session: AsyncSession = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
    telegram_user_repo: TelegramUserRepository = Depends(get_telegram_user_repository),
) -> UserService:
    return UserService(
        session=session,
        user_repo=user_repo,
        telegram_user_repo=telegram_user_repo,
    )


async def get_ride_service(
    session: AsyncSession = Depends(get_session),
    offer_repo: RideOfferRepository = Depends(get_ride_offer_repository),
    request_repo: RideRequestRepository = Depends(get_ride_request_repository),
    photo_repo: CarPhotoRepository = Depends(get_car_photo_repository),
    media_service: IMediaService = Depends(get_media_service),
) -> RideService:
    return RideService(
        session=session,
        offer_repo=offer_repo,
        request_repo=request_repo,
        photo_repo=photo_repo,
        media_service=media_service,
    )


