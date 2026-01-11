from datetime import timedelta, datetime
from typing import Sequence
from uuid import UUID
from sqlalchemy import select, delete, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.ride import RideOffer, RideRequest, CarPhoto
from app.representations.dtos.ride import (
    CreateRideOfferDTO, CreateRideRequestDTO
)


class RideOfferRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, driver_id: UUID, dto: CreateRideOfferDTO) -> RideOffer:
        ride_offer = RideOffer(
            driver_id=driver_id,
            request_source=dto.request_source,
            travel_start_date=dto.travel_start_date,
            travel_start_time=dto.travel_start_time,
            start_location=dto.start_location.lower().strip(),
            end_location=dto.end_location.lower().strip(),
            car_model=dto.car_model,
            total_seat_amount=dto.total_seat_amount,
            free_seats=dto.free_seats
        )
        self.session.add(ride_offer)
        await self.session.flush()
        return ride_offer

    async def get_by_id(self, offer_id: UUID) -> RideOffer | None:
        return await self.session.get(RideOffer, offer_id)

    async def get_all(self) -> Sequence[RideOffer]:
        query = select(RideOffer).order_by(RideOffer.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_driver(self, driver_id: UUID) -> Sequence[RideOffer]:
        query = select(RideOffer).where(RideOffer.driver_id == driver_id).order_by(RideOffer.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete(self, ride_offer: RideOffer) -> None:
        await self.session.delete(ride_offer)
        await self.session.flush()

    async def search_offers(
        self,
        start_location: str,
        end_location: str,
        seats_needed: int,
        start_date: str, # string or date
        limit: int = 10,
        offset: int = 0
    ) -> Sequence[RideOffer]:
        # Calculate Date Window (+2 days)
        if isinstance(start_date, str):
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_date_obj = start_date
            
        end_date_limit = start_date_obj + timedelta(hours=4)

        query = select(RideOffer).where(
            RideOffer.start_location == start_location.lower().strip(),
            RideOffer.end_location == end_location.lower().strip(),
            RideOffer.free_seats >= seats_needed,
            RideOffer.travel_start_date >= start_date,
            RideOffer.travel_start_date <= end_date_limit
        ).order_by(
            RideOffer.travel_start_date.asc(),
            RideOffer.travel_start_time.asc()
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class RideRequestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, passenger_id: UUID, dto: CreateRideRequestDTO) -> RideRequest:
        ride_request = RideRequest(
            passenger_id=passenger_id,
            request_source=dto.request_source,
            travel_start_date=dto.travel_start_date,
            travel_start_time=dto.travel_start_time,
            start_location=dto.start_location.lower().strip(),
            end_location=dto.end_location.lower().strip(),
            seat_amount=dto.seat_amount
        )
        self.session.add(ride_request)
        await self.session.flush()
        return ride_request

    async def get_by_id(self, request_id: UUID) -> RideRequest | None:
        return await self.session.get(RideRequest, request_id)

    async def get_all(self) -> Sequence[RideRequest]:
        query = select(RideRequest).order_by(RideRequest.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_passenger(self, passenger_id: UUID) -> Sequence[RideRequest]:
        query = select(RideRequest).where(RideRequest.passenger_id == passenger_id).order_by(RideRequest.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def search_requests(
        self,
        start_location: str,
        end_location: str,
        start_date: str,
        limit: int = 10,
        offset: int = 0
    ) -> Sequence[RideRequest]:
        # Calculate Date Window (+2 days)
        if isinstance(start_date, str):
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_date_obj = start_date
            
        end_date_limit = start_date_obj + timedelta(days=2)

        query = select(RideRequest).where(
            RideRequest.start_location == start_location.lower().strip(),
            RideRequest.end_location == end_location.lower().strip(),
            RideRequest.travel_start_date >= start_date,
            RideRequest.travel_start_date <= end_date_limit
        ).order_by(
            RideRequest.travel_start_date.asc(),
            RideRequest.travel_start_time.asc()
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
        
    async def delete(self, ride_request: RideRequest) -> None:
        await self.session.delete(ride_request)
        await self.session.flush()


class CarPhotoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, driver_id: UUID, url: str) -> CarPhoto:
        photo = CarPhoto(
            driver_id=driver_id,
            url=url
        )
        self.session.add(photo)
        await self.session.flush()
        return photo

    async def get_by_driver(self, driver_id: UUID) -> Sequence[CarPhoto]:
        query = select(CarPhoto).where(CarPhoto.driver_id == driver_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, photo_id: UUID) -> CarPhoto | None:
        return await self.session.get(CarPhoto, photo_id)
        
    async def delete(self, photo: CarPhoto) -> None:
        await self.session.delete(photo)
        await self.session.flush()
