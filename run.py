#!/usr/bin/env python3
"""
JARVIS4 AI OFFICE — Main Entry Point

Launches the complete AI Office system:
- All AI agents (Master, PM, Factory, Workers)
- Individual Telegram bots for each agent
- Control Panel Telegram bot
- WebSocket server for real-time updates
- FastAPI REST API server
- Voice system
- Memory/self-learning system
- Security manager

The system runs continuously (24/7) and supports:
- Text control (Telegram, API)
- Voice control (Speech → Text → AI → Text → Speech)
- Real-time monitoring (WebSocket)
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from src.memory.memory_system import MemorySystem
from src.core.agent_manager import AgentManager
from src.core.task_engine import TaskEngine
from src.communication.telegram_bot import TelegramBotManager
from src.communication.websocket_server import WebSocketServer
from src.voice.voice_system import VoiceSystem
from src.security.security_manager import SecurityManager
from src.ai.llm_client import LLMClient
from src.api.server import app as fastapi_app, set_dependencies

# Configure logging
os.makedirs("data/logs", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("jarvis4")


class Jarvis4System:
    """
    Main AI Office system orchestrator.
    
    Initializes and runs all components:
    - Memory system (self-learning)
    - Agent manager (all agents)
    - Task engine (task processing)
    - Telegram bots (one per agent + control panel)
    - WebSocket server (real-time)
    - FastAPI server (REST API)
    - Voice system (speech pipeline)
    - Security manager
    """

    def __init__(self):
        self.memory = MemorySystem(settings.CHROMA_PATH, settings.KNOWLEDGE_PATH)

        # Initialize LLM client (OpenRouter)
        self.llm_client = LLMClient(
            api_key=settings.OPENROUTER_API_KEY,
            default_model=settings.OPENROUTER_DEFAULT_MODEL,
            site_url=settings.OPENROUTER_SITE_URL,
            app_name=settings.OPENROUTER_APP_NAME
        )

        self.agent_manager = AgentManager(self.memory, self.llm_client)
        self.task_engine = TaskEngine(self.agent_manager, self.memory)
        self.telegram_manager = TelegramBotManager(
            self.agent_manager, self.task_engine, settings
        )
        self.websocket = WebSocketServer(self.agent_manager)
        self.voice = VoiceSystem(
            language=settings.VOICE_LANGUAGE,
            tts_engine=settings.TTS_ENGINE
        ) if settings.VOICE_ENABLED else None
        self.security = SecurityManager(
            secret_key=settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
            token_expiry_hours=settings.JWT_EXPIRATION_HOURS
        )

        # Set FastAPI dependencies
        set_dependencies(self.task_engine, self.agent_manager, self.memory, self.voice, self.llm_client)

    async def start(self):
        """Start all system components."""
        logger.info("=" * 60)
        logger.info("  JARVIS4 AI OFFICE — Starting...")
        logger.info("=" * 60)

        # 1. Initialize memory
        logger.info("[1/6] Initializing memory system...")
        await self.memory.initialize()

        # 2. Initialize agents
        logger.info("[2/6] Initializing AI agents...")
        await self.agent_manager.initialize()

        # Set cross-references
        master = self.agent_manager.get_agent("master")
        if master:
            master.set_agent_manager(self.agent_manager)

        # 3. Start task engine
        logger.info("[3/6] Starting task engine...")
        await self.task_engine.start()

        # 4. Start agent work loops
        logger.info("[4/6] Starting agent work loops...")
        await self.agent_manager.start_all()

        # 5. Initialize and start Telegram bots
        logger.info("[5/6] Starting Telegram bots...")
        await self.telegram_manager.initialize()
        telegram_task = asyncio.create_task(self.telegram_manager.start_all())

        # 6. Start WebSocket server
        logger.info("[6/6] Starting WebSocket server...")
        ws_task = asyncio.create_task(
            self.websocket.start(settings.WS_HOST, settings.WS_PORT)
        )

        logger.info("=" * 60)
        logger.info("  JARVIS4 AI OFFICE — All systems online!")
        logger.info(f"  Agents: {self.agent_manager.get_agent_count()}")
        logger.info(f"  WebSocket: ws://{settings.WS_HOST}:{settings.WS_PORT}")
        logger.info(f"  API: http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}")
        logger.info(f"  Voice: {'enabled' if self.voice else 'disabled'}")
        logger.info("=" * 60)

        # Start FastAPI in background
        import uvicorn
        api_config = uvicorn.Config(
            fastapi_app,
            host=settings.FASTAPI_HOST,
            port=settings.FASTAPI_PORT,
            log_level="info"
        )
        api_server = uvicorn.Server(api_config)
        api_task = asyncio.create_task(api_server.serve())

        # Wait for all services
        await asyncio.gather(telegram_task, ws_task, api_task, return_exceptions=True)

    async def stop(self):
        """Stop all components."""
        logger.info("Shutting down JARVIS4 AI OFFICE...")
        await self.telegram_manager.stop_all()
        await self.agent_manager.stop_all()
        await self.task_engine.stop()
        logger.info("JARVIS4 AI OFFICE stopped.")


async def main():
    system = Jarvis4System()
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
