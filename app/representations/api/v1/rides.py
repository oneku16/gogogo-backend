import uuid
from typing import List, Annotated

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form

from app.representations.dtos.ride import (
    CreateRideOfferDTO, RideOfferDTO,
    CreateRideRequestDTO, RideRequestDTO,
    CarPhotoDTO,
    RideOfferSearchDTO, RideRequestSearchDTO
)
from app.services.ride_service import RideService
from app.infrastructure.dependencies.providers import get_ride_service

router = APIRouter(tags=["Rides"])

# --- Ride Offers ---

@router.post("/offers", response_model=RideOfferDTO, status_code=status.HTTP_201_CREATED)
async def create_ride_offer(
    driver_id: uuid.UUID, # In real app, get from current_user
    dto: CreateRideOfferDTO,
    service: Annotated[RideService, Depends(get_ride_service)]
):
    return await service.create_ride_offer(driver_id, dto)

@router.get("/offers/search", response_model=List[RideOfferDTO])
async def search_ride_offers(
    # Query params mapping to DTO
    start_location: str,
    end_location: str,
    seats_needed: int,
    start_time: str, # date string YYYY-MM-DD
    limit: int = 10,
    offset: int = 0,
    service: Annotated[RideService, Depends(get_ride_service)] = None
):
    dto = RideOfferSearchDTO(
        start_location=start_location,
        end_location=end_location,
        seats_needed=seats_needed,
        start_time=start_time,
        limit=limit,
        offset=offset
    )
    return await service.search_ride_offers(dto)

@router.get("/offers", response_model=List[RideOfferDTO])
async def get_ride_offers(
    service: Annotated[RideService, Depends(get_ride_service)]
):
    return await service.get_ride_offers()

@router.get("/drivers/{driver_id}/offers", response_model=List[RideOfferDTO])
async def get_driver_offers(
    driver_id: uuid.UUID,
    service: Annotated[RideService, Depends(get_ride_service)]
):
    return await service.get_driver_offers(driver_id)

@router.delete("/offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ride_offer(
    offer_id: uuid.UUID,
    driver_id: uuid.UUID, # In real app, get from current_user
    service: Annotated[RideService, Depends(get_ride_service)]
):
    try:
        await service.delete_ride_offer(offer_id, driver_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

# --- Ride Requests ---

@router.get("/requests/search", response_model=List[RideRequestDTO])
async def search_ride_requests(
    # Query params mapping to DTO
    start_location: str,
    end_location: str,
    start_time: str, # date string YYYY-MM-DD
    limit: int = 10,
    offset: int = 0,
    service: Annotated[RideService, Depends(get_ride_service)] = None
):
    dto = RideRequestSearchDTO(
        start_location=start_location,
        end_location=end_location,
        start_time=start_time,
        limit=limit,
        offset=offset
    )
    return await service.search_ride_requests(dto)

@router.post("/requests", response_model=RideRequestDTO, status_code=status.HTTP_201_CREATED)
async def create_ride_request(
    passenger_id: uuid.UUID, # In real app, get from current_user
    dto: CreateRideRequestDTO,
    service: Annotated[RideService, Depends(get_ride_service)]
):
    return await service.create_ride_request(passenger_id, dto)

@router.get("/requests", response_model=List[RideRequestDTO])
async def get_ride_requests(
    service: Annotated[RideService, Depends(get_ride_service)]
):
    return await service.get_ride_requests()

@router.get("/passengers/{passenger_id}/requests", response_model=List[RideRequestDTO])
async def get_passenger_requests(
    passenger_id: uuid.UUID,
    service: Annotated[RideService, Depends(get_ride_service)]
):
    return await service.get_passenger_requests(passenger_id)

@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ride_request(
    request_id: uuid.UUID,
    passenger_id: uuid.UUID, # In real app, get from current_user
    service: Annotated[RideService, Depends(get_ride_service)]
):
    try:
        await service.delete_ride_request(request_id, passenger_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

# --- Car Photos ---

@router.post("/drivers/{driver_id}/photos", response_model=CarPhotoDTO, status_code=status.HTTP_201_CREATED)
async def upload_car_photo(
    driver_id: uuid.UUID, # In real app, get from current_user
    file: UploadFile = File(...),
    service: Annotated[RideService, Depends(get_ride_service)] = None
):
    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    
    try:
        return await service.upload_car_photo(driver_id, content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/drivers/{driver_id}/photos", response_model=List[CarPhotoDTO])
async def get_driver_photos(
    driver_id: uuid.UUID,
    service: Annotated[RideService, Depends(get_ride_service)]
):
    return await service.get_driver_photos(driver_id)

@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_car_photo(
    photo_id: uuid.UUID,
    driver_id: uuid.UUID, # In real app, get from current_user
    service: Annotated[RideService, Depends(get_ride_service)]
):
    try:
        await service.delete_car_photo(photo_id, driver_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
