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
llm_client = None


class TaskRequest(BaseModel):
    description: str
    target_agent: Optional[str] = None
    model: Optional[str] = None  # Override AI model for this task


class AssignRequest(BaseModel):
    agent_name: str
    description: str


class VoiceRequest(BaseModel):
    audio_path: str


class ModelSelectRequest(BaseModel):
    model: str  # e.g. "claude-3.5-sonnet" or "openai/gpt-4o"


class AgentModelRequest(BaseModel):
    agent_name: str  # e.g. "programmer", "researcher"
    model: str  # e.g. "deepseek-coder" or "anthropic/claude-3.5-sonnet"


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    agent: Optional[str] = None


def set_dependencies(te, am, ms, vs=None, lc=None):
    """Set dependencies from the main application."""
    global task_engine, agent_manager, memory_system, voice_system, llm_client
    task_engine = te
    agent_manager = am
    memory_system = ms
    voice_system = vs
    llm_client = lc


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


# ─── LLM / OpenRouter Endpoints ───────────────────────────────────

@app.get("/llm/models")
async def list_models():
    """List available AI model shortcuts."""
    if not llm_client:
        raise HTTPException(500, "LLM client not initialized")
    from src.ai.llm_client import AVAILABLE_MODELS
    return {
        "current_model": llm_client.default_model,
        "available_models": AVAILABLE_MODELS,
        "api_configured": bool(llm_client.api_key),
    }


@app.post("/llm/model")
async def set_model(request: ModelSelectRequest):
    """Change the default AI model for all agents."""
    if not llm_client:
        raise HTTPException(500, "LLM client not initialized")
    old_model = llm_client.default_model
    llm_client.set_model(request.model)
    # Update all agents
    if agent_manager:
        agent_manager.set_llm_client(llm_client)
    return {
        "old_model": old_model,
        "new_model": llm_client.default_model,
        "status": "updated"
    }


@app.get("/llm/info")
async def llm_info():
    """Get current LLM configuration."""
    if not llm_client:
        raise HTTPException(500, "LLM client not initialized")
    return llm_client.get_info()


@app.post("/llm/chat")
async def llm_chat(request: ChatRequest):
    """Direct chat with the AI model."""
    if not llm_client:
        raise HTTPException(500, "LLM client not initialized")

    # If agent specified, use agent's ask_llm
    if request.agent and agent_manager:
        agent = agent_manager.get_agent(request.agent)
        if agent:
            response = await agent.ask_llm(
                request.message,
                system_prompt=request.system_prompt,
                model=request.model
            )
            return {"response": response, "agent": request.agent,
                    "model": request.model or llm_client.default_model}

    # Direct LLM call
    result = await llm_client.chat(
        message=request.message,
        model=request.model,
        system_prompt=request.system_prompt
    )
    return {
        "response": result.content,
        "model": result.model,
        "usage": result.usage
    }


@app.get("/llm/models/fetch")
async def fetch_openrouter_models():
    """Fetch all available models from OpenRouter API."""
    if not llm_client:
        raise HTTPException(500, "LLM client not initialized")
    models = await llm_client.fetch_available_models()
    return {"count": len(models), "models": models[:50]}  # Limit to 50


# ─── Agent Model Management ──────────────────────────────────────

@app.get("/agents/models")
async def get_agent_models():
    """Get current AI model for each agent."""
    if not agent_manager:
        raise HTTPException(500, "Agent manager not initialized")
    return {
        "agent_models": agent_manager.get_agent_models(),
        "available_models": agent_manager.get_available_models(),
    }


@app.post("/agents/model")
async def set_agent_model(request: AgentModelRequest):
    """Set AI model for a specific agent."""
    if not agent_manager:
        raise HTTPException(500, "Agent manager not initialized")

    agent = agent_manager.get_agent(request.agent_name)
    if not agent:
        raise HTTPException(404, f"Agent '{request.agent_name}' not found")

    old_model = agent.get_preferred_model()
    success = agent_manager.set_agent_model(request.agent_name, request.model)
    if not success:
        raise HTTPException(400, "Failed to set model")

    return {
        "agent": request.agent_name,
        "old_model": old_model,
        "new_model": request.model,
        "status": "updated"
    }


@app.get("/agents/{agent_name}/model")
async def get_single_agent_model(agent_name: str):
    """Get the current AI model for a specific agent."""
    if not agent_manager:
        raise HTTPException(500, "Agent manager not initialized")
    agent = agent_manager.get_agent(agent_name)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_name}' not found")
    return {
        "agent": agent_name,
        "model": agent.get_preferred_model(),
        "name": agent.name,
        "role": agent.role,
    }
