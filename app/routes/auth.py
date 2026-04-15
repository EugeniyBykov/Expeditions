from fastapi import APIRouter, Depends

from app.db import get_uow, AsyncUnitOfWork
from app.services.auth import AuthService, LoginRequest, TokenResponse

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse, tags=["auth"])
async def login(
    payload: LoginRequest,
    uow: AsyncUnitOfWork = Depends(get_uow),
) -> TokenResponse:
    service = AuthService()
    return await service.login(payload.email, uow)
