"""WebSocket connection manager keyed by user_id.
A user may have multiple tabs open, so each user_id maps to a list of sockets."""

import uuid
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Dict[user_id, List[WebSocket]]
        self._connections: dict[uuid.UUID, list[WebSocket]] = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)
        logger.info(f"WS connected: user={user_id}, total={len(self._connections[user_id])}")

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket):
        if user_id in self._connections:
            try:
                self._connections[user_id].remove(websocket)
            except ValueError:
                pass
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info(f"WS disconnected: user={user_id}")

    async def send_to_user(self, user_id: uuid.UUID, event: dict[str, Any]):
        """Send an event to all connections of a specific user."""
        if user_id not in self._connections:
            return
        message = json.dumps(event, default=str)
        dead: list[WebSocket] = []
        for ws in self._connections[user_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        # Clean up dead connections
        for ws in dead:
            try:
                self._connections[user_id].remove(ws)
            except ValueError:
                pass
        if user_id in self._connections and not self._connections[user_id]:
            del self._connections[user_id]

    async def send_to_users(self, user_ids: list[uuid.UUID], event: dict[str, Any]):
        """Send an event to multiple users."""
        for uid in user_ids:
            await self.send_to_user(uid, event)


# Global singleton
manager = ConnectionManager()
