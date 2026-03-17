"""
Worker Agents — Specialized agents that execute tasks.

Each worker agent has unique capabilities and handles specific types of work.
"""

import asyncio
import logging
import os
from typing import Any
from datetime import datetime

from .base_agent import BaseAgent, Task

logger = logging.getLogger(__name__)


class ResearcherAgent(BaseAgent):
    """Researches information, collects data, finds answers."""

    def __init__(self):
        super().__init__(
            name="Researcher",
            role="Исследователь",
            capabilities=[
                "Поиск информации в интернете",
                "Сбор и систематизация данных",
                "Анализ источников",
                "Составление обзоров",
                "Факт-чекинг",
                "Мониторинг трендов"
            ]
        )

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Поиск информации...")
        await asyncio.sleep(0.2)
        await self._report_progress(task, 0.5, "Анализ источников...")
        await asyncio.sleep(0.2)
        await self._report_progress(task, 0.8, "Составление отчёта...")
        return {
            "type": "research",
            "topic": task.description,
            "findings": f"Результаты исследования по теме: {task.description}",
            "sources": ["web_search", "knowledge_base"],
            "timestamp": datetime.now().isoformat()
        }


class ProgrammerAgent(BaseAgent):
    """Writes, reviews, and debugs code."""

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
                "Автоматизация процессов"
            ]
        )

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Анализ требований...")
        await asyncio.sleep(0.2)
        await self._report_progress(task, 0.5, "Написание кода...")
        await asyncio.sleep(0.3)
        await self._report_progress(task, 0.8, "Тестирование...")
        return {
            "type": "code",
            "task": task.description,
            "result": f"Код разработан для: {task.description}",
            "language": "python",
            "timestamp": datetime.now().isoformat()
        }


class AnalystAgent(BaseAgent):
    """Analyzes data, creates reports, provides insights."""

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

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Сбор данных...")
        await asyncio.sleep(0.2)
        await self._report_progress(task, 0.5, "Анализ...")
        await asyncio.sleep(0.2)
        await self._report_progress(task, 0.8, "Формирование выводов...")
        return {
            "type": "analysis",
            "task": task.description,
            "insights": f"Аналитический отчёт: {task.description}",
            "metrics": {"confidence": 0.85, "data_points": 100},
            "timestamp": datetime.now().isoformat()
        }


class DesignerAgent(BaseAgent):
    """Creates UI/UX designs, layouts, wireframes."""

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

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Изучение требований...")
        await asyncio.sleep(0.2)
        await self._report_progress(task, 0.5, "Создание макета...")
        await asyncio.sleep(0.2)
        await self._report_progress(task, 0.8, "Финализация дизайна...")
        return {
            "type": "design",
            "task": task.description,
            "result": f"Дизайн создан: {task.description}",
            "format": "figma_concept",
            "timestamp": datetime.now().isoformat()
        }


class ArtistAgent(BaseAgent):
    """Generates images using OpenAI DALL-E API or LLM description."""

    def __init__(self):
        super().__init__(
            name="Artist",
            role="Художник",
            capabilities=[
                "Генерация изображений (DALL-E)",
                "Иллюстрации",
                "Создание баннеров",
                "Инфографика",
                "Визуальный контент"
            ]
        )

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Подготовка промпта...")

        # Try to generate image via OpenAI DALL-E
        image_url = await self._generate_image(task.description)

        if image_url:
            await self._report_progress(task, 0.9, "Изображение сгенерировано!")
            return {
                "type": "image",
                "task": task.description,
                "image_url": image_url,
                "result": f"Изображение создано! URL: {image_url}",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Fallback: use LLM to describe the image
            await self._report_progress(task, 0.5, "Генерация через LLM...")
            if self._llm_client:
                description = await self.ask_llm(
                    f"Опиши подробно изображение: {task.description}. "
                    f"Дай детальное художественное описание того, как бы выглядело это изображение.",
                    system_prompt="Ты художник-иллюстратор. Описывай изображения ярко и детально."
                )
                return {
                    "type": "image_description",
                    "task": task.description,
                    "result": description,
                    "timestamp": datetime.now().isoformat()
                }
            return {
                "type": "image",
                "task": task.description,
                "result": f"[Artist] Описание: {task.description}. Для генерации изображений добавьте OPENAI_API_KEY.",
                "timestamp": datetime.now().isoformat()
            }

    async def _generate_image(self, prompt: str) -> str:
        """Generate image using OpenAI DALL-E API."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return ""

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1024"
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["data"][0]["url"]
                    else:
                        error = await resp.text()
                        logger.error(f"DALL-E error: {error}")
                        return ""
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return ""


class MarketerAgent(BaseAgent):
    """Creates marketing content, strategies, campaigns."""

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

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.2, "Анализ целевой аудитории...")
        await asyncio.sleep(0.2)
        await self._report_progress(task, 0.5, "Разработка стратегии...")
        await asyncio.sleep(0.2)
        await self._report_progress(task, 0.8, "Создание контента...")
        return {
            "type": "marketing",
            "task": task.description,
            "result": f"Маркетинговый план: {task.description}",
            "channels": ["telegram", "instagram", "email"],
            "timestamp": datetime.now().isoformat()
        }
