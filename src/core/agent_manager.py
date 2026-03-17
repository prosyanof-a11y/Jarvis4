"""
Agent Manager — Manages all AI agents in the system.

Responsibilities:
- Initialize and register agents
- Start/stop agent work loops
- Provide agent lookup
- Report agent statuses
- Configure LLM (OpenRouter) for all agents
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from src.agents.base_agent import BaseAgent
from src.agents.master_agent import MasterAgent
from src.agents.project_manager_agent import ProjectManagerAgent
from src.agents.agent_factory import AgentFactory
from src.agents.worker_agents import (
    ResearcherAgent, ProgrammerAgent, AnalystAgent,
    DesignerAgent, ArtistAgent, MarketerAgent
)
from src.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AgentManager:
    """Central manager for all AI agents."""

    def __init__(self, memory_system=None, llm_client: LLMClient = None):
        self.memory_system = memory_system
        self.llm_client = llm_client
        self.agents: Dict[str, BaseAgent] = {}
        self._initialized = False
        self._agent_tasks: List[asyncio.Task] = []

    def set_llm_client(self, llm_client: LLMClient):
        """Set LLM client and propagate to all agents."""
        self.llm_client = llm_client
        for agent in self.agents.values():
            agent.set_llm_client(llm_client)
        logger.info(f"LLM client set for all agents (model: {llm_client.default_model})")

    async def initialize(self):
        """Initialize all core agents."""
        if self._initialized:
            return

        logger.info("Initializing AI agents...")

        # Core agents
        self.agents["master"] = MasterAgent()
        self.agents["project_manager"] = ProjectManagerAgent()
        self.agents["agent_factory"] = AgentFactory()

        # Worker agents
        self.agents["researcher"] = ResearcherAgent()
        self.agents["programmer"] = ProgrammerAgent()
        self.agents["analyst"] = AnalystAgent()
        self.agents["designer"] = DesignerAgent()
        self.agents["artist"] = ArtistAgent()
        self.agents["marketer"] = MarketerAgent()

        # Set references
        self.agents["master"].set_agent_manager(self)
        self.agents["agent_factory"].set_agent_manager(self)

        # Set memory system for all agents
        if self.memory_system:
            for agent in self.agents.values():
                agent.set_memory_system(self.memory_system)

        # Set LLM client for all agents
        if self.llm_client:
            for agent in self.agents.values():
                agent.set_llm_client(self.llm_client)

        self._initialized = True
        logger.info(f"Initialized {len(self.agents)} agents")

    def register_agent(self, name: str, agent: BaseAgent):
        """Register a new agent (used by AgentFactory)."""
        self.agents[name] = agent
        if self.memory_system:
            agent.set_memory_system(self.memory_system)
        logger.info(f"Registered new agent: {name}")

    async def start_all(self):
        """Start work loops for all agents."""
        if not self._initialized:
            await self.initialize()

        logger.info("Starting all agent work loops...")
        for name, agent in self.agents.items():
            task = asyncio.create_task(agent.start_working())
            self._agent_tasks.append(task)
            logger.info(f"Started: {name}")

    async def stop_all(self):
        """Stop all agent work loops."""
        logger.info("Stopping all agents...")
        for agent in self.agents.values():
            await agent.stop_working()
        for task in self._agent_tasks:
            task.cancel()
        self._agent_tasks.clear()

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name."""
        return self.agents.get(name)

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all agents."""
        return [agent.get_status() for agent in self.agents.values()]

    def get_agent_count(self) -> int:
        return len(self.agents)
