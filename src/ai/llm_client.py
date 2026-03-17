"""
LLM Client — OpenRouter API integration with model selection.

OpenRouter provides access to 100+ AI models through a single API:
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus, Haiku)
- Google (Gemini Pro, Gemini Flash)
- Meta (Llama 3.1, Llama 3.2)
- Mistral (Mistral Large, Mixtral)
- DeepSeek, Qwen, and many more

Usage:
    client = LLMClient(api_key="your_openrouter_key")
    response = await client.chat("Hello!", model="anthropic/claude-3.5-sonnet")
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# ─── Available Models ──────────────────────────────────────────────

AVAILABLE_MODELS = {
    # OpenAI
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "gpt-4-turbo": "openai/gpt-4-turbo",
    "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
    "o1": "openai/o1",
    "o1-mini": "openai/o1-mini",

    # Anthropic
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    "claude-3-opus": "anthropic/claude-3-opus",
    "claude-3-sonnet": "anthropic/claude-3-sonnet",
    "claude-3-haiku": "anthropic/claude-3-haiku",

    # Google
    "gemini-2.0-flash": "google/gemini-2.0-flash-001",
    "gemini-pro": "google/gemini-pro-1.5",
    "gemini-flash": "google/gemini-flash-1.5",

    # Meta Llama
    "llama-3.1-405b": "meta-llama/llama-3.1-405b-instruct",
    "llama-3.1-70b": "meta-llama/llama-3.1-70b-instruct",
    "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
    "llama-3.2-90b": "meta-llama/llama-3.2-90b-vision-instruct",

    # Mistral
    "mistral-large": "mistralai/mistral-large",
    "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct",
    "mistral-7b": "mistralai/mistral-7b-instruct",

    # DeepSeek
    "deepseek-chat": "deepseek/deepseek-chat",
    "deepseek-r1": "deepseek/deepseek-r1",
    "deepseek-coder": "deepseek/deepseek-coder",

    # Qwen
    "qwen-2.5-72b": "qwen/qwen-2.5-72b-instruct",
    "qwen-2.5-coder-32b": "qwen/qwen-2.5-coder-32b-instruct",

    # Free models (for testing)
    "free-gpt-3.5": "openai/gpt-3.5-turbo",
    "free-llama": "meta-llama/llama-3.1-8b-instruct:free",
    "free-mistral": "mistralai/mistral-7b-instruct:free",
}

DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str = ""
    raw: Dict[str, Any] = None


class LLMClient:
    """
    OpenRouter LLM Client with model selection.
    
    Supports 100+ AI models through OpenRouter API.
    Compatible with OpenAI API format.
    """

    def __init__(self, api_key: str = "", default_model: str = DEFAULT_MODEL,
                 site_url: str = "https://jarvis4.ai", app_name: str = "Jarvis4 AI Office"):
        self.api_key = api_key
        self.default_model = default_model
        self.site_url = site_url
        self.app_name = app_name
        self._session = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for OpenRouter API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }

    async def chat(self, message: str, model: str = None,
                   system_prompt: str = None,
                   temperature: float = 0.7,
                   max_tokens: int = 4096,
                   history: List[Dict[str, str]] = None) -> LLMResponse:
        """
        Send a chat message to the LLM.
        
        Args:
            message: User message
            model: Model ID (e.g. "anthropic/claude-3.5-sonnet") or short name (e.g. "claude-3.5-sonnet")
            system_prompt: System prompt for the conversation
            temperature: Creativity (0.0 - 1.0)
            max_tokens: Maximum response length
            history: Previous messages [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            LLMResponse with content, model, usage info
        """
        if not self.api_key:
            return LLMResponse(
                content="[ERROR] OpenRouter API key not configured. Set OPENROUTER_API_KEY in .env",
                model="none", usage={}
            )

        # Resolve model name
        resolved_model = self._resolve_model(model)

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        # Build request body
        body = {
            "model": resolved_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.info(f"LLM request: model={resolved_model}, message={message[:80]}...")

        try:
            if AIOHTTP_AVAILABLE:
                return await self._request_aiohttp(body, resolved_model)
            elif HTTPX_AVAILABLE:
                return await self._request_httpx(body, resolved_model)
            else:
                return LLMResponse(
                    content="[ERROR] No HTTP client available. Install aiohttp or httpx.",
                    model=resolved_model, usage={}
                )
        except Exception as e:
            logger.error(f"LLM request error: {e}")
            return LLMResponse(
                content=f"[ERROR] LLM request failed: {str(e)}",
                model=resolved_model, usage={}
            )

    async def _request_aiohttp(self, body: dict, model: str) -> LLMResponse:
        """Make request using aiohttp."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_API_URL,
                headers=self._get_headers(),
                json=body,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                data = await resp.json()

                if resp.status != 200:
                    error = data.get("error", {}).get("message", str(data))
                    return LLMResponse(content=f"[API Error {resp.status}] {error}",
                                       model=model, usage={})

                return self._parse_response(data, model)

    async def _request_httpx(self, body: dict, model: str) -> LLMResponse:
        """Make request using httpx."""
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                OPENROUTER_API_URL,
                headers=self._get_headers(),
                json=body
            )
            data = resp.json()

            if resp.status_code != 200:
                error = data.get("error", {}).get("message", str(data))
                return LLMResponse(content=f"[API Error {resp.status_code}] {error}",
                                   model=model, usage={})

            return self._parse_response(data, model)

    def _parse_response(self, data: dict, model: str) -> LLMResponse:
        """Parse OpenRouter API response."""
        choices = data.get("choices", [])
        if not choices:
            return LLMResponse(content="[No response from model]", model=model, usage={})

        choice = choices[0]
        content = choice.get("message", {}).get("content", "")
        finish_reason = choice.get("finish_reason", "")
        usage = data.get("usage", {})
        actual_model = data.get("model", model)

        return LLMResponse(
            content=content,
            model=actual_model,
            usage=usage,
            finish_reason=finish_reason,
            raw=data
        )

    def _resolve_model(self, model: str = None) -> str:
        """Resolve short model name to full OpenRouter model ID."""
        if not model:
            return self.default_model

        # Check if it's already a full model ID (contains /)
        if "/" in model:
            return model

        # Look up in available models
        if model in AVAILABLE_MODELS:
            return AVAILABLE_MODELS[model]

        # Try partial match
        model_lower = model.lower()
        for short_name, full_name in AVAILABLE_MODELS.items():
            if model_lower in short_name.lower() or model_lower in full_name.lower():
                return full_name

        # Return as-is (let OpenRouter handle it)
        return model

    def set_model(self, model: str):
        """Change the default model."""
        self.default_model = self._resolve_model(model)
        logger.info(f"Default model set to: {self.default_model}")

    def set_api_key(self, api_key: str):
        """Update the API key."""
        self.api_key = api_key

    @staticmethod
    def list_models() -> Dict[str, str]:
        """List all available model shortcuts."""
        return AVAILABLE_MODELS.copy()

    async def fetch_available_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from OpenRouter API."""
        if not self.api_key:
            return []

        try:
            if AIOHTTP_AVAILABLE:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        OPENROUTER_MODELS_URL,
                        headers=self._get_headers(),
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data.get("data", [])
            elif HTTPX_AVAILABLE:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(OPENROUTER_MODELS_URL, headers=self._get_headers())
                    if resp.status_code == 200:
                        return resp.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")

        return []

    def get_info(self) -> Dict[str, Any]:
        """Get client configuration info."""
        return {
            "api_configured": bool(self.api_key),
            "default_model": self.default_model,
            "available_shortcuts": len(AVAILABLE_MODELS),
            "app_name": self.app_name,
        }
