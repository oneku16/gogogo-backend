import uuid
from datetime import date, time
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.ride_service import RideService
from app.representations.dtos.ride import RideOfferSearchDTO, RideRequestSearchDTO, RideOfferDTO, RideRequestDTO
from app.domain.models.ride import RideOffer, RideRequest

@pytest.fixture
def mock_session():
    session = AsyncMock()
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
async def test_search_ride_offers(ride_service, mock_offer_repo):
    dto = RideOfferSearchDTO(
        start_location="A",
        end_location="B",
        seats_needed=2,
        start_time=date(2025, 1, 1)
    )
    
    mock_offer = RideOffer(
        id=uuid.uuid4(),
        driver_id=uuid.uuid4(),
        start_location="A",
        end_location="B",
        free_seats=3,
        travel_start_date=date(2025, 1, 1),
        travel_start_time=time(10, 0),
        car_model="Toyota",
        total_seat_amount=4,
        created_at="now",
        updated_at="now",
        request_source="mobile_app"
    )
    mock_offer_repo.search_offers.return_value = [mock_offer]
    
    result = await ride_service.search_ride_offers(dto)
    
    assert len(result) == 1
    assert result[0].start_location == "A"
    assert result[0].end_location == "B"
    mock_offer_repo.search_offers.assert_called_once_with(
        start_location="A",
        end_location="B",
        seats_needed=2,
        start_date=date(2025, 1, 1),
        limit=10,
        offset=0
    )

@pytest.mark.asyncio
async def test_search_ride_requests(ride_service, mock_request_repo):
    dto = RideRequestSearchDTO(
        start_location="X",
        end_location="Y",
        start_time=date(2025, 2, 1)
    )
    
    mock_request = RideRequest(
        id=uuid.uuid4(),
        passenger_id=uuid.uuid4(),
        start_location="X",
        end_location="Y",
        travel_start_date=date(2025, 2, 1),
        travel_start_time=time(12, 0),
        seat_amount="1",
        created_at="now",
        updated_at="now",
        request_source="telegram_app"
    )
    mock_request_repo.search_requests.return_value = [mock_request]
    
    result = await ride_service.search_ride_requests(dto)
    
    assert len(result) == 1
    assert result[0].start_location == "X"
    mock_request_repo.search_requests.assert_called_once_with(
        start_location="X",
        end_location="Y",
        start_date=date(2025, 2, 1),
        limit=10,
        offset=0
    )

@pytest.mark.asyncio
async def test_search_ride_offers_empty(ride_service, mock_offer_repo):
    dto = RideOfferSearchDTO(
        start_location="A",
        end_location="B",
        seats_needed=2,
        start_time=date(2025, 1, 1)
    )
    mock_offer_repo.search_offers.return_value = []
    
    result = await ride_service.search_ride_offers(dto)
    
    assert len(result) == 0
