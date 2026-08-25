"""
Feedback Loop — aggregates successful attacks and auto-hardens defenses.
Replaces the old evasion_tuner.py + retrainer.py with prompt/policy hardening
instead of ML model retraining.
"""

import logging
from typing import Optional
from collections import Counter

from blue_team.guard_rules import GuardRules
from blue_team.judge_agent import JudgeAgent
from blue_team.architect_agent import DefenseArchitectAgent
from blue_team.verdict import FeedbackEntry, HardeningAction

logger = logging.getLogger(__name__)


class FeedbackLoop:
    """
    Closed-loop defense hardening engine.
    Aggregates evasion patterns from successful attacks and:
    1. Adds/strengthens guard rules.
    2. Amends the LLM judge system prompt.
    """

    def __init__(self, guard_rules: GuardRules, judge: Optional[JudgeAgent] = None):
        self.guard_rules = guard_rules
        self.judge = judge
        self.architect = DefenseArchitectAgent()
        self.feedback_log: list[FeedbackEntry] = []
        self.hardening_history: list[list[HardeningAction]] = []

    def log_attempt(self, entry: FeedbackEntry) -> None:
        """Record an attack attempt outcome."""
        self.feedback_log.append(entry)

    def analyze_weaknesses(self) -> dict:
        """
        Analyze accumulated feedback to identify defense weaknesses.
        Returns breakdown of successful attack patterns.
        """
        successful = [e for e in self.feedback_log if e.success]

        if not successful:
            return {
                "total_logged": len(self.feedback_log),
                "total_successful": 0,
                "weakest_category": None,
                "weakest_strategy": None,
                "most_effective_converter": None,
            }

        category_counts = Counter(e.objective_category for e in successful)
        strategy_counts = Counter(e.strategy for e in successful)
        converter_counts = Counter(e.converter_used for e in successful)

        return {
            "total_logged": len(self.feedback_log),
            "total_successful": len(successful),
            "success_rate": round(len(successful) / max(1, len(self.feedback_log)), 4),
            "by_category": dict(category_counts),
            "by_strategy": dict(strategy_counts),
            "by_converter": dict(converter_counts),
            "weakest_category": category_counts.most_common(1)[0][0] if category_counts else None,
            "weakest_strategy": strategy_counts.most_common(1)[0][0] if strategy_counts else None,
            "most_effective_converter": converter_counts.most_common(1)[0][0] if converter_counts else None,
        }

    async def generate_hardening_actions(self) -> list[HardeningAction]:
        """
        Generate defense hardening actions dynamically using the LLM Architect.
        """
        analysis = self.analyze_weaknesses()
        actions: list[HardeningAction] = []

        if analysis["total_successful"] == 0:
            return actions

        successful = [e for e in self.feedback_log if e.success]
        
        # Compile a digest of successful attacks
        transcripts_digest = ""
        for i, entry in enumerate(successful):
            transcripts_digest += f"--- ATTACK {i+1} ---\n"
            transcripts_digest += f"Objective: {entry.objective_category}\n"
            transcripts_digest += f"Strategy: {entry.strategy}\n"
            # Format the transcript properly if it's a list of ConversationTurn dicts
            for t in getattr(entry, "full_transcript", []):
                # Ensure we handle object attributes safely if it's an object instead of dict
                role = getattr(t, "role", t.get("role") if isinstance(t, dict) else "unknown")
                content = getattr(t, "content", t.get("content") if isinstance(t, dict) else "")
                transcripts_digest += f"{role.upper()}: {content}\n"
            transcripts_digest += "\n"

        # Ask the architect to patch the vulnerabilities
        patch = await self.architect.generate_defense_patch(transcripts_digest)

        # 1. Action to add the new Guard Rule
        if patch.get("description"):
            actions.append(HardeningAction(
                action_type="add_rule",
                description="Dynamically generated Guard Rule.",
                target_weakness=analysis.get("weakest_category", "unknown"),
                new_content=patch["description"],
            ))

        # 2. Action to update the Judge Prompt
        if patch.get("judge_prompt"):
            actions.append(HardeningAction(
                action_type="update_judge_prompt",
                description="Dynamically generated Judge Prompt amendment.",
                target_weakness=analysis.get("weakest_strategy", "unknown"),
                new_content=f"\n\n## DYNAMIC ALERT (Harden Round {len(self.hardening_history) + 1})\n{patch['judge_prompt']}\n",
            ))

        return actions

    async def apply_hardening(self, actions: Optional[list[HardeningAction]] = None) -> list[HardeningAction]:
        """
        Apply hardening actions to guard rules and judge prompt.
        If no actions provided, generates them asynchronously from current feedback.
        Clears the feedback log after successfully generating rules.
        """
        if actions is None:
            actions = await self.generate_hardening_actions()

        for action in actions:
            if action.action_type in ("add_rule", "strengthen_rule"):
                rule_name = f"RULE_DYNAMIC_{len(self.guard_rules.rules) + 1}"
                self.guard_rules.add_rule(rule_name, {
                    "description": action.new_content,
                    "target": "all",  # dynamically generated rules apply broadly by default
                    "check": "dynamic", # in a real impl, we'd use LLM to generate the python `check` logic too
                    "severity": "high",
                    "content": action.new_content,
                })
                logger.info(f"Applied dynamic hardening rule: {action.new_content}")

            elif action.action_type == "update_judge_prompt":
                if self.judge is not None:
                    current = self.judge.get_prompt_snapshot()
                    updated = current + action.new_content
                    self.judge.update_prompt(updated)
                    logger.info("Applied dynamic judge prompt amendment.")

        self.hardening_history.append(actions)
        
        # CLEAR THE LOG to prevent endless re-processing of stale attacks (Bug fix)
        self.feedback_log.clear()
        
        return actions

    def get_recommendation_for_red_team(self) -> dict:
        """
        Suggest Red Team strategy adjustments based on defense state.
        Mirrors the old evasion_tuner's suggest_next_iteration.
        """
        analysis = self.analyze_weaknesses()

        if analysis["total_successful"] == 0:
            return {
                "suggestion": "Escalate attack sophistication",
                "recommended_strategy": "multi_turn_escalation",
                "recommended_converters": ["roleplay", "paraphrase"],
                "focus_category": "impersonation",
                "reasoning": "All attacks blocked. Try multi-turn escalation with obfuscation.",
            }

        weakest = analysis.get("weakest_category", "impersonation")
        return {
            "suggestion": "Focus on weakest defense area",
            "recommended_strategy": analysis.get("weakest_strategy", "multi_turn_escalation"),
            "recommended_converters": [analysis.get("most_effective_converter", "none")],
            "focus_category": weakest,
            "reasoning": (
                f"Category '{weakest}' has the highest evasion success rate. "
                f"Focus attacks there to maximize impact."
            ),
        }
