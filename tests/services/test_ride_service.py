import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.ride_service import RideService
from app.representations.dtos.ride import CreateRideOfferDTO, CreateRideRequestDTO, RequestSource
from app.domain.models.ride import RideOffer, RideRequest, CarPhoto

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_offer_repo():
    return AsyncMock()

@pytest.fixture
def mock_request_repo():
    return AsyncMock()

@pytest.fixture
def mock_photo_repo():
    return AsyncMock()

@pytest.fixture
def mock_media_service():
    return AsyncMock()

@pytest.fixture
def ride_service(mock_session, mock_offer_repo, mock_request_repo, mock_photo_repo, mock_media_service):
    return RideService(mock_session, mock_offer_repo, mock_request_repo, mock_photo_repo, mock_media_service)

@pytest.mark.asyncio
async def test_create_ride_offer(ride_service, mock_offer_repo, mock_session):
    driver_id = uuid.uuid4()
    dto = CreateRideOfferDTO(
        travel_start_date="2025-01-01",
        travel_start_time="10:00:00",
        start_location="A",
        end_location="B",
        car_model="Toyota",
        total_seat_amount=4,
        free_seats=4,
        request_source=RequestSource.mobile_app
    )
    
    mock_offer = RideOffer(
        id=uuid.uuid4(),
        driver_id=driver_id,
        created_at="now",
        updated_at="now",
        **dto.model_dump()
    )
    mock_offer_repo.create.return_value = mock_offer
    
    result = await ride_service.create_ride_offer(driver_id, dto)
    
    assert result.driver_id == driver_id
    assert result.car_model == "Toyota"
    mock_offer_repo.create.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_create_ride_request(ride_service, mock_request_repo, mock_session):
    passenger_id = uuid.uuid4()
    dto = CreateRideRequestDTO(
        travel_start_date="2025-01-01",
        travel_start_time="10:00:00",
        start_location="A",
        end_location="B",
        seat_amount="2",
        request_source=RequestSource.mobile_app
    )
    
    mock_request = RideRequest(
        id=uuid.uuid4(),
        passenger_id=passenger_id,
        created_at="now",
        updated_at="now",
        **dto.model_dump()
    )
    mock_request_repo.create.return_value = mock_request
    
    result = await ride_service.create_ride_request(passenger_id, dto)
    
    assert result.passenger_id == passenger_id
    assert result.seat_amount == "2"
    mock_request_repo.create.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_upload_car_photo(ride_service, mock_media_service, mock_photo_repo, mock_session):
    driver_id = uuid.uuid4()
    file_bytes = b"fake_image_bytes"
    expected_url = "http://cloudinary.com/image.jpg"
    
    # Mock media service response
    mock_media_service.upload_file.return_value = {"url": expected_url}
    
    # Mock photo repo response
    mock_photo = CarPhoto(
        id=uuid.uuid4(),
        driver_id=driver_id,
        url=expected_url,
        created_at="now",
    )
    mock_photo_repo.create.return_value = mock_photo
    
    result = await ride_service.upload_car_photo(driver_id, file_bytes)
    
    assert result.url == expected_url
    assert result.driver_id == driver_id
    mock_media_service.upload_file.assert_called_once()
    mock_photo_repo.create.assert_called_once_with(driver_id, expected_url)
    mock_session.commit.assert_called_once()
