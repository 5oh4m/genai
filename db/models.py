"""
SQLAlchemy ORM models for the AEGIS-AI attempt log and defense round tracking.
Replaces the old in-memory DataFrames (df_public / df_answer / df_predictions).
"""

import uuid
import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Boolean,
    Integer,
    DateTime,
    JSON,
    Uuid,
)

from db import Base


class AttackAttempt(Base):
    """
    A single red-team attack attempt against a defended target.
    This is the primary data record — replaces the old oracle + prediction tables.
    """
    __tablename__ = "attack_attempts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid(as_uuid=True), nullable=False, index=True)

    # Attack metadata
    target_name = Column(String(64), nullable=False, index=True)
    objective_category = Column(String(64), nullable=False, index=True)
    strategy = Column(String(64), nullable=False)
    converter_used = Column(String(128), default="none")

    # Transcript & outcome
    full_transcript = Column(JSON, nullable=False, default=list)
    target_action_taken = Column(String(256), default="none")

    # Blue team defense results
    blue_team_verdict = Column(String(32), default="allowed")  # blocked | allowed | escalated
    blue_team_reasoning = Column(Text, default="")
    rules_fired = Column(JSON, default=list)
    judge_analysis = Column(Text, default="")

    # Scorer results
    scorer_confidence = Column(Float, default=0.0)
    success = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "target_name": self.target_name,
            "objective_category": self.objective_category,
            "strategy": self.strategy,
            "converter_used": self.converter_used,
            "full_transcript": self.full_transcript,
            "target_action_taken": self.target_action_taken,
            "blue_team_verdict": self.blue_team_verdict,
            "blue_team_reasoning": self.blue_team_reasoning,
            "rules_fired": self.rules_fired,
            "judge_analysis": self.judge_analysis,
            "scorer_confidence": self.scorer_confidence,
            "success": self.success,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DefenseRound(Base):
    """
    Snapshot of the Blue Team defense state at a given hardening round.
    Tracks how guard rules and judge prompts evolve over time.
    """
    __tablename__ = "defense_rounds"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    round_number = Column(Integer, nullable=False, unique=True)

    # Defense state snapshots
    guard_rules_snapshot = Column(JSON, default=dict)
    judge_prompt_snapshot = Column(Text, default="")

    # Round-level metrics
    total_attempts = Column(Integer, default=0)
    successful_attacks = Column(Integer, default=0)
    blocked_attacks = Column(Integer, default=0)
    escalated_attacks = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    block_rate = Column(Float, default=0.0)

    # Per-category breakdown
    category_breakdown = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "round_number": self.round_number,
            "guard_rules_snapshot": self.guard_rules_snapshot,
            "judge_prompt_snapshot": self.judge_prompt_snapshot,
            "total_attempts": self.total_attempts,
            "successful_attacks": self.successful_attacks,
            "blocked_attacks": self.blocked_attacks,
            "escalated_attacks": self.escalated_attacks,
            "success_rate": self.success_rate,
            "block_rate": self.block_rate,
            "category_breakdown": self.category_breakdown,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
