"""
Pydantic schemas for the Blue Team defense verdict pipeline.
Used by guard rules, the LLM judge, and the defense wrapper.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class GuardRuleResult(BaseModel):
    """Result from a single deterministic guard rule check."""
    rule_name: str
    fired: bool
    verdict: Literal["allow", "block", "escalate"]
    reason: str


class GuardRulesVerdict(BaseModel):
    """Aggregate result from all guard rules."""
    overall_verdict: Literal["allow", "block", "escalate"]
    rules_checked: int
    rules_fired: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    is_critical_override: bool = False


class JudgeVerdict(BaseModel):
    """Result from the LLM judge/guardrail agent."""
    verdict: Literal["allow", "block", "escalate"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    risk_factors: list[str] = Field(default_factory=list)


class DefenseVerdict(BaseModel):
    """
    Combined Blue Team defense verdict from both layers.
    This is the final output attached to each attack attempt.
    """
    final_verdict: Literal["allow", "block", "escalate"]
    guard_rules_result: GuardRulesVerdict
    judge_result: Optional[JudgeVerdict] = None
    was_short_circuited: bool = False  # True if guard rules blocked before judge ran


class FeedbackEntry(BaseModel):
    """A single entry in the feedback loop log."""
    objective_category: str
    strategy: str
    converter_used: str
    success: bool
    blue_team_verdict: str
    weakness_identified: str = ""


class HardeningAction(BaseModel):
    """An auto-generated defense hardening action."""
    action_type: Literal["add_rule", "strengthen_rule", "update_judge_prompt"]
    description: str
    target_weakness: str
    new_content: str  # The new rule text or prompt amendment
