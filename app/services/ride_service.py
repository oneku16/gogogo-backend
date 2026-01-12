import uuid
from typing import Sequence, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.ride import RideOffer, RideRequest, CarPhoto
from app.representations.dtos.ride import (
    CreateRideOfferDTO, CreateRideRequestDTO, RideOfferDTO, RideRequestDTO, CarPhotoDTO, UpdateRideRequestDTO, UpdateRideOfferDTO,
    RideOfferSearchDTO, RideRequestSearchDTO
)
from app.infrastructure.repositories.ride import (
    RideOfferRepository, RideRequestRepository, CarPhotoRepository
)
from app.domain.interfaces.media_service import IMediaService
from app.utils.normalization import normalize_location


class RideService:
    def __init__(
        self,
        session: AsyncSession,
        offer_repo: RideOfferRepository,
        request_repo: RideRequestRepository,
        photo_repo: CarPhotoRepository,
        media_service: IMediaService
    ):
        self.session = session
        self.offer_repo = offer_repo
        self.request_repo = request_repo
        self.photo_repo = photo_repo
        self.media_service = media_service

    # --- Ride Offers ---

    async def create_ride_offer(self, driver_id: uuid.UUID, dto: CreateRideOfferDTO) -> RideOfferDTO:
        # Normalize locations
        dto.start_location = normalize_location(dto.start_location)
        dto.end_location = normalize_location(dto.end_location)
        
        offer = await self.offer_repo.create(driver_id, dto)
        await self.session.commit()
        await self.session.refresh(offer)
        
        # Trigger Celery Task
        print(f"Attempting to trigger process_ride_offer for {offer.id}")
        try:
            from app.services.tasks import process_ride_offer
            print(f"Imported process_ride_offer: {process_ride_offer}")
            result = process_ride_offer.delay(str(offer.id))
            print(f"Task triggered. Result ID: {result.id}")
        except Exception as e:
            # Log error but don't fail request
            print(f"Failed to trigger task: {e}")
            import traceback
            traceback.print_exc()

        return RideOfferDTO.model_validate(offer)

    async def get_ride_offers(self) -> List[RideOfferDTO]:
        offers = await self.offer_repo.get_all()
        return [RideOfferDTO.model_validate(o) for o in offers]

    async def get_driver_offers(self, driver_id: uuid.UUID) -> List[RideOfferDTO]:
        offers = await self.offer_repo.get_by_driver(driver_id)
        return [RideOfferDTO.model_validate(o) for o in offers]
    
    async def delete_ride_offer(self, offer_id: uuid.UUID, driver_id: uuid.UUID) -> None:
        offer = await self.offer_repo.get_by_id(offer_id)
        if not offer:
            raise ValueError("Ride offer not found")
        if offer.driver_id != driver_id:
            raise ValueError("Not authorized to delete this offer")
        await self.offer_repo.delete(offer)
        await self.session.commit()

    async def search_ride_offers(self, dto: RideOfferSearchDTO) -> List[RideOfferDTO]:
        start = normalize_location(dto.start_location) if dto.start_location else None
        end = normalize_location(dto.end_location) if dto.end_location else None
        
        offers = await self.offer_repo.search_offers(
            start_location=start,
            end_location=end,
            seats_needed=dto.seats_needed,
            start_date=dto.start_time,
            limit=dto.limit,
            offset=dto.offset
        )
        return [RideOfferDTO.model_validate(o) for o in offers]

    # --- Ride Requests ---

    async def create_ride_request(self, passenger_id: uuid.UUID, dto: CreateRideRequestDTO) -> RideRequestDTO:
        # Normalize locations
        dto.start_location = normalize_location(dto.start_location)
        dto.end_location = normalize_location(dto.end_location)

        request = await self.request_repo.create(passenger_id, dto)
        await self.session.commit()
        await self.session.refresh(request)

        # Trigger Celery Task
        print(f"Attempting to trigger process_ride_request for {request.id}")
        try:
            from app.services.tasks import process_ride_request
            print(f"Imported process_ride_request: {process_ride_request}")
            result = process_ride_request.delay(str(request.id))
            print(f"Task triggered. Result ID: {result.id}")
        except Exception as e:
            print(f"Failed to trigger task: {e}")
            import traceback
            traceback.print_exc()

        return RideRequestDTO.model_validate(request)

    async def get_ride_requests(self) -> List[RideRequestDTO]:
        requests = await self.request_repo.get_all()
        return [RideRequestDTO.model_validate(r) for r in requests]
    
    async def get_passenger_requests(self, passenger_id: uuid.UUID) -> List[RideRequestDTO]:
        requests = await self.request_repo.get_by_passenger(passenger_id)
        return [RideRequestDTO.model_validate(r) for r in requests]

    async def delete_ride_request(self, request_id: uuid.UUID, passenger_id: uuid.UUID) -> None:
        request = await self.request_repo.get_by_id(request_id)
        if not request:
            raise ValueError("Ride request not found")
        if request.passenger_id != passenger_id:
            raise ValueError("Not authorized to delete this request")
        await self.request_repo.delete(request)
        await self.session.commit()

    async def search_ride_requests(self, dto: RideRequestSearchDTO) -> List[RideRequestDTO]:
        start = normalize_location(dto.start_location) if dto.start_location else None
        end = normalize_location(dto.end_location) if dto.end_location else None

        requests = await self.request_repo.search_requests(
            start_location=start,
            end_location=end,
            start_date=dto.start_time,
            limit=dto.limit,
            offset=dto.offset
        )
        return [RideRequestDTO.model_validate(r) for r in requests]

    # --- Car Photos ---

    async def upload_car_photo(self, driver_id: uuid.UUID, file_bytes: bytes) -> CarPhotoDTO:
        # Generate a unique public_id for Cloudinary
        public_id = f"car_photos/{driver_id}/{uuid.uuid4()}"
        
        # Upload to Media Service
        result = await self.media_service.upload_file(public_id, file_bytes)
        url = result.get("url") or result.get("secure_url")
        
        if not url:
            raise RuntimeError("Failed to get URL from media service")

        # Save to DB
        photo = await self.photo_repo.create(driver_id, url)
        await self.session.commit()
        await self.session.refresh(photo)
        return CarPhotoDTO.model_validate(photo)

    async def get_driver_photos(self, driver_id: uuid.UUID) -> List[CarPhotoDTO]:
        photos = await self.photo_repo.get_by_driver(driver_id)
        return [CarPhotoDTO.model_validate(p) for p in photos]
    
    async def delete_car_photo(self, photo_id: uuid.UUID, driver_id: uuid.UUID) -> None:
        photo = await self.photo_repo.get_by_id(photo_id)
        if not photo:
             raise ValueError("Photo not found")
        if photo.driver_id != driver_id:
             raise ValueError("Not authorized to delete this photo")
        
        # Ideally we should also delete from Cloudinary, but IMediaService doesn't have delete yet.
        # For now, just remove from DB.
        await self.photo_repo.delete(photo)
        await self.session.commit()
