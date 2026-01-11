import uuid
import enum
from datetime import date, time
from typing import List

from sqlalchemy import String, Integer, Date, Time, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel


class RequestSource(enum.Enum):
    telegram_app = "telegram_app"
    mobile_app = "mobile_app"


class CarPhoto(BaseModel):
    __tablename__ = "car_photos"

    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), type_=UUID(as_uuid=True), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)


class RideOffer(BaseModel):
    __tablename__ = "ride_offers"

    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), type_=UUID(as_uuid=True), nullable=False, index=True)
    request_source: Mapped[RequestSource] = mapped_column(Enum(RequestSource, name="request_source_enum"), nullable=False)
    
    travel_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    travel_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    start_location: Mapped[str] = mapped_column(String(255), nullable=False)
    end_location: Mapped[str] = mapped_column(String(255), nullable=False)
    
    car_model: Mapped[str] = mapped_column(String(100), nullable=False)
    total_seat_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    free_seats: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    # If we want to access photos from the RideOffer, we have to decide if photos are tied to a specific offer or just the user.
    # The requirement said "driver_id" for photos. I will assume for now they are loosely coupled or accessed via User.
    # However, to be safe, I am leaving this simple for now.


class RideRequest(BaseModel):
    __tablename__ = "ride_requests"

    passenger_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), type_=UUID(as_uuid=True), nullable=False, index=True)
    request_source: Mapped[RequestSource] = mapped_column(Enum(RequestSource, name="request_source_enum"), nullable=False)
    
    travel_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    travel_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    # locations might be pure string like Bishkek or GPS coordinates
    start_location: Mapped[str] = mapped_column(String(255), nullable=False)
    end_location: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # "Any" or specific number. 'full' option.
    seat_amount: Mapped[str] = mapped_column(String(20), nullable=False)

    def is_full(self) -> bool:
        return self.seat_amount == "full"

    @property
    def seats(self) -> int:
        return int(self.seat_amount)
