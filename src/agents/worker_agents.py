"""
Worker Agents — Specialized agents that execute tasks via OpenRouter LLM.

Each agent uses the most appropriate AI model for their role:
- Researcher: fast model for search/analysis
- Programmer: code-specialized model
- Analyst: analytical model
- Designer: creative model
- Artist: image generation (DALL-E) + creative description
- Marketer: content-focused model
"""

import asyncio
import logging
import os
from typing import Any
from datetime import datetime

from .base_agent import BaseAgent, Task

logger = logging.getLogger(__name__)

# Model assignments per agent role (OpenRouter model IDs)
# Priority: free → cheap → standard
AGENT_MODELS = {
    "researcher": "meta-llama/llama-3.1-8b-instruct:free",      # Free, good for research
    "programmer": "deepseek/deepseek-coder",                      # Cheap, code-specialized
    "analyst": "meta-llama/llama-3.1-70b-instruct",              # Good analytical reasoning
    "designer": "meta-llama/llama-3.1-8b-instruct:free",        # Free, creative
    "artist": "meta-llama/llama-3.1-8b-instruct:free",          # Free for descriptions
    "marketer": "mistralai/mistral-7b-instruct:free",            # Free, good for content
    "master": "anthropic/claude-3.5-sonnet",                      # Best for coordination
    "project_manager": "meta-llama/llama-3.1-8b-instruct:free", # Free for planning
}


class ResearcherAgent(BaseAgent):
    """Researches information using LLM."""

    def __init__(self):
        super().__init__(
            name="Researcher",
            role="Исследователь",
            capabilities=[
                "Поиск информации",
                "Сбор и систематизация данных",
                "Анализ источников",
                "Составление обзоров",
                "Факт-чекинг",
                "Мониторинг трендов"
            ]
        )
        self._preferred_model = AGENT_MODELS["researcher"]

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Поиск информации...")

        if self._llm_client:
            await self._report_progress(task, 0.4, "Анализ через AI...")
            result = await self.ask_llm(
                f"Исследуй тему и дай подробный ответ: {task.description}",
                system_prompt=(
                    "Ты опытный исследователь. Дай подробный, структурированный ответ. "
                    "Используй факты, цифры, примеры. Отвечай на русском."
                ),
                model=self._preferred_model
            )
            await self._report_progress(task, 0.9, "Формирую отчёт...")
            return {"type": "research", "task": task.description, "result": result,
                    "model": self._preferred_model, "timestamp": datetime.now().isoformat()}

        return {"type": "research", "task": task.description,
                "result": f"[Researcher] Исследование: {task.description}",
                "timestamp": datetime.now().isoformat()}


class ProgrammerAgent(BaseAgent):
    """Writes code using code-specialized LLM."""

    def __init__(self):
        super().__init__(
            name="Programmer",
            role="Программист",
            capabilities=[
                "Написание кода (Python, JS, и др.)",
                "Отладка и исправление ошибок",
                "Code review",
                "Создание API",
                "Работа с базами данных",
                "Автоматизация"
            ]
        )
        self._preferred_model = AGENT_MODELS["programmer"]

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Анализ требований...")

        if self._llm_client:
            await self._report_progress(task, 0.5, "Написание кода...")
            result = await self.ask_llm(
                f"Напиши код для: {task.description}",
                system_prompt=(
                    "Ты опытный программист. Пиши чистый, рабочий код. "
                    "Добавляй комментарии. Используй лучшие практики. "
                    "Если нужен Python — пиши на Python. Отвечай на русском с кодом."
                ),
                model=self._preferred_model
            )
            await self._report_progress(task, 0.9, "Код готов!")
            return {"type": "code", "task": task.description, "result": result,
                    "model": self._preferred_model, "timestamp": datetime.now().isoformat()}

        return {"type": "code", "task": task.description,
                "result": f"[Programmer] Код для: {task.description}",
                "timestamp": datetime.now().isoformat()}


class AnalystAgent(BaseAgent):
    """Analyzes data using analytical LLM."""

    def __init__(self):
        super().__init__(
            name="Analyst",
            role="Аналитик",
            capabilities=[
                "Анализ данных",
                "Статистическая обработка",
                "Визуализация данных",
                "Прогнозирование",
                "Составление отчётов",
                "Бизнес-аналитика"
            ]
        )
        self._preferred_model = AGENT_MODELS["analyst"]

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Сбор данных...")

        if self._llm_client:
            await self._report_progress(task, 0.5, "Анализ...")
            result = await self.ask_llm(
                f"Проведи анализ: {task.description}",
                system_prompt=(
                    "Ты бизнес-аналитик. Проведи глубокий анализ. "
                    "Используй структуру: проблема, данные, выводы, рекомендации. "
                    "Добавляй метрики и цифры где возможно. Отвечай на русском."
                ),
                model=self._preferred_model
            )
            await self._report_progress(task, 0.9, "Отчёт готов!")
            return {"type": "analysis", "task": task.description, "result": result,
                    "model": self._preferred_model, "timestamp": datetime.now().isoformat()}

        return {"type": "analysis", "task": task.description,
                "result": f"[Analyst] Анализ: {task.description}",
                "timestamp": datetime.now().isoformat()}


class DesignerAgent(BaseAgent):
    """Creates designs using creative LLM."""

    def __init__(self):
        super().__init__(
            name="Designer",
            role="Дизайнер",
            capabilities=[
                "UI/UX дизайн",
                "Создание макетов",
                "Прототипирование",
                "Дизайн-системы",
                "Адаптивный дизайн",
                "Брендинг"
            ]
        )
        self._preferred_model = AGENT_MODELS["designer"]

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Изучение требований...")

        if self._llm_client:
            await self._report_progress(task, 0.5, "Создание концепции...")
            result = await self.ask_llm(
                f"Создай дизайн-концепцию: {task.description}",
                system_prompt=(
                    "Ты UI/UX дизайнер. Опиши дизайн-концепцию подробно: "
                    "цвета, шрифты, layout, компоненты, UX-решения. "
                    "Если нужен код — дай HTML/CSS. Отвечай на русском."
                ),
                model=self._preferred_model
            )
            await self._report_progress(task, 0.9, "Дизайн готов!")
            return {"type": "design", "task": task.description, "result": result,
                    "model": self._preferred_model, "timestamp": datetime.now().isoformat()}

        return {"type": "design", "task": task.description,
                "result": f"[Designer] Дизайн: {task.description}",
                "timestamp": datetime.now().isoformat()}


class ArtistAgent(BaseAgent):
    """Generates images using DALL-E (OpenRouter) or LLM descriptions."""

    def __init__(self):
        super().__init__(
            name="Artist",
            role="Художник",
            capabilities=[
                "Генерация изображений (DALL-E 3)",
                "Иллюстрации",
                "Создание баннеров",
                "Инфографика",
                "Визуальный контент"
            ]
        )
        self._preferred_model = AGENT_MODELS["artist"]

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Подготовка промпта...")

        # Try image generation
        image_url = await self._generate_image(task.description)

        if image_url:
            await self._report_progress(task, 0.9, "Изображение создано!")
            return {"type": "image", "task": task.description, "image_url": image_url,
                    "result": f"Изображение: {image_url}",
                    "timestamp": datetime.now().isoformat()}

        # Fallback: LLM description
        if self._llm_client:
            await self._report_progress(task, 0.5, "Создаю описание...")
            result = await self.ask_llm(
                f"Опиши подробно изображение: {task.description}. "
                f"Дай детальное художественное описание.",
                system_prompt="Ты художник. Описывай изображения ярко и детально на русском.",
                model=self._preferred_model
            )
            return {"type": "image_description", "task": task.description, "result": result,
                    "timestamp": datetime.now().isoformat()}

        return {"type": "image", "task": task.description,
                "result": f"[Artist] {task.description}. Добавьте OPENROUTER_API_KEY для генерации.",
                "timestamp": datetime.now().isoformat()}

    async def _generate_image(self, prompt: str) -> str:
        """Generate image. Priority: Pollinations (free) → OpenAI DALL-E."""
        import aiohttp
        from urllib.parse import quote

        # 1. Pollinations.ai — FREE, no API key needed
        try:
            encoded = quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200 and resp.content_type.startswith("image"):
                        return url  # Pollinations returns the image at this URL
            logger.warning("Pollinations.ai failed")
        except Exception as e:
            logger.warning(f"Pollinations error: {e}")

        # 2. OpenAI DALL-E (if key available)
        key = os.getenv("OPENAI_API_KEY", "")
        if key:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.openai.com/v1/images/generations",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json={"model": "dall-e-3", "prompt": prompt, "n": 1, "size": "1024x1024"},
                        timeout=aiohttp.ClientTimeout(total=90)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data["data"][0]["url"]
            except Exception as e:
                logger.error(f"OpenAI image: {e}")

        return ""


class MarketerAgent(BaseAgent):
    """Creates marketing content using LLM."""

    def __init__(self):
        super().__init__(
            name="Marketer",
            role="Маркетолог",
            capabilities=[
                "Маркетинговые стратегии",
                "Контент-маркетинг",
                "SMM и соцсети",
                "Email-маркетинг",
                "SEO-оптимизация",
                "Рекламные кампании",
                "Копирайтинг"
            ]
        )
        self._preferred_model = AGENT_MODELS["marketer"]

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Анализ аудитории...")

        if self._llm_client:
            await self._report_progress(task, 0.5, "Создание контента...")
            result = await self.ask_llm(
                f"Создай маркетинговый контент: {task.description}",
                system_prompt=(
                    "Ты маркетолог-копирайтер. Создавай продающий контент. "
                    "Используй: заголовки, CTA, эмоции, структуру. "
                    "Адаптируй под соцсети (Telegram, Instagram). Отвечай на русском."
                ),
                model=self._preferred_model
            )
            await self._report_progress(task, 0.9, "Контент готов!")
            return {"type": "marketing", "task": task.description, "result": result,
                    "model": self._preferred_model, "timestamp": datetime.now().isoformat()}

        return {"type": "marketing", "task": task.description,
                "result": f"[Marketer] Маркетинг: {task.description}",
                "timestamp": datetime.now().isoformat()}
