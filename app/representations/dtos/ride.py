import uuid
from datetime import date, time
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.domain.models.ride import RequestSource


class BaseRideDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    travel_start_date: date
    travel_start_time: time
    start_location: str
    end_location: str
    request_source: RequestSource


# --- Ride Offer DTOs ---

class CreateRideOfferDTO(BaseRideDTO):
    car_model: str
    total_seat_amount: int
    free_seats: int
    price: Optional[int] = None


class UpdateRideOfferDTO(BaseModel):
    travel_start_date: Optional[date] = None
    travel_start_time: Optional[time] = None
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    car_model: Optional[str] = None
    total_seat_amount: Optional[int] = None
    free_seats: Optional[int] = None
    price: Optional[int] = None


class RideOfferDTO(BaseRideDTO):
    id: uuid.UUID
    driver_id: uuid.UUID
    car_model: str
    total_seat_amount: int
    free_seats: int
    price: Optional[int] = None


# --- Ride Request DTOs ---

class CreateRideRequestDTO(BaseRideDTO):
    seat_amount: str  # "1", "2", "full"


class UpdateRideRequestDTO(BaseModel):
    travel_start_date: Optional[date] = None
    travel_start_time: Optional[time] = None
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    seat_amount: Optional[str] = None


class RideRequestDTO(BaseRideDTO):
    id: uuid.UUID
    passenger_id: uuid.UUID
    seat_amount: str


# --- Search DTOs ---

class RideOfferSearchDTO(BaseModel):
    start_location: str
    end_location: str
    seats_needed: int
    start_time: date # we'll use date for MVP search, or datetime if needed. Requirement said "time".
                     # Actually, requirement said "offer_start_times >= request_start_time".
                     # Let's support date and time.
    start_time_time: Optional[time] = None # Optional, if not provided maybe just date?
                                           # For simplicity let's stick to date + optional time filter logic
                                           # or just timestamp. The models use date + time separate columns.
    
    limit: int = 10
    offset: int = 0


class RideRequestSearchDTO(BaseModel):
    start_location: str
    end_location: str
    start_time: date
    start_time_time: Optional[time] = None
    
    limit: int = 10
    offset: int = 0


# --- Car Photo DTOs ---

class CreateCarPhotoDTO(BaseModel):
    url: str

class CarPhotoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    driver_id: uuid.UUID
    url: str
