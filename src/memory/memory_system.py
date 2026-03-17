"""
Memory System — Self-learning with three memory types.

Memory types:
- Short-term memory: current session, recent tasks
- Long-term memory: persistent storage (ChromaDB)
- Knowledge base: learned facts and strategies

After each task:
- Analyze results
- Store successful strategies
- Reuse knowledge in future tasks
"""

import asyncio
import json
import logging
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. Using in-memory fallback.")


class MemorySystem:
    """
    Self-learning memory system with three tiers:
    
    1. Short-term memory — recent tasks, current context (in-memory)
    2. Long-term memory — persistent task history (ChromaDB)
    3. Knowledge base — learned strategies and facts (ChromaDB)
    """

    def __init__(self, persist_dir: str = "./data/memory",
                 knowledge_dir: str = "./data/knowledge"):
        self.persist_dir = persist_dir
        self.knowledge_dir = knowledge_dir
        self.short_term: deque = deque(maxlen=100)
        self.context: Dict[str, Any] = {}
        self.client = None
        self.collections: Dict[str, Any] = {}
        self._initialized = False
        os.makedirs(persist_dir, exist_ok=True)
        os.makedirs(knowledge_dir, exist_ok=True)

    async def initialize(self):
        if self._initialized:
            return
        logger.info("Initializing memory system...")
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(
                    path=self.persist_dir,
                    settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True)
                )
                self.collections["tasks"] = self.client.get_or_create_collection(
                    name="task_history")
                self.collections["knowledge"] = self.client.get_or_create_collection(
                    name="knowledge_base")
                self.collections["agent_memory"] = self.client.get_or_create_collection(
                    name="agent_memories")
                logger.info("ChromaDB initialized")
            except Exception as e:
                logger.error(f"ChromaDB init error: {e}")
                self._init_fallback()
        else:
            self._init_fallback()
        self._initialized = True

    def _init_fallback(self):
        self.collections = {"tasks": [], "knowledge": [], "agent_memory": []}

    # ─── Short-term Memory ─────────────────────────────────────────

    def remember_short(self, key: str, value: Any):
        entry = {"key": key, "value": value, "timestamp": datetime.now().isoformat()}
        self.short_term.append(entry)
        self.context[key] = value

    def recall_short(self, key: str) -> Optional[Any]:
        return self.context.get(key)

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        return list(self.short_term)[-n:]

    # ─── Long-term Memory ──────────────────────────────────────────

    async def store_task_result(self, agent_name: str, task_description: str,
                                result: str, success: bool = True):
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id, "agent": agent_name, "task": task_description,
            "result": result, "success": success,
            "timestamp": datetime.now().isoformat()
        }
        self.remember_short(f"task_{entry_id}", entry)

        if CHROMADB_AVAILABLE and self.client:
            try:
                self.collections["tasks"].add(
                    documents=[json.dumps(entry)],
                    metadatas=[{"agent": agent_name, "success": str(success)}],
                    ids=[entry_id]
                )
            except Exception as e:
                logger.error(f"Store error: {e}")
                self._fallback_store("tasks", entry)
        else:
            self._fallback_store("tasks", entry)

        if success:
            await self._learn_from_task(agent_name, task_description, result)

    async def search_similar(self, query: str, n: int = 5) -> Optional[Dict[str, Any]]:
        if not query:
            return None
        if CHROMADB_AVAILABLE and self.client:
            try:
                results = self.collections["tasks"].query(
                    query_texts=[query], n_results=n)
                if results and results["documents"] and results["documents"][0]:
                    return json.loads(results["documents"][0][0])
            except Exception as e:
                logger.error(f"Search error: {e}")
                return self._fallback_search("tasks", query)
        else:
            return self._fallback_search("tasks", query)
        return None

    # ─── Knowledge Base ────────────────────────────────────────────

    async def store_knowledge(self, fact: str, category: str = "general",
                              source: str = "system"):
        kid = str(uuid.uuid4())
        if CHROMADB_AVAILABLE and self.client:
            try:
                self.collections["knowledge"].add(
                    documents=[fact],
                    metadatas=[{"category": category, "source": source}],
                    ids=[kid]
                )
            except Exception as e:
                logger.error(f"Knowledge store error: {e}")
                self._fallback_store("knowledge", {"fact": fact, "category": category})
        else:
            self._fallback_store("knowledge", {"fact": fact, "category": category})

    async def search_knowledge(self, query: str, n: int = 5) -> List[str]:
        if not query:
            return []
        if CHROMADB_AVAILABLE and self.client:
            try:
                results = self.collections["knowledge"].query(
                    query_texts=[query], n_results=n)
                if results and results["documents"] and results["documents"][0]:
                    return results["documents"][0]
            except Exception as e:
                logger.error(f"Knowledge search error: {e}")
        return []

    # ─── Self-Learning ─────────────────────────────────────────────

    async def _learn_from_task(self, agent: str, task: str, result: str):
        """Extract and store reusable knowledge from completed tasks."""
        strategy = f"Agent '{agent}' completed: '{task[:100]}' -> success"
        await self.store_knowledge(fact=strategy, category="strategy", source=agent)

        experience = f"{agent}: {task[:80]} = {result[:80]}"
        if CHROMADB_AVAILABLE and self.client:
            try:
                self.collections["agent_memory"].add(
                    documents=[experience],
                    metadatas=[{"agent": agent}],
                    ids=[str(uuid.uuid4())]
                )
            except Exception as e:
                logger.error(f"Agent memory store error: {e}")

    # ─── Fallback Storage ──────────────────────────────────────────

    def _fallback_store(self, collection: str, entry: Dict[str, Any]):
        if collection in self.collections and isinstance(self.collections[collection], list):
            self.collections[collection].append(entry)

    def _fallback_search(self, collection: str, query: str) -> Optional[Dict[str, Any]]:
        if collection not in self.collections:
            return None
        items = self.collections[collection]
        if not isinstance(items, list):
            return None
        q = query.lower()
        for item in items:
            if isinstance(item, dict):
                for v in item.values():
                    if isinstance(v, str) and q in v.lower():
                        return item
        return None

    def get_stats(self) -> Dict[str, Any]:
        stats = {"short_term_count": len(self.short_term)}
        if CHROMADB_AVAILABLE and self.client:
            for name, col in self.collections.items():
                try:
                    stats[name] = col.count()
                except Exception:
                    stats[name] = 0
        else:
            for name, col in self.collections.items():
                stats[name] = len(col) if isinstance(col, list) else 0
        return stats

    async def reset(self):
        logger.warning("Resetting all memory!")
        self.short_term.clear()
        self.context.clear()
        if CHROMADB_AVAILABLE and self.client:
            for name in list(self.collections.keys()):
                try:
                    self.client.delete_collection(name)
                except Exception:
                    pass
            self._initialized = False
            await self.initialize()
        else:
            self._init_fallback()
