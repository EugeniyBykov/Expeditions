from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id)
        if not sockets:
            return

        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        sockets = self._connections.get(user_id)
        if not sockets:
            return

        dead_sockets: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_sockets.append(websocket)

        for websocket in dead_sockets:
            sockets.discard(websocket)

        if not sockets:
            self._connections.pop(user_id, None)

    async def broadcast_to_users(
        self,
        user_ids: Iterable[str],
        message: dict[str, Any],
    ) -> None:
        for user_id in set(user_ids):
            await self.send_to_user(user_id, message)


ws_manager = WebSocketManager()
