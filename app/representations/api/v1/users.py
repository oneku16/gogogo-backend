from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.dependencies.providers import get_user_service
from app.representations.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    Create a new user.
    """
    try:
        user_dto = await service.register_user(user_create)
        return user_dto # Pydantic will validate this against UserRead
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
