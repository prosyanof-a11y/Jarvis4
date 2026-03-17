"""
Task Engine — Central task processing and routing system.

Handles:
- Task creation and queuing
- Task delegation to Master Agent
- Task status tracking
- Task history
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.agents.base_agent import Task, AgentState

logger = logging.getLogger(__name__)


class TaskEngine:
    """Central task processing engine."""

    def __init__(self, agent_manager, memory_system=None):
        self.agent_manager = agent_manager
        self.memory_system = memory_system
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.task_queue: List[Task] = []
        self._running = False

    async def start(self):
        """Start the task processing loop."""
        logger.info("Task Engine started")
        self._running = True
        asyncio.create_task(self._process_loop())

    async def stop(self):
        """Stop the task engine."""
        self._running = False
        logger.info("Task Engine stopped")

    async def submit_task(self, description: str, target_agent: str = None) -> Task:
        """Submit a new task to the system."""
        task = Task(description=description, assigned_to=target_agent)
        self.task_queue.append(task)
        self.active_tasks[task.id] = task
        logger.info(f"Task submitted: {task.id} - {description[:80]}")
        return task

    async def execute_task(self, task: Task) -> Any:
        """Execute a task through the agent system."""
        logger.info(f"Executing task: {task.description}")

        # Check memory for similar past tasks
        if self.memory_system:
            past = await self.memory_system.search_similar(task.description)
            if past:
                logger.info(f"Found similar past task in memory")

        # Route to specific agent or Master
        if task.assigned_to:
            agent = self.agent_manager.get_agent(task.assigned_to)
            if agent:
                await agent.think(task)
                result = await agent.work(task)
            else:
                result = f"Агент '{task.assigned_to}' не найден"
        else:
            # Delegate to Master Agent
            master = self.agent_manager.get_agent("master")
            if master:
                await master.think(task)
                result = await master.work(task)
            else:
                result = "Master Agent не доступен"

        # Finalize
        task.state = AgentState.FINISHED
        task.result = result
        task.completed_at = datetime.now()

        if task.id in self.active_tasks:
            del self.active_tasks[task.id]
        self.completed_tasks.append(task)

        # Store in memory
        if self.memory_system:
            await self.memory_system.store_task_result(
                agent_name="system",
                task_description=task.description,
                result=str(result),
                success=True
            )

        return result

    async def _process_loop(self):
        """Continuously process queued tasks."""
        while self._running:
            if self.task_queue:
                task = self.task_queue.pop(0)
                try:
                    await self.execute_task(task)
                except Exception as e:
                    logger.error(f"Task execution error: {e}")
                    task.state = AgentState.ERROR
                    task.error = str(e)
            else:
                await asyncio.sleep(0.2)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        if task_id in self.active_tasks:
            t = self.active_tasks[task_id]
            return {"id": t.id, "description": t.description, "state": t.state.value,
                    "progress": t.progress, "assigned_to": t.assigned_to}
        for t in self.completed_tasks:
            if t.id == task_id:
                return {"id": t.id, "description": t.description, "state": t.state.value,
                        "result": t.result, "assigned_to": t.assigned_to}
        return None

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks."""
        tasks = []
        for t in self.active_tasks.values():
            tasks.append({"id": t.id, "description": t.description,
                         "state": t.state.value, "assigned_to": t.assigned_to})
        for t in self.completed_tasks:
            tasks.append({"id": t.id, "description": t.description,
                         "state": t.state.value, "result": str(t.result)[:200]})
        return tasks
