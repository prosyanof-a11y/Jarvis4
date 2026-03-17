"""
Master Agent — Controls everything in the AI Office.

Responsibilities:
- Receives tasks from user
- Analyzes and decomposes complex tasks
- Delegates subtasks to specialized agents
- Monitors execution progress
- Synthesizes final results
- Can override agent decisions
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_agent import BaseAgent, Task, AgentState, NotificationType

logger = logging.getLogger(__name__)


class MasterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Master",
            role="Главный управляющий AI Office",
            capabilities=[
                "Анализ и декомпозиция задач",
                "Координация всех агентов",
                "Мониторинг прогресса",
                "Синтез результатов",
                "Стратегическое планирование",
                "Управление приоритетами",
                "Создание новых агентов",
                "Оптимизация процессов"
            ]
        )
        self.agent_manager = None
        self.task_history: List[Dict[str, Any]] = []

    def set_agent_manager(self, manager):
        self.agent_manager = manager

    async def _execute_task(self, task: Task) -> Any:
        """Analyze task, delegate to agents, synthesize results."""
        # Step 1: Analyze
        await self._report_progress(task, 0.1, "Анализирую задачу...")
        plan = self._create_execution_plan(task.description)

        # Step 2: Delegate
        await self._report_progress(task, 0.2, f"План создан: {len(plan)} подзадач")
        results = []

        for i, subtask_info in enumerate(plan):
            progress = 0.2 + (0.7 * (i / len(plan)))
            agent_type = subtask_info["agent"]
            desc = subtask_info["description"]

            await self._report_progress(task, progress, f"Делегирую: {agent_type}: {desc[:50]}...")

            agent = self.agent_manager.get_agent(agent_type) if self.agent_manager else None
            if agent:
                subtask = Task(description=desc, assigned_to=agent_type, parent_task_id=task.id)
                try:
                    await agent.think(subtask)
                    result = await agent.work(subtask)
                    results.append({"agent": agent_type, "result": result, "success": True})

                    # Send subtask result to Master's Telegram
                    await self._send_subtask_result(agent_type, result)

                except Exception as e:
                    results.append({"agent": agent_type, "error": str(e), "success": False})
                    await self.notify(NotificationType.TASK_ERROR, {
                        "message": f"Ошибка {agent_type}: {str(e)[:100]}"
                    })
            else:
                results.append({"agent": agent_type, "error": "Агент не найден", "success": False})

        # Step 3: Synthesize
        await self._report_progress(task, 0.95, "Синтезирую результаты...")
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        final = {
            "task": task.description,
            "summary": f"Выполнено {len(successful)}/{len(results)} подзадач",
            "results": [{"agent": r["agent"], "result": r["result"]} for r in successful],
            "errors": [{"agent": r["agent"], "error": r["error"]} for r in failed],
            "completed_at": datetime.now().isoformat()
        }

        self.task_history.append(final)
        return final

    async def _send_subtask_result(self, agent_type: str, result):
        """Send subtask result to Master's Telegram chat, including images."""
        if not self._telegram_notifier:
            return

        try:
            # Check for image URL in result
            image_url = None
            result_text = ""

            if isinstance(result, dict):
                image_url = result.get("image_url")
                result_text = result.get("result", str(result))
            else:
                result_text = str(result)

            # Send image if available
            if image_url and hasattr(self._telegram_notifier, 'bot') and self._telegram_notifier.bot:
                for cid in self._telegram_notifier.chat_ids:
                    try:
                        await self._telegram_notifier.bot.send_photo(
                            chat_id=cid,
                            photo=image_url,
                            caption=f"🎨 {agent_type}: изображение создано"
                        )
                    except Exception as e:
                        # If photo fails, send URL as text
                        await self._telegram_notifier.bot.send_message(
                            chat_id=cid,
                            text=f"🎨 {agent_type}: {image_url}"
                        )
            else:
                # Send text result
                if len(result_text) > 3000:
                    result_text = result_text[:3000] + "..."
                await self.notify(NotificationType.TASK_COMPLETED, {
                    "message": f"📄 {agent_type} завершил:\n{result_text[:500]}"
                })
        except Exception as e:
            self.logger.error(f"Send subtask result error: {e}")

    def _create_execution_plan(self, description: str) -> List[Dict[str, str]]:
        """Create execution plan based on task description keywords."""
        desc = description.lower()
        plan = []

        keyword_map = {
            "researcher": ["исследов", "research", "найти", "поиск", "search", "информац", "узнать"],
            "programmer": ["код", "программ", "code", "develop", "скрипт", "api", "бот", "сайт", "приложен"],
            "analyst": ["анализ", "analys", "данн", "data", "статистик", "отчет", "report"],
            "designer": ["дизайн", "design", "интерфейс", "ui", "ux", "макет", "layout"],
            "artist": ["изображ", "image", "картин", "рисун", "иллюстрац", "art", "фото"],
            "marketer": ["маркетинг", "market", "продвиж", "реклам", "пост", "контент", "seo"],
        }

        for agent, keywords in keyword_map.items():
            if any(kw in desc for kw in keywords):
                plan.append({"agent": agent, "description": f"{agent}: {description}"})

        if not plan:
            plan = [
                {"agent": "researcher", "description": f"Исследование: {description}"},
                {"agent": "analyst", "description": f"Анализ: {description}"},
            ]

        return plan

    async def get_system_report(self) -> Dict[str, Any]:
        """Generate full system status report."""
        report = {
            "master_state": self.state.value,
            "tasks_completed": len(self.task_history),
            "agents": {},
            "timestamp": datetime.now().isoformat()
        }
        if self.agent_manager:
            for name, agent in self.agent_manager.agents.items():
                report["agents"][name] = agent.get_status()
        return report
