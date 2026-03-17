#!/usr/bin/env python3
"""
JARVIS4 AI OFFICE — Main Entry Point

Launches:
- FastAPI REST API (primary, for Railway health check)
- Telegram bots (background)
- Memory system
- Agent manager
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from src.memory.memory_system import MemorySystem
from src.core.agent_manager import AgentManager
from src.core.task_engine import TaskEngine
from src.communication.telegram_bot import TelegramBotManager
from src.voice.voice_system import VoiceSystem
from src.security.security_manager import SecurityManager
from src.ai.llm_client import LLMClient
from src.api.server import app as fastapi_app, set_dependencies

# Logging
os.makedirs("data/logs", exist_ok=True)
log_handlers = [logging.StreamHandler(sys.stdout)]
try:
    log_handlers.append(logging.FileHandler(settings.LOG_FILE, encoding="utf-8"))
except Exception:
    pass

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=log_handlers
)
logger = logging.getLogger("jarvis4")


class Jarvis4System:
    def __init__(self):
        self.memory = MemorySystem(settings.CHROMA_PATH, settings.KNOWLEDGE_PATH)
        self.llm_client = LLMClient(
            api_key=settings.OPENROUTER_API_KEY,
            default_model=settings.OPENROUTER_DEFAULT_MODEL,
            site_url=getattr(settings, 'OPENROUTER_SITE_URL', ''),
            app_name=getattr(settings, 'OPENROUTER_APP_NAME', 'Jarvis4')
        )
        self.agent_manager = AgentManager(self.memory, self.llm_client)
        self.task_engine = TaskEngine(self.agent_manager, self.memory)
        self.telegram_manager = TelegramBotManager(
            self.agent_manager, self.task_engine, settings
        )
        self.voice = None
        if settings.VOICE_ENABLED:
            try:
                self.voice = VoiceSystem(settings.VOICE_LANGUAGE, settings.TTS_ENGINE)
            except Exception:
                pass

        set_dependencies(self.task_engine, self.agent_manager, self.memory, self.voice, self.llm_client)

    async def start_background(self):
        """Start background services (memory, agents, telegram)."""
        logger.info("=" * 50)
        logger.info("  JARVIS4 AI OFFICE — Starting...")
        logger.info("=" * 50)

        try:
            await self.memory.initialize()
            logger.info("[1/4] Memory initialized")
        except Exception as e:
            logger.error(f"Memory init error: {e}")

        try:
            await self.agent_manager.initialize()
            master = self.agent_manager.get_agent("master")
            if master:
                master.set_agent_manager(self.agent_manager)
            logger.info(f"[2/4] {self.agent_manager.get_agent_count()} agents initialized")
        except Exception as e:
            logger.error(f"Agent init error: {e}")

        try:
            await self.task_engine.start()
            logger.info("[3/4] Task engine started")
        except Exception as e:
            logger.error(f"Task engine error: {e}")

        try:
            await self.telegram_manager.initialize()
            asyncio.create_task(self.telegram_manager.start_all())
            logger.info("[4/4] Telegram bots starting...")
        except Exception as e:
            logger.error(f"Telegram error: {e}")

        logger.info("=" * 50)
        logger.info("  JARVIS4 AI OFFICE — Online!")
        logger.info("=" * 50)


# Global system instance
system = Jarvis4System()


@fastapi_app.on_event("startup")
async def startup():
    """Start background services when FastAPI starts."""
    await system.start_background()


if __name__ == "__main__":
    import uvicorn
    # Railway sets PORT env var; default to 8080 for Railway compatibility
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting FastAPI on {host}:{port}")
    uvicorn.run(
        "run:fastapi_app",
        host=host,
        port=port,
        log_level="info"
    )
