from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.db import async_session_factory
from app.models import User
from app.security import decode_access_token
from app.websockets.manager import ws_manager

router = APIRouter()


async def _get_ws_user(websocket: WebSocket) -> User | None:
    token = websocket.query_params.get("token")
    if not token:
        return None

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None

    async with async_session_factory() as session:
        user = await session.get(User, UUID(user_id))
        return user


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket) -> None:
    user = await _get_ws_user(websocket)
    if user is None:
        await websocket.close(code=1008)
        return

    await ws_manager.connect(str(user.id), websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(str(user.id), websocket)
