"""
BaseAgent — Foundation for all AI agents in the AI Office.

Each agent:
- Has a unique Telegram bot
- Can receive commands from the user
- Must send status updates
- Follows the notification lifecycle:
  1. Confirm task receipt
  2. Start execution
  3. Send progress updates
  4. Send intermediate results
  5. Send final result
  6. Report errors if they occur
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
import asyncio
import logging
import uuid
from datetime import datetime


class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    FINISHED = "finished"
    ERROR = "error"


class NotificationType(Enum):
    TASK_RECEIVED = "task_received"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_ERROR = "task_error"
    STATUS_UPDATE = "status_update"


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    assigned_to: Optional[str] = None
    state: AgentState = AgentState.IDLE
    result: Optional[Any] = None
    progress: float = 0.0
    error: Optional[str] = None
    parent_task_id: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BaseAgent:
    """
    Base class for all AI agents in the AI Office.

    Supports:
    - Task lifecycle management with notifications
    - Individual Telegram bot integration
    - Progress reporting
    - Self-learning through memory system
    - Continuous work loop
    """

    def __init__(self, name: str, role: str, capabilities: List[str]):
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.state = AgentState.IDLE
        self.task_queue: List[Task] = []
        self.current_task: Optional[Task] = None
        self.completed_tasks: List[Dict[str, Any]] = []
        self.telegram_bot_token: Optional[str] = None
        self.telegram_chat_ids: List[int] = []

        self.logger = logging.getLogger(f"agent.{name}")
        self._notification_callbacks: List[Callable] = []
        self._telegram_notifier = None
        self._running = False
        self._memory_system = None
        self._llm_client = None  # OpenRouter LLM client

    # ─── LLM / AI Integration ─────────────────────────────────────

    def set_llm_client(self, llm_client):
        """Set the LLM client (OpenRouter) for AI-powered task execution."""
        self._llm_client = llm_client

    async def ask_llm(self, prompt: str, system_prompt: str = None,
                      model: str = None) -> str:
        """Ask the LLM a question. Uses OpenRouter API."""
        if not self._llm_client:
            return f"[{self.name}] LLM not configured"
        
        if not system_prompt:
            system_prompt = (
                f"You are {self.name}, an AI agent with role: {self.role}. "
                f"Your capabilities: {', '.join(self.capabilities)}. "
                f"Respond in Russian. Be concise and professional."
            )
        
        response = await self._llm_client.chat(
            message=prompt,
            model=model,
            system_prompt=system_prompt
        )
        return response.content

    # ─── Telegram Integration ──────────────────────────────────────

    def set_telegram_notifier(self, notifier):
        """Set the Telegram notifier for this agent."""
        self._telegram_notifier = notifier

    def set_memory_system(self, memory_system):
        """Set the memory system for self-learning."""
        self._memory_system = memory_system

    def register_notification_callback(self, callback: Callable):
        """Register a callback for agent notifications."""
        self._notification_callbacks.append(callback)

    async def notify(self, ntype: NotificationType, data: Dict[str, Any] = None):
        """Send notification about agent activity. Only COMPLETED and ERROR go to Telegram."""
        notification = {
            "agent_id": self.id,
            "agent_name": self.name,
            "type": ntype.value,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        self.logger.info(f"[{self.name}] {ntype.value}: {data}")

        for cb in self._notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(notification)
                else:
                    cb(notification)
            except Exception as e:
                self.logger.error(f"Notification callback error: {e}")

        # Only send COMPLETED and ERROR to Telegram (no intermediate spam)
        if self._telegram_notifier and ntype in (NotificationType.TASK_COMPLETED, NotificationType.TASK_ERROR):
            try:
                await self._telegram_notifier.send_notification(notification)
            except Exception as e:
                self.logger.error(f"Telegram notification error: {e}")

    # ─── Task Lifecycle ────────────────────────────────────────────

    async def assign_task(self, task: Task):
        """Step 1: Confirm task receipt."""
        task.assigned_to = self.name
        self.task_queue.append(task)
        await self.notify(NotificationType.TASK_RECEIVED, {
            "task_id": task.id,
            "description": task.description,
            "message": f"📋 {self.name} получил задачу: {task.description}"
        })

    async def think(self, task: Task):
        """Step 2: Analyze the task."""
        self.state = AgentState.THINKING
        self.current_task = task
        task.state = AgentState.THINKING
        await self.notify(NotificationType.TASK_STARTED, {
            "task_id": task.id,
            "message": f"🧠 {self.name} анализирует задачу..."
        })
        await asyncio.sleep(0.1)

    async def work(self, task: Task) -> Any:
        """Steps 3-5: Execute task with progress updates and final result."""
        self.state = AgentState.WORKING
        task.state = AgentState.WORKING
        task.started_at = datetime.now()

        await self.notify(NotificationType.TASK_PROGRESS, {
            "task_id": task.id,
            "progress": 0.0,
            "message": f"⚙️ {self.name} приступил к выполнению..."
        })

        try:
            result = await self._execute_task(task)
            task.result = result
            task.state = AgentState.FINISHED
            task.progress = 1.0
            task.completed_at = datetime.now()
            self.state = AgentState.FINISHED

            # Store in completed tasks
            self.completed_tasks.append({
                "task_id": task.id,
                "description": task.description,
                "result": str(result)[:500],
                "success": True,
                "completed_at": datetime.now().isoformat()
            })

            # Self-learning: store in memory
            if self._memory_system:
                await self._memory_system.store_task_result(
                    agent_name=self.name,
                    task_description=task.description,
                    result=str(result),
                    success=True
                )

            await self.notify(NotificationType.TASK_COMPLETED, {
                "task_id": task.id,
                "result": str(result)[:500],
                "message": f"✅ {self.name} завершил задачу!"
            })
            return result

        except Exception as e:
            task.state = AgentState.ERROR
            task.error = str(e)
            self.state = AgentState.ERROR

            self.completed_tasks.append({
                "task_id": task.id,
                "description": task.description,
                "error": str(e),
                "success": False,
                "completed_at": datetime.now().isoformat()
            })

            # Step 6: Report errors
            await self.notify(NotificationType.TASK_ERROR, {
                "task_id": task.id,
                "error": str(e),
                "message": f"❌ {self.name}: ошибка — {str(e)}"
            })
            raise

    async def _execute_task(self, task: Task) -> Any:
        """Override in subclasses for actual task execution."""
        await self._report_progress(task, 0.5, "Обработка...")
        await asyncio.sleep(0.1)
        return f"[{self.name}] Выполнено: {task.description}"

    async def _report_progress(self, task: Task, progress: float, message: str = ""):
        """Send intermediate progress update."""
        task.progress = progress
        task.updated_at = datetime.now()
        await self.notify(NotificationType.TASK_PROGRESS, {
            "task_id": task.id,
            "progress": progress,
            "message": f"📊 {self.name}: {message} ({int(progress * 100)}%)"
        })

    # ─── Work Loop ─────────────────────────────────────────────────

    async def start_working(self):
        """Continuous work loop — processes tasks from queue."""
        self._running = True
        self.logger.info(f"{self.name} started work loop")
        while self._running:
            if self.task_queue:
                task = self.task_queue.pop(0)
                self.current_task = task
                try:
                    await self.think(task)
                    await self.work(task)
                except Exception as e:
                    self.logger.error(f"Task error: {e}")
                finally:
                    self.current_task = None
            else:
                self.state = AgentState.IDLE
                await asyncio.sleep(0.5)

    async def stop_working(self):
        """Stop the work loop."""
        self._running = False

    # ─── Info ──────────────────────────────────────────────────────

    def get_info(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "capabilities": self.capabilities,
            "state": self.state.value,
            "has_telegram": self.telegram_bot_token is not None,
            "task_queue_length": len(self.task_queue),
            "completed_tasks_count": len(self.completed_tasks),
            "current_task": self.current_task.description if self.current_task else None
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "state": self.state.value,
            "capabilities": self.capabilities,
            "task_queue_length": len(self.task_queue),
            "current_task": self.current_task.description if self.current_task else None
        }
