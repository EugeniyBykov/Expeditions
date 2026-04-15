from __future__ import annotations

from pydantic import BaseModel, EmailStr
from fastapi import HTTPException, status

from app.db import AsyncUnitOfWork
from app.repositories.user import UserRepository
from app.security import create_access_token


class LoginRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthService:
    def __init__(self, user_repository: UserRepository | None = None):
        self._user_repository = user_repository or UserRepository()

    async def login(self, email: str, uow: AsyncUnitOfWork) -> TokenResponse:
        # no psw usage, no refresh token for simplicity
        user = await self._user_repository.get_by_email(uow.session, email)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        token = create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "role": user.role.value,
            },
        )
        return TokenResponse(access_token=token)
