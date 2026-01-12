import uuid
import enum
from datetime import date, time
from typing import List

from sqlalchemy import String, Integer, Date, Time, ForeignKey, Enum, Index
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
    __table_args__ = (
        Index('ix_ride_offers_search', 'start_location', 'end_location', 'travel_start_date'),
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), type_=UUID(as_uuid=True), nullable=False, index=True)
    request_source: Mapped[RequestSource] = mapped_column(Enum(RequestSource, name="request_source_enum"), nullable=False)
    
    travel_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    travel_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    start_location: Mapped[str] = mapped_column(String(255), nullable=False)
    end_location: Mapped[str] = mapped_column(String(255), nullable=False)
    
    car_model: Mapped[str] = mapped_column(String(100), nullable=False)
    total_seat_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    free_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=True)

    # Relationships
    driver = relationship("User", foreign_keys=[driver_id])


class RideRequest(BaseModel):
    __tablename__ = "ride_requests"
    __table_args__ = (
        Index('ix_ride_requests_search', 'start_location', 'end_location', 'travel_start_date'),
    )

    passenger_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), type_=UUID(as_uuid=True), nullable=False, index=True)
    request_source: Mapped[RequestSource] = mapped_column(Enum(RequestSource, name="request_source_enum"), nullable=False)
    
    travel_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    travel_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    # locations might be pure string like Bishkek or GPS coordinates
    start_location: Mapped[str] = mapped_column(String(255), nullable=False)
    end_location: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # "Any" or specific number. 'full' option.
    seat_amount: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships
    passenger = relationship("User", foreign_keys=[passenger_id])

    def is_full(self) -> bool:
        return self.seat_amount == "full"

    @property
    def seats(self) -> int:
        return int(self.seat_amount)
