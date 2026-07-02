"""WebSocket endpoint: /ws?token=<access_token>
Authenticates via the same JWT verification used for HTTP requests."""

import logging

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.security import decode_access_token
from app.websocket.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """Authenticate the WebSocket handshake with a JWT access token passed
    as a query parameter (browsers cannot send custom headers on WS)."""
    try:
        user_id = decode_access_token(token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as exc:
        logger.warning(f"WS auth failed: {exc}")
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    await manager.connect(user_id, websocket)
    try:
        # Keep the connection alive -- we only send events server→client.
        # The receive loop handles pings and detects disconnects.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception:
        manager.disconnect(user_id, websocket)
