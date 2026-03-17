"""
FastAPI Server — REST API for the AI Office system.

Endpoints:
- POST /task — Submit a new task
- GET /status — System status
- GET /agents — List all agents
- GET /tasks — List all tasks
- GET /task/{id} — Get task status
- POST /assign — Assign task to specific agent
- GET /memory/stats — Memory statistics
- POST /voice — Voice input processing
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Jarvis4 AI Office",
    description="Autonomous AI Organization REST API",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# These will be set by the main application
task_engine = None
agent_manager = None
memory_system = None
voice_system = None


class TaskRequest(BaseModel):
    description: str
    target_agent: Optional[str] = None


class AssignRequest(BaseModel):
    agent_name: str
    description: str


class VoiceRequest(BaseModel):
    audio_path: str


def set_dependencies(te, am, ms, vs=None):
    """Set dependencies from the main application."""
    global task_engine, agent_manager, memory_system, voice_system
    task_engine = te
    agent_manager = am
    memory_system = ms
    voice_system = vs


@app.get("/")
async def root():
    return {
        "name": "Jarvis4 AI Office",
        "version": "4.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/task")
async def submit_task(request: TaskRequest):
    if not task_engine:
        raise HTTPException(500, "Task engine not initialized")
    task = await task_engine.submit_task(request.description, request.target_agent)
    return {"task_id": task.id, "description": task.description, "status": "queued"}


@app.get("/status")
async def system_status():
    if not agent_manager:
        raise HTTPException(500, "Agent manager not initialized")
    return {
        "agents": agent_manager.get_all_statuses(),
        "tasks": task_engine.get_all_tasks() if task_engine else [],
        "memory": memory_system.get_stats() if memory_system else {},
        "timestamp": datetime.now().isoformat()
    }


@app.get("/agents")
async def list_agents():
    if not agent_manager:
        raise HTTPException(500, "Agent manager not initialized")
    return {"agents": agent_manager.get_all_statuses()}


@app.get("/tasks")
async def list_tasks():
    if not task_engine:
        raise HTTPException(500, "Task engine not initialized")
    return {"tasks": task_engine.get_all_tasks()}


@app.get("/task/{task_id}")
async def get_task(task_id: str):
    if not task_engine:
        raise HTTPException(500, "Task engine not initialized")
    status = task_engine.get_task_status(task_id)
    if not status:
        raise HTTPException(404, "Task not found")
    return status


@app.post("/assign")
async def assign_task(request: AssignRequest):
    if not task_engine or not agent_manager:
        raise HTTPException(500, "System not initialized")
    agent = agent_manager.get_agent(request.agent_name)
    if not agent:
        raise HTTPException(404, f"Agent '{request.agent_name}' not found")
    task = await task_engine.submit_task(request.description, request.agent_name)
    return {"task_id": task.id, "agent": request.agent_name, "status": "assigned"}


@app.get("/memory/stats")
async def memory_stats():
    if not memory_system:
        raise HTTPException(500, "Memory system not initialized")
    return memory_system.get_stats()


@app.post("/voice")
async def process_voice(request: VoiceRequest):
    if not voice_system:
        raise HTTPException(500, "Voice system not available")
    text = await voice_system.speech_to_text_from_file(request.audio_path)
    if not text:
        raise HTTPException(400, "Could not recognize speech")
    task = await task_engine.submit_task(text)
    return {"recognized_text": text, "task_id": task.id}
