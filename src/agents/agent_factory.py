"""
Agent Factory — Creates new agents dynamically.

Responsibilities:
- Create new specialized agents on demand
- Configure agent capabilities
- Register agents in the system
- Manage agent lifecycle
"""

import logging
from typing import Dict, Any, Optional, Type
from datetime import datetime

from .base_agent import BaseAgent, Task

logger = logging.getLogger(__name__)


class DynamicAgent(BaseAgent):
    """A dynamically created agent with custom capabilities."""

    def __init__(self, name: str, role: str, capabilities: list, instructions: str = ""):
        super().__init__(name=name, role=role, capabilities=capabilities)
        self.instructions = instructions

    async def _execute_task(self, task: Task) -> Any:
        await self._report_progress(task, 0.3, "Выполняю по инструкциям...")
        await self._report_progress(task, 0.7, "Обрабатываю результат...")
        return f"[{self.name}] Выполнено: {task.description}"


class AgentFactory(BaseAgent):
    """Factory agent that creates new agents."""

    def __init__(self):
        super().__init__(
            name="AgentFactory",
            role="Фабрика агентов",
            capabilities=[
                "Создание новых агентов",
                "Настройка возможностей",
                "Регистрация в системе",
                "Управление жизненным циклом агентов"
            ]
        )
        self.created_agents: Dict[str, BaseAgent] = {}
        self.agent_manager = None

    def set_agent_manager(self, manager):
        self.agent_manager = manager

    async def _execute_task(self, task: Task) -> Any:
        """Create a new agent based on task description."""
        await self._report_progress(task, 0.3, "Анализирую требования к агенту...")

        # Parse agent creation request
        desc = task.description.lower()
        agent_config = self._parse_agent_request(desc)

        await self._report_progress(task, 0.6, f"Создаю агента: {agent_config['name']}...")

        new_agent = self.create_agent(
            name=agent_config["name"],
            role=agent_config["role"],
            capabilities=agent_config["capabilities"],
            instructions=agent_config.get("instructions", "")
        )

        await self._report_progress(task, 0.9, "Регистрирую агента в системе...")

        if self.agent_manager:
            self.agent_manager.register_agent(agent_config["name"].lower(), new_agent)

        return {
            "status": "created",
            "agent_name": new_agent.name,
            "agent_role": new_agent.role,
            "capabilities": new_agent.capabilities,
            "created_at": datetime.now().isoformat()
        }

    def create_agent(self, name: str, role: str, capabilities: list,
                     instructions: str = "") -> DynamicAgent:
        """Create a new dynamic agent."""
        agent = DynamicAgent(
            name=name,
            role=role,
            capabilities=capabilities,
            instructions=instructions
        )
        self.created_agents[name.lower()] = agent
        logger.info(f"AgentFactory created new agent: {name} ({role})")
        return agent

    def _parse_agent_request(self, description: str) -> Dict[str, Any]:
        """Parse agent creation request from description."""
        # Simple keyword-based parsing
        if "переводчик" in description or "translat" in description:
            return {
                "name": "Translator",
                "role": "Переводчик",
                "capabilities": ["Перевод текстов", "Мультиязычность", "Локализация"]
            }
        elif "тестировщик" in description or "test" in description or "qa" in description:
            return {
                "name": "QATester",
                "role": "Тестировщик",
                "capabilities": ["Тестирование", "Поиск багов", "Автотесты"]
            }
        elif "писатель" in description or "writer" in description or "копирайт" in description:
            return {
                "name": "Writer",
                "role": "Копирайтер",
                "capabilities": ["Написание текстов", "Редактирование", "SEO-копирайтинг"]
            }
        else:
            return {
                "name": "CustomAgent",
                "role": "Специализированный агент",
                "capabilities": ["Выполнение пользовательских задач"],
                "instructions": description
            }

    def get_created_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get info about all created agents."""
        return {
            name: agent.get_info()
            for name, agent in self.created_agents.items()
        }
