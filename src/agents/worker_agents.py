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

# Import settings for agent model configuration
try:
    from config.settings import settings
    AGENT_MODELS = settings.AGENT_MODELS
except ImportError:
    # Fallback defaults if settings not available
    AGENT_MODELS = {
        "researcher": "meta-llama/llama-3.1-8b-instruct:free",
        "programmer": "deepseek/deepseek-coder",
        "analyst": "meta-llama/llama-3.1-70b-instruct",
        "designer": "meta-llama/llama-3.1-8b-instruct:free",
        "artist": "meta-llama/llama-3.1-8b-instruct:free",
        "marketer": "mistralai/mistral-7b-instruct:free",
        "master": "anthropic/claude-3.5-sonnet",
        "project_manager": "meta-llama/llama-3.1-8b-instruct:free",
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
    """Writes and EXECUTES code using code-specialized LLM + CodeExecutorTool."""

    def __init__(self):
        super().__init__(
            name="Programmer",
            role="Программист",
            capabilities=[
                "Написание кода (Python, JS, и др.)",
                "Выполнение Python-кода",
                "Сохранение файлов в workspace",
                "Отладка и исправление ошибок",
                "Code review",
                "Создание API",
                "Работа с базами данных",
                "Автоматизация"
            ]
        )
        self._preferred_model = AGENT_MODELS["programmer"]

    def _extract_code_blocks(self, text: str) -> list:
        """Extract code blocks from LLM response."""
        import re
        # Match ```python ... ``` or ``` ... ```
        pattern = r"```(?:python|py|javascript|js|bash|sh|html|css)?\n?(.*?)```"
        blocks = re.findall(pattern, text, re.DOTALL)
        return [b.strip() for b in blocks if b.strip()]

    def _detect_language(self, code: str, task_desc: str) -> str:
        """Detect programming language from code or task description."""
        desc_lower = task_desc.lower()
        if any(kw in desc_lower for kw in ["javascript", "js", "node", "react", "vue"]):
            return "javascript"
        if any(kw in desc_lower for kw in ["html", "css", "web", "сайт", "страниц"]):
            return "html"
        # Default to Python
        return "python"

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.1, "Анализ требований...")

        if not self._llm_client:
            return {"type": "code", "task": task.description,
                    "result": f"[Programmer] Код для: {task.description}",
                    "timestamp": datetime.now().isoformat()}

        await self._report_progress(task, 0.3, "Написание кода через AI...")

        # Determine if we should execute or just write
        desc_lower = task.description.lower()
        should_execute = any(kw in desc_lower for kw in [
            "выполни", "запусти", "run", "execute", "посчитай", "вычисли",
            "calculate", "compute", "проверь", "test"
        ])
        should_save = any(kw in desc_lower for kw in [
            "сохрани", "создай файл", "save", "write file", "скрипт", "script"
        ])

        # Generate code via LLM
        code_response = await self.ask_llm(
            f"Напиши код для следующей задачи. Верни ТОЛЬКО код в блоке ```python ... ```, "
            f"без лишних объяснений до и после блока кода. Задача: {task.description}",
            system_prompt=(
                "Ты опытный программист. Пиши чистый, рабочий код. "
                "Добавляй комментарии на русском. Используй лучшие практики. "
                "ВАЖНО: Верни код в блоке ```python ... ```. "
                "После блока кода можешь добавить краткое объяснение."
            ),
            model=self._preferred_model
        )

        await self._report_progress(task, 0.6, "Код написан, обрабатываю...")

        # Extract code blocks
        code_blocks = self._extract_code_blocks(code_response)
        saved_files = []
        execution_results = []

        if code_blocks and self._tool_manager:
            for i, code in enumerate(code_blocks):
                # Save code to file
                if should_save or True:  # Always save for reference
                    lang = self._detect_language(code, task.description)
                    ext_map = {"python": "py", "javascript": "js", "html": "html", "css": "css"}
                    ext = ext_map.get(lang, "py")
                    filename = f"code_{hash(task.description) % 10000}_{i}.{ext}"

                    save_result = await self._tool_manager.file_writer.write_file(
                        filename=filename,
                        content=code
                    )
                    if save_result["success"]:
                        saved_files.append(save_result["filepath"])
                        await self._report_progress(task, 0.7, f"Файл сохранён: {filename}")

                # Execute Python code if requested
                if should_execute and self._detect_language(code, task.description) == "python":
                    await self._report_progress(task, 0.8, "Выполняю код...")
                    exec_result = await self._tool_manager.code_exec.execute_python(code)
                    execution_results.append(exec_result)

                    if exec_result.get("success"):
                        await self._report_progress(task, 0.9, "Код выполнен успешно!")
                    else:
                        await self._report_progress(task, 0.9, f"Ошибка выполнения: {exec_result.get('stderr', '')[:100]}")

        await self._report_progress(task, 0.95, "Формирую отчёт...")

        result_data = {
            "type": "code",
            "task": task.description,
            "result": code_response,
            "code_blocks": code_blocks,
            "saved_files": saved_files,
            "execution_results": execution_results,
            "model": self._preferred_model,
            "timestamp": datetime.now().isoformat()
        }

        # Build human-readable summary
        summary_parts = [code_response]
        if saved_files:
            summary_parts.append(f"\n\n📁 **Файлы сохранены:**\n" + "\n".join(f"• `{f}`" for f in saved_files))
        if execution_results:
            for er in execution_results:
                if er.get("success"):
                    out = er.get("stdout", "").strip()
                    summary_parts.append(f"\n\n✅ **Результат выполнения:**\n```\n{out}\n```" if out else "\n\n✅ Код выполнен успешно (нет вывода)")
                else:
                    err = er.get("stderr", er.get("error", "Неизвестная ошибка"))
                    summary_parts.append(f"\n\n❌ **Ошибка выполнения:**\n```\n{err}\n```")

        result_data["result"] = "".join(summary_parts)
        return result_data


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
    """Creates designs, presentations, and HTML mockups using creative LLM + PresentationTool."""

    def __init__(self):
        super().__init__(
            name="Designer",
            role="Дизайнер",
            capabilities=[
                "UI/UX дизайн",
                "Создание презентаций (HTML/PPTX)",
                "Создание макетов",
                "Прототипирование",
                "Дизайн-системы",
                "Адаптивный дизайн",
                "Брендинг"
            ]
        )
        self._preferred_model = AGENT_MODELS["designer"]

    def _is_presentation_task(self, desc: str) -> bool:
        """Check if task is about creating a presentation."""
        keywords = [
            "презентац", "presentation", "слайд", "slide", "pptx", "powerpoint",
            "доклад", "report", "pitch", "питч"
        ]
        return any(kw in desc.lower() for kw in keywords)

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.1, "Изучение требований...")

        if not self._llm_client:
            return {"type": "design", "task": task.description,
                    "result": f"[Designer] Дизайн: {task.description}",
                    "timestamp": datetime.now().isoformat()}

        # Check if it's a presentation task
        if self._is_presentation_task(task.description):
            return await self._create_presentation(task)

        # Regular design task
        await self._report_progress(task, 0.4, "Создание концепции...")
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

    async def _create_presentation(self, task: Task) -> Any:
        """Create a real presentation file."""
        await self._report_progress(task, 0.2, "Генерирую структуру презентации...")

        # Ask LLM to generate slide content in JSON format
        slides_json = await self.ask_llm(
            f"Создай структуру презентации для: {task.description}\n\n"
            f"Верни JSON-массив слайдов в формате:\n"
            f'[{{"title": "Заголовок слайда", "content": "Содержание слайда"}}, ...]\n'
            f"Создай 5-8 слайдов. Верни ТОЛЬКО JSON без пояснений.",
            system_prompt=(
                "Ты профессиональный дизайнер презентаций. "
                "Создавай структурированные, информативные презентации. "
                "Отвечай ТОЛЬКО валидным JSON-массивом."
            ),
            model=self._preferred_model
        )

        await self._report_progress(task, 0.5, "Создаю файл презентации...")

        # Parse slides
        import json
        import re
        slides = []
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', slides_json, re.DOTALL)
            if json_match:
                slides = json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"Failed to parse slides JSON: {e}")
            # Fallback: create basic slides from text
            lines = slides_json.strip().split('\n')
            for i, line in enumerate(lines[:8]):
                if line.strip():
                    slides.append({"title": f"Слайд {i+1}", "content": line.strip()})

        if not slides:
            slides = [
                {"title": "Введение", "content": task.description},
                {"title": "Основные моменты", "content": "Ключевые аспекты темы"},
                {"title": "Заключение", "content": "Выводы и рекомендации"}
            ]

        # Extract title from task description
        title = task.description[:60] if len(task.description) > 60 else task.description
        # Clean up title
        for prefix in ["создай презентацию", "сделай презентацию", "presentation about", "create presentation"]:
            if prefix in title.lower():
                title = title[title.lower().index(prefix) + len(prefix):].strip(" :о")
                break

        # Create presentation file
        if self._tool_manager:
            await self._report_progress(task, 0.7, "Сохраняю файл...")

            # Try PPTX first, fallback to HTML
            pptx_result = await self._tool_manager.presentation.create_pptx_presentation(
                title=title or "Презентация",
                slides=slides
            )

            if pptx_result["success"]:
                filepath = pptx_result["filepath"]
                fmt = pptx_result["format"]
                await self._report_progress(task, 0.95, f"Презентация создана ({fmt})!")

                return {
                    "type": "presentation",
                    "task": task.description,
                    "result": (
                        f"✅ Презентация создана!\n\n"
                        f"📊 **Формат:** {fmt.upper()}\n"
                        f"📁 **Файл:** `{filepath}`\n"
                        f"🎯 **Слайдов:** {pptx_result['slides_count']}\n\n"
                        f"Слайды:\n" + "\n".join(f"• {s.get('title', '')}" for s in slides)
                    ),
                    "filepath": filepath,
                    "slides_count": pptx_result["slides_count"],
                    "format": fmt,
                    "model": self._preferred_model,
                    "timestamp": datetime.now().isoformat()
                }

        # Fallback: return text description
        await self._report_progress(task, 0.95, "Презентация готова (текстовый формат)!")
        slides_text = "\n".join(f"**{s.get('title', '')}**\n{s.get('content', '')}" for s in slides)
        return {
            "type": "presentation",
            "task": task.description,
            "result": f"📊 Структура презентации '{title}':\n\n{slides_text}",
            "model": self._preferred_model,
            "timestamp": datetime.now().isoformat()
        }


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
        """Generate image and save to temp file. Returns file:// path."""
        import aiohttp
        import tempfile

        # 1. HuggingFace Inference API (FREE, no key needed for some models)
        hf_token = os.getenv("HF_TOKEN", "")
        try:
            headers = {"Content-Type": "application/json"}
            if hf_token:
                headers["Authorization"] = f"Bearer {hf_token}"
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                    headers=headers,
                    json={"inputs": prompt},
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200 and resp.content_type.startswith("image"):
                        img_bytes = await resp.read()
                        if len(img_bytes) > 1000:
                            fd, path = tempfile.mkstemp(suffix='.png')
                            with os.fdopen(fd, 'wb') as f:
                                f.write(img_bytes)
                            logger.info(f"Image generated via HuggingFace: {path}")
                            return f"file://{path}"
                    else:
                        logger.warning(f"HuggingFace: status={resp.status}")
        except Exception as e:
            logger.warning(f"HuggingFace image: {e}")

        # 2. OpenAI DALL-E
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
