"""
Project Manager Agent — Manages tasks, priorities, and deadlines.

Responsibilities:
- Task prioritization and scheduling
- Resource allocation
- Progress tracking across all agents
- Deadline management
- Risk assessment
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

from .base_agent import BaseAgent, Task, AgentState, NotificationType

logger = logging.getLogger(__name__)


class ProjectManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ProjectManager",
            role="Менеджер проектов",
            capabilities=[
                "Управление задачами",
                "Приоритизация",
                "Планирование сроков",
                "Распределение ресурсов",
                "Отслеживание прогресса",
                "Оценка рисков",
                "Генерация отчётов"
            ]
        )
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.task_registry: Dict[str, Dict[str, Any]] = {}

    async def _execute_task(self, task: Task) -> Any:
        """Manage and track project tasks."""
        await self._report_progress(task, 0.2, "Анализирую проект...")

        project_id = task.id
        self.projects[project_id] = {
            "id": project_id,
            "description": task.description,
            "status": "in_progress",
            "created_at": datetime.now().isoformat(),
            "tasks": [],
            "progress": 0.0
        }

        await self._report_progress(task, 0.5, "Создаю план проекта...")

        plan = {
            "project": task.description,
            "phases": [
                {"name": "Исследование", "duration": "1-2 дня", "priority": "high"},
                {"name": "Планирование", "duration": "1 день", "priority": "high"},
                {"name": "Разработка", "duration": "3-5 дней", "priority": "medium"},
                {"name": "Тестирование", "duration": "1-2 дня", "priority": "medium"},
                {"name": "Деплой", "duration": "1 день", "priority": "low"},
            ],
            "risks": ["Нехватка данных", "Технические сложности", "Изменение требований"],
            "created_at": datetime.now().isoformat()
        }

        await self._report_progress(task, 0.9, "Финализирую план...")

        self.projects[project_id]["plan"] = plan
        self.projects[project_id]["status"] = "planned"

        return plan

    def register_task(self, task_id: str, agent_name: str, description: str):
        """Register a task for tracking."""
        self.task_registry[task_id] = {
            "agent": agent_name,
            "description": description,
            "status": "assigned",
            "registered_at": datetime.now().isoformat()
        }

    def update_task_status(self, task_id: str, status: str, progress: float = 0.0):
        """Update tracked task status."""
        if task_id in self.task_registry:
            self.task_registry[task_id]["status"] = status
            self.task_registry[task_id]["progress"] = progress

    def get_project_report(self) -> Dict[str, Any]:
        """Generate project status report."""
        return {
            "total_projects": len(self.projects),
            "tracked_tasks": len(self.task_registry),
            "projects": self.projects,
            "timestamp": datetime.now().isoformat()
        }
