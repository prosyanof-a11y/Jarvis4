"""
Jarvis4 AI Office - Configuration Settings
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central configuration for the AI Office system."""

    def __init__(self):
        # ─── AI API Keys ───────────────────────────
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

        # ─── OpenRouter (100+ AI models) ──────────
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
        self.OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "anthropic/claude-3.5-sonnet")
        self.OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "https://jarvis4.ai")
        self.OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "Jarvis4 AI Office")

        # ─── Telegram Bot Tokens (one per agent) ──
        # Fallback: use TELEGRAM_BOT_TOKEN for all if individual tokens not set
        fallback_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.TELEGRAM_TOKENS = {
            "master": os.getenv("TELEGRAM_MASTER_BOT_TOKEN", fallback_token),
            "project_manager": os.getenv("TELEGRAM_PROJECT_MANAGER_BOT_TOKEN", ""),
            "researcher": os.getenv("TELEGRAM_RESEARCHER_BOT_TOKEN", ""),
            "programmer": os.getenv("TELEGRAM_PROGRAMMER_BOT_TOKEN", ""),
            "analyst": os.getenv("TELEGRAM_ANALYST_BOT_TOKEN", ""),
            "designer": os.getenv("TELEGRAM_DESIGNER_BOT_TOKEN", ""),
            "artist": os.getenv("TELEGRAM_ARTIST_BOT_TOKEN", ""),
            "marketer": os.getenv("TELEGRAM_MARKETER_BOT_TOKEN", ""),
        }
        self.TELEGRAM_CONTROL_TOKEN = os.getenv("TELEGRAM_CONTROL_BOT_TOKEN", fallback_token)

        # Authorized users
        users_str = os.getenv("TELEGRAM_AUTHORIZED_USERS", "")
        self.TELEGRAM_AUTHORIZED_USERS = [
            int(uid.strip()) for uid in users_str.split(",") if uid.strip().isdigit()
        ]

        # ─── Server Settings ──────────────────────
        self.FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
        self.FASTAPI_PORT = int(os.getenv("PORT", os.getenv("FASTAPI_PORT", "8000")))
        self.WS_HOST = os.getenv("WS_HOST", "localhost")
        self.WS_PORT = int(os.getenv("WS_PORT", "8765"))

        # ─── Security ─────────────────────────────
        self.SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

        # ─── Memory / Database ────────────────────
        self.CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/memory")
        self.KNOWLEDGE_PATH = os.getenv("KNOWLEDGE_PATH", "./data/knowledge")

        # ─── Voice Settings ───────────────────────
        self.VOICE_ENABLED = os.getenv("VOICE_ENABLED", "true").lower() == "true"
        self.VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "ru")
        self.TTS_ENGINE = os.getenv("TTS_ENGINE", "gtts")
        self.STT_ENGINE = os.getenv("STT_ENGINE", "google")

        # ─── File Paths ───────────────────────────
        self.WORKSPACE_DIR = "./workspace"
        self.GENERATED_IMAGES_DIR = "./generated_images"
        self.LOGS_DIR = "./data/logs"

        # ─── Agent Settings ───────────────────────
        self.AGENT_UPDATE_INTERVAL = float(os.getenv("AGENT_UPDATE_INTERVAL", "1.0"))
        self.TASK_PROCESSING_TIMEOUT = int(os.getenv("TASK_PROCESSING_TIMEOUT", "300"))
        self.MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "10"))

        # ─── Agent AI Models (OpenRouter) ────────
        # Each agent can have its own AI model via env vars
        # Format: AGENT_{NAME}_MODEL=openrouter/model-id
        # Falls back to defaults if not set
        self.AGENT_MODELS = {
            "master": os.getenv("AGENT_MASTER_MODEL", "anthropic/claude-3.5-sonnet"),
            "project_manager": os.getenv("AGENT_PROJECT_MANAGER_MODEL", "google/gemini-2.0-flash-001"),
            "researcher": os.getenv("AGENT_RESEARCHER_MODEL", "google/gemini-2.0-flash-001"),
            "programmer": os.getenv("AGENT_PROGRAMMER_MODEL", "deepseek/deepseek-chat"),
            "analyst": os.getenv("AGENT_ANALYST_MODEL", "google/gemini-2.0-flash-001"),
            "designer": os.getenv("AGENT_DESIGNER_MODEL", "google/gemini-2.0-flash-001"),
            "artist": os.getenv("AGENT_ARTIST_MODEL", "google/gemini-2.0-flash-001"),
            "marketer": os.getenv("AGENT_MARKETER_MODEL", "google/gemini-2.0-flash-001"),
        }

        # ─── Logging ──────────────────────────────
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "./data/logs/jarvis4.log")

        # Ensure directories exist
        for d in [self.WORKSPACE_DIR, self.GENERATED_IMAGES_DIR,
                  self.LOGS_DIR, self.CHROMA_PATH, self.KNOWLEDGE_PATH]:
            os.makedirs(d, exist_ok=True)

    def get_agent_model(self, agent_name: str) -> str:
        """Get the configured AI model for a specific agent."""
        return self.AGENT_MODELS.get(agent_name.lower(), self.OPENROUTER_DEFAULT_MODEL)

    def set_agent_model(self, agent_name: str, model: str):
        """Set the AI model for a specific agent (runtime only, not persisted to .env)."""
        self.AGENT_MODELS[agent_name.lower()] = model


# Global singleton
settings = Settings()
