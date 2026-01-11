import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.user_service import UserService
from app.representations.dtos.user import CreateUserDTO, CreateTelegramUserDTO

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_user_repo():
    return AsyncMock()

@pytest.fixture
def mock_telegram_user_repo():
    return AsyncMock()

@pytest.fixture
def user_service(mock_session, mock_user_repo, mock_telegram_user_repo):
    return UserService(mock_session, mock_user_repo, mock_telegram_user_repo)

@pytest.mark.asyncio
async def test_register_user_success(user_service, mock_user_repo, mock_session):
    dto = CreateUserDTO(
        phone_number="1234567890",
        first_name="John",
        last_name="Doe"
    )
    
    mock_user_repo.find_by_phone.return_value = None
    
    # Mock created user
    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.phone_number = dto.phone_number
    mock_user.first_name = dto.first_name
    mock_user.last_name = dto.last_name
    mock_user.created_at = "now"
    mock_user.updated_at = "now"
    
    mock_user_repo.create.return_value = mock_user
    
    result = await user_service.register_user(dto)
    
    assert result.phone_number == dto.phone_number
    mock_user_repo.find_by_phone.assert_called_once_with(dto.phone_number)
    mock_user_repo.create.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_register_user_duplicate_phone(user_service, mock_user_repo):
    dto = CreateUserDTO(phone_number="1234567890", first_name="John")
    
    # Simulate existing user
    existing_user = MagicMock()
    existing_user.id = uuid.uuid4()
    existing_user.phone_number = dto.phone_number
    mock_user_repo.find_by_phone.return_value = existing_user
    
    # Expectation: No error raised, returns existing user
    result = await user_service.register_user(dto)
    
    assert result.id == existing_user.id
    assert result.phone_number == existing_user.phone_number
    # Verify create was NOT called
    mock_user_repo.create.assert_not_called()

@pytest.mark.asyncio
async def test_register_telegram_user_bind_by_id(user_service, mock_telegram_user_repo, mock_user_repo, mock_session):
    user_id = uuid.uuid4()
    dto = CreateTelegramUserDTO(
        telegram_id=12345,
        username="john_tg",
        user_id=user_id
    )
    
    mock_telegram_user_repo.find_by_telegram_id.return_value = None
    
    # Mock existing user finding
    mock_user_repo.get_by_id.return_value = MagicMock(id=user_id)
    
    # Mock telegram user creation
    mock_tg_user = MagicMock()
    mock_tg_user.id = uuid.uuid4()
    mock_tg_user.telegram_id = dto.telegram_id
    mock_tg_user.user_id = user_id
    mock_tg_user.created_at = "now"
    mock_tg_user.updated_at = "now"
    
    mock_telegram_user_repo.create.return_value = mock_tg_user
    
    result = await user_service.register_telegram_user(dto)
    
    assert result.telegram_id == dto.telegram_id
    assert result.user_id == user_id
    mock_user_repo.get_by_id.assert_called_once_with(user_id)
    mock_telegram_user_repo.create.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_register_telegram_user_create_new_implicit(user_service, mock_telegram_user_repo, mock_user_repo, mock_session):
    dto = CreateTelegramUserDTO(
        telegram_id=98765,
        username="new_user",
        phone_number="9876543210" # Provided phone, no user_id
    )
    
    mock_telegram_user_repo.find_by_telegram_id.return_value = None
    mock_user_repo.find_by_phone.return_value = None # No existing user with this phone
    
    # Mock creation of new user
    new_user_id = uuid.uuid4()
    mock_new_user = MagicMock(id=new_user_id)
    mock_user_repo.create.return_value = mock_new_user
    
    # Mock creation of telegram user
    mock_tg_user = MagicMock(id=uuid.uuid4(), user_id=new_user_id, telegram_id=dto.telegram_id)
    mock_tg_user.created_at = "now"
    mock_tg_user.updated_at = "now"
    mock_telegram_user_repo.create.return_value = mock_tg_user
    
    result = await user_service.register_telegram_user(dto)
    
    assert result.user_id == new_user_id
    mock_user_repo.create.assert_called_once() # Implicit creation verified
    mock_telegram_user_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_register_telegram_user_already_registered(user_service, mock_telegram_user_repo):
    dto = CreateTelegramUserDTO(telegram_id=123, user_id=uuid.uuid4())
    
    mock_telegram_user_repo.find_by_telegram_id.return_value = MagicMock()
    
    with pytest.raises(ValueError, match="already registered"):
        await user_service.register_telegram_user(dto)
