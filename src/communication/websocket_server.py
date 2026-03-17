"""
WebSocket Server — Real-time communication between agents and clients.

Provides:
- Real-time agent status updates
- Task progress streaming
- Client notifications
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets not installed")


class WebSocketServer:
    """WebSocket server for real-time updates."""

    def __init__(self, agent_manager):
        self.agent_manager = agent_manager
        self.clients: Set = set()
        self._running = False

    async def start(self, host: str = "localhost", port: int = 8765):
        """Start the WebSocket server."""
        if not WEBSOCKETS_AVAILABLE:
            logger.error("websockets not installed")
            return

        self._running = True
        logger.info(f"WebSocket server starting on ws://{host}:{port}")

        async with websockets.serve(self._handler, host, port):
            # Start broadcasting agent statuses
            asyncio.create_task(self._broadcast_loop())
            await asyncio.Future()  # Run forever

    async def _handler(self, websocket, path=None):
        """Handle new WebSocket connections."""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total: {len(self.clients)}")

        try:
            # Send initial state
            await websocket.send(json.dumps({
                "type": "init",
                "agents": self.agent_manager.get_all_statuses(),
                "timestamp": datetime.now().isoformat()
            }))

            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON"}))

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client disconnected. Total: {len(self.clients)}")

    async def _handle_message(self, websocket, data: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type", "")

        if msg_type == "get_status":
            await websocket.send(json.dumps({
                "type": "status",
                "agents": self.agent_manager.get_all_statuses()
            }))
        elif msg_type == "ping":
            await websocket.send(json.dumps({"type": "pong"}))

    async def _broadcast_loop(self):
        """Periodically broadcast agent statuses."""
        while self._running:
            if self.clients:
                message = json.dumps({
                    "type": "status_update",
                    "agents": self.agent_manager.get_all_statuses(),
                    "timestamp": datetime.now().isoformat()
                })
                disconnected = set()
                for client in self.clients:
                    try:
                        await client.send(message)
                    except Exception:
                        disconnected.add(client)
                self.clients -= disconnected
            await asyncio.sleep(2)

    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return
        message = json.dumps(data)
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except Exception:
                disconnected.add(client)
        self.clients -= disconnected
