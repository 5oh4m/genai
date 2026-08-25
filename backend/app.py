"""
FastAPI Backend for AEGIS-AI — AI Agent Red Team vs Blue Team Payment Security Lab.
Provides REST endpoints for attack execution, defense management, metrics,
and WebSocket streaming for real-time transcript updates.
"""

import os
import sys
import uuid
import json
import asyncio
import logging
import datetime
from typing import Optional
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

load_dotenv()

# Ensure root directory is on Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from db import init_db, close_db, get_session
from db.models import AttackAttempt, DefenseRound
from red_team.config import (
    AttackConfig, BatchAttackConfig,
    ALL_TARGETS, ALL_OBJECTIVES, ALL_STRATEGIES, ALL_CONVERTERS,
)
from red_team.orchestrator import RedTeamOrchestrator
from blue_team.guard_rules import GuardRules
from blue_team.judge_agent import JudgeAgent
from blue_team.defense_wrapper import DefenseWrapper
from blue_team.feedback_loop import FeedbackLoop
from blue_team.evaluator import BlueTeamEvaluator
from blue_team.verdict import FeedbackEntry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------

class AppState:
    """Application-level singletons shared across requests."""
    guard_rules: GuardRules
    judge: Optional[JudgeAgent]
    feedback_loop: FeedbackLoop
    orchestrator: RedTeamOrchestrator
    evaluator: BlueTeamEvaluator
    ws_clients: list[WebSocket]
    openrouter_available: bool

app_state = AppState()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Check for OpenRouter API key
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    app_state.openrouter_available = bool(api_key)

    if not api_key:
        logger.warning(
            "\n" + "=" * 60 +
            "\n  OPENROUTER_API_KEY not set!" +
            "\n  Copy .env.example to .env and add your key." +
            "\n  Get one at https://openrouter.ai/keys" +
            "\n  The server will start but attacks will fail." +
            "\n" + "=" * 60
        )

    # Initialize DB
    try:
        await init_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Database init failed: {e}. Running in degraded mode.")

    # Initialize Blue Team components
    app_state.guard_rules = GuardRules()

    if app_state.openrouter_available:
        try:
            app_state.judge = JudgeAgent()
        except Exception as e:
            logger.warning(f"Judge agent init failed: {e}")
            app_state.judge = None
    else:
        app_state.judge = None

    app_state.feedback_loop = FeedbackLoop(app_state.guard_rules, app_state.judge)
    app_state.orchestrator = RedTeamOrchestrator(app_state.guard_rules, app_state.judge)
    app_state.evaluator = BlueTeamEvaluator()
    app_state.ws_clients = []

    logger.info("AEGIS-AI systems initialized.")

    yield

    # Shutdown
    await close_db()
    logger.info("AEGIS-AI shutdown complete.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AEGIS-AI Command Center API",
    description="AI Agent Red Team vs Blue Team Payment Security Lab",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class AttackRequest(BaseModel):
    target: str = Field(default="support_chatbot")
    objective: str = Field(default="impersonation")
    strategy: str = Field(default="single_turn")
    converter: str = Field(default="none")
    max_turns: int = Field(default=10, ge=1, le=50)


class BatchAttackRequest(BaseModel):
    num_attempts: int = Field(default=5, ge=1, le=50)
    targets: list[str] = Field(default=["support_chatbot"])
    objectives: list[str] = Field(default=["impersonation", "injected_instruction", "coercion"])
    strategies: list[str] = Field(default=["single_turn", "multi_turn_escalation"])
    converters: list[str] = Field(default=["none", "roleplay"])
    max_turns: int = Field(default=10, ge=1, le=50)


class SandboxRequest(BaseModel):
    target: str = Field(default="support_chatbot")
    message: str = Field(default="Hello, I need help with my account.")


class HardenRequest(BaseModel):
    auto: bool = Field(default=True)


# ---------------------------------------------------------------------------
# WebSocket Manager
# ---------------------------------------------------------------------------

async def broadcast_ws(data: dict):
    """Broadcast data to all connected WebSocket clients."""
    dead = []
    for ws in app_state.ws_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        app_state.ws_clients.remove(ws)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {
        "status": "ONLINE",
        "version": "2.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "openrouter_available": app_state.openrouter_available,
        "judge_active": app_state.judge is not None,
        "guard_rules_count": len(app_state.guard_rules.rules),
    }


# ---------------------------------------------------------------------------
# Attack Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/attack/run")
async def run_attack(req: AttackRequest, session: AsyncSession = Depends(get_session)):
    """Run a single attack attempt against a defended target."""
    if not app_state.openrouter_available:
        raise HTTPException(400, "OPENROUTER_API_KEY not configured. Set it in .env.")

    config = AttackConfig(
        target=req.target,
        objective=req.objective,
        strategy=req.strategy,
        converters=[req.converter],
        max_turns=req.max_turns,
    )

    result = await app_state.orchestrator.run_single_attack(config)

    # Persist to DB
    attempt = AttackAttempt(
        id=uuid.UUID(result["id"]),
        session_id=uuid.UUID(result["session_id"]),
        target_name=result["target_name"],
        objective_category=result["objective_category"],
        strategy=result["strategy"],
        converter_used=result["converter_used"],
        full_transcript=result["full_transcript"],
        target_action_taken=result["target_action_taken"],
        blue_team_verdict=result["blue_team_verdict"],
        blue_team_reasoning=result["blue_team_reasoning"],
        rules_fired=result["rules_fired"],
        judge_analysis=result["judge_analysis"],
        scorer_confidence=result["scorer_confidence"],
        success=result["success"],
    )
    session.add(attempt)
    await session.commit()

    # Log to feedback loop
    app_state.feedback_loop.log_attempt(FeedbackEntry(
        objective_category=result["objective_category"],
        strategy=result["strategy"],
        converter_used=result["converter_used"],
        success=result["success"],
        blue_team_verdict=result["blue_team_verdict"],
    ))

    # Broadcast via WebSocket
    await broadcast_ws({"type": "attack_result", "data": result})

    return result


@app.post("/api/attack/batch")
async def run_batch_attack(req: BatchAttackRequest, session: AsyncSession = Depends(get_session)):
    """Run a batch of attack attempts."""
    if not app_state.openrouter_available:
        raise HTTPException(400, "OPENROUTER_API_KEY not configured.")

    config = BatchAttackConfig(
        num_attempts=req.num_attempts,
        targets=req.targets,
        objectives=req.objectives,
        strategies=req.strategies,
        converters=req.converters,
        max_turns=req.max_turns,
    )

    results = await app_state.orchestrator.run_batch(config)

    # Persist all results
    for result in results:
        attempt = AttackAttempt(
            id=uuid.UUID(result["id"]),
            session_id=uuid.UUID(result["session_id"]),
            target_name=result["target_name"],
            objective_category=result["objective_category"],
            strategy=result["strategy"],
            converter_used=result["converter_used"],
            full_transcript=result["full_transcript"],
            target_action_taken=result["target_action_taken"],
            blue_team_verdict=result["blue_team_verdict"],
            blue_team_reasoning=result["blue_team_reasoning"],
            rules_fired=result["rules_fired"],
            judge_analysis=result["judge_analysis"],
            scorer_confidence=result["scorer_confidence"],
            success=result["success"],
        )
        session.add(attempt)

        app_state.feedback_loop.log_attempt(FeedbackEntry(
            objective_category=result["objective_category"],
            strategy=result["strategy"],
            converter_used=result["converter_used"],
            success=result["success"],
            blue_team_verdict=result["blue_team_verdict"],
        ))

        await broadcast_ws({"type": "attack_result", "data": result})

    await session.commit()

    # Compute batch metrics
    metrics = app_state.evaluator.evaluate(results)

    return {
        "status": "COMPLETED",
        "total_attempts": len(results),
        "metrics": metrics,
        "attempts": results,
    }


@app.get("/api/attack/history")
async def get_attack_history(
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """Get recent attack attempts."""
    stmt = select(AttackAttempt).order_by(AttackAttempt.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    attempts = result.scalars().all()
    return [a.to_dict() for a in attempts]


@app.get("/api/attack/{attempt_id}")
async def get_attempt(attempt_id: str, session: AsyncSession = Depends(get_session)):
    """Get a single attack attempt by ID."""
    stmt = select(AttackAttempt).where(AttackAttempt.id == uuid.UUID(attempt_id))
    result = await session.execute(stmt)
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(404, "Attempt not found.")
    return attempt.to_dict()


# ---------------------------------------------------------------------------
# Defense Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/defense/status")
async def defense_status():
    """Current defense state."""
    return {
        "guard_rules": app_state.guard_rules.get_rules_snapshot(),
        "judge_active": app_state.judge is not None,
        "judge_prompt_length": len(app_state.judge.get_prompt_snapshot()) if app_state.judge else 0,
        "feedback_logged": len(app_state.feedback_loop.feedback_log),
        "hardening_rounds": len(app_state.feedback_loop.hardening_history),
    }


@app.post("/api/defense/harden")
async def harden_defenses(req: HardenRequest, session: AsyncSession = Depends(get_session)):
    """Trigger the feedback loop to analyze weaknesses and harden defenses."""
    analysis = app_state.feedback_loop.analyze_weaknesses()
    actions = await app_state.feedback_loop.apply_hardening()

    # Record the hardening round
    round_num = len(app_state.feedback_loop.hardening_history)
    defense_round = DefenseRound(
        round_number=round_num,
        guard_rules_snapshot=app_state.guard_rules.get_rules_snapshot(),
        judge_prompt_snapshot=(
            app_state.judge.get_prompt_snapshot() if app_state.judge else ""
        ),
        total_attempts=analysis.get("total_logged", 0),
        successful_attacks=analysis.get("total_successful", 0),
        blocked_attacks=analysis.get("total_logged", 0) - analysis.get("total_successful", 0),
        success_rate=analysis.get("success_rate", 0.0),
        block_rate=1.0 - analysis.get("success_rate", 0.0),
        category_breakdown=analysis.get("by_category", {}),
    )
    session.add(defense_round)
    await session.commit()

    await broadcast_ws({
        "type": "defense_hardened",
        "data": {
            "round": round_num,
            "actions": [a.model_dump() for a in actions],
            "analysis": analysis,
        },
    })

    return {
        "status": "HARDENED",
        "round": round_num,
        "analysis": analysis,
        "actions_applied": [a.model_dump() for a in actions],
        "red_team_recommendation": app_state.feedback_loop.get_recommendation_for_red_team(),
    }


@app.get("/api/defense/rounds")
async def get_defense_rounds(session: AsyncSession = Depends(get_session)):
    """Get history of defense hardening rounds."""
    stmt = select(DefenseRound).order_by(DefenseRound.round_number)
    result = await session.execute(stmt)
    rounds = result.scalars().all()
    return [r.to_dict() for r in rounds]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@app.get("/api/metrics/overview")
async def metrics_overview(session: AsyncSession = Depends(get_session)):
    """Overall defense metrics from all attack attempts."""
    stmt = select(AttackAttempt).order_by(AttackAttempt.created_at.desc()).limit(500)
    result = await session.execute(stmt)
    attempts = [a.to_dict() for a in result.scalars().all()]
    return app_state.evaluator.evaluate(attempts)


# ---------------------------------------------------------------------------
# Sandbox
# ---------------------------------------------------------------------------

@app.post("/api/sandbox/prompt")
async def sandbox_prompt(req: SandboxRequest):
    """Send a single prompt to a target (with defenses) and see the verdict."""
    if not app_state.openrouter_available:
        raise HTTPException(400, "OPENROUTER_API_KEY not configured.")

    from targets.support_chatbot import SupportChatbot
    from targets.invoice_agent import InvoiceAgent
    from targets.merchant_onboarding import MerchantOnboarding

    target_map = {
        "support_chatbot": SupportChatbot,
        "invoice_agent": InvoiceAgent,
        "merchant_onboarding": MerchantOnboarding,
    }

    target_cls = target_map.get(req.target)
    if not target_cls:
        raise HTTPException(400, f"Unknown target: {req.target}")

    target = target_cls()
    defended = DefenseWrapper(target, app_state.guard_rules, app_state.judge)
    response, verdict = await defended.process_message(req.message)

    return {
        "response": response,
        "transcript": target.get_transcript(),
        "verdict": verdict.model_dump() if verdict else None,
        "tool_calls": [
            {"tool": tc.tool_name, "args": tc.arguments, "result": tc.result}
            for tc in target.tool_calls_log
        ],
    }


# ---------------------------------------------------------------------------
# Config info
# ---------------------------------------------------------------------------

@app.get("/api/config")
async def get_config():
    """Return available targets, objectives, strategies, and converters."""
    return {
        "targets": ALL_TARGETS,
        "objectives": ALL_OBJECTIVES,
        "strategies": ALL_STRATEGIES,
        "converters": ALL_CONVERTERS,
    }


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/stream")
async def websocket_stream(ws: WebSocket):
    """Real-time attack result streaming."""
    await ws.accept()
    app_state.ws_clients.append(ws)
    logger.info(f"WebSocket client connected. Total: {len(app_state.ws_clients)}")
    try:
        while True:
            # Keep connection alive; clients send pings
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        app_state.ws_clients.remove(ws)
        logger.info(f"WebSocket client disconnected. Total: {len(app_state.ws_clients)}")


# ---------------------------------------------------------------------------
# Static Files & SPA
# ---------------------------------------------------------------------------

FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
FRONTEND_OUT = os.path.join(FRONTEND_DIR, "out")  # Next.js static export

# Serve Next.js static export if it exists
if os.path.exists(FRONTEND_OUT):
    # Mount everything in out/ to the root, with html=True to support /attack -> attack.html
    app.mount("/", StaticFiles(directory=FRONTEND_OUT, html=True), name="frontend")
else:
    @app.get("/")
    async def serve_fallback():
        return JSONResponse({
            "message": "AEGIS-AI API is running. Frontend not built yet.",
            "docs": "/docs",
            "health": "/api/health",
        })
