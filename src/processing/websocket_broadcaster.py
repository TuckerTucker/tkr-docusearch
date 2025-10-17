"""
WebSocket broadcaster for real-time status updates.

Broadcasts processing status and log messages to connected web clients.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketBroadcaster:
    """
    Manages WebSocket connections and broadcasts updates.

    Keeps track of connected clients and sends status updates
    to all connected clients simultaneously.
    """

    def __init__(self):
        """Initialize broadcaster with empty connection set."""
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection to add
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)

        logger.info(f"WebSocket client connected (total: {len(self.active_connections)})")

        # Send initial welcome message
        await self.send_to_client(
            websocket,
            {
                "type": "connection",
                "status": "connected",
                "message": "Connected to DocuSearch monitoring",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            self.active_connections.discard(websocket)

        logger.info(f"WebSocket client disconnected (total: {len(self.active_connections)})")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected clients.

        Args:
            message: Dictionary to send (will be JSON-encoded)
        """
        if not self.active_connections:
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        json_message = json.dumps(message)

        # Send to all clients, remove disconnected ones
        disconnected = set()
        async with self._lock:
            for connection in self.active_connections.copy():
                try:
                    await connection.send_text(json_message)
                except Exception as e:
                    logger.warning(f"Failed to send to client: {e}")
                    disconnected.add(connection)

            # Remove disconnected clients
            for connection in disconnected:
                self.active_connections.discard(connection)

    async def send_to_client(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send message to specific client.

        Args:
            websocket: WebSocket connection
            message: Dictionary to send (will be JSON-encoded)
        """
        try:
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()

            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send to client: {e}")

    async def broadcast_status_update(self, doc_id: str, status: str, progress: float, **kwargs):
        """
        Broadcast a status update.

        Args:
            doc_id: Document ID
            status: Processing status
            progress: Progress (0.0-1.0)
            **kwargs: Additional status fields
        """
        message = {
            "type": "status_update",
            "doc_id": doc_id,
            "status": status,
            "progress": progress,
            **kwargs,
        }
        await self.broadcast(message)

    async def broadcast_log_message(self, level: str, message: str, doc_id: str = None):
        """
        Broadcast a log message.

        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            doc_id: Optional document ID
        """
        msg = {"type": "log", "level": level, "message": message}
        if doc_id:
            msg["doc_id"] = doc_id

        await self.broadcast(msg)

    async def broadcast_processing_stats(self, stats: Dict[str, Any]):
        """
        Broadcast processing statistics.

        Args:
            stats: Statistics dictionary
        """
        message = {"type": "stats", **stats}
        await self.broadcast(message)

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global broadcaster instance
_broadcaster: WebSocketBroadcaster = None


def get_broadcaster() -> WebSocketBroadcaster:
    """Get or create the global broadcaster instance."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = WebSocketBroadcaster()
    return _broadcaster
