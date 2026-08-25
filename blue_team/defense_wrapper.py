"""
Defense Wrapper — wraps a target agent with the two-layer Blue Team defense.
1. Guard rules (fast, deterministic) — short-circuits if blocked.
2. LLM Judge agent — reviews conversation + proposed action.
"""

import logging
from typing import Optional

from targets.base import BaseTarget, ToolCall
from blue_team.guard_rules import GuardRules
from blue_team.judge_agent import JudgeAgent
from blue_team.verdict import DefenseVerdict, GuardRulesVerdict, JudgeVerdict

logger = logging.getLogger(__name__)


class DefenseWrapper:
    """
    Wraps a BaseTarget with Blue Team defenses.
    Intercepts tool calls and evaluates them through guard rules + judge agent.
    """

    def __init__(
        self,
        target: BaseTarget,
        guard_rules: Optional[GuardRules] = None,
        judge: Optional[JudgeAgent] = None,
    ):
        self.target = target
        self.guard_rules = guard_rules or GuardRules()
        self.judge = judge  # Can be None for rules-only mode
        self.last_verdict: Optional[DefenseVerdict] = None
        self.verdicts_log: list[DefenseVerdict] = []

    def reset(self) -> None:
        """Reset the target conversation and verdict log."""
        self.target.reset_conversation()
        self.last_verdict = None
        self.verdicts_log = []

    async def process_message(self, user_message: str) -> tuple[str, Optional[DefenseVerdict]]:
        """
        Process a user message through the defended target.

        Returns:
            Tuple of (assistant_response, defense_verdict_or_None).
            The verdict is only generated if the target attempted a tool call.
        """
        # Let the target process the message
        response = await self.target.process_message(user_message)

        # Check if any tool calls were made in this turn
        latest_turn = self.target.conversation_history[-1] if self.target.conversation_history else None
        if not latest_turn or not latest_turn.tool_calls:
            # No tool calls — no defense verdict needed
            return response, None

        # Evaluate each tool call through defenses
        for tool_call in latest_turn.tool_calls:
            verdict = await self._evaluate_tool_call(tool_call)
            self.verdicts_log.append(verdict)
            self.last_verdict = verdict

        return response, self.last_verdict

    async def _evaluate_tool_call(self, tool_call: ToolCall) -> DefenseVerdict:
        """Run a tool call through both defense layers."""

        # Layer 1: Guard Rules (fast, deterministic)
        guard_result = self.guard_rules.evaluate_tool_call(
            target_name=self.target.name,
            tool_name=tool_call.tool_name,
            tool_args=tool_call.arguments,
            conversation_context=self.target.get_transcript(),
        )

        # Short-circuit if guard rules block
        if guard_result.overall_verdict == "block":
            logger.warning(
                f"[BLOCKED by guard rules] {self.target.name}.{tool_call.tool_name} — "
                f"Rules: {guard_result.rules_fired}"
            )
            return DefenseVerdict(
                final_verdict="block",
                guard_rules_result=guard_result,
                judge_result=None,
                was_short_circuited=True,
            )

        # Layer 2: LLM Judge (adaptive, slower)
        judge_result = None
        if self.judge is not None:
            transcript = self.target.get_transcript()
            proposed_action = {
                "tool_name": tool_call.tool_name,
                "arguments": tool_call.arguments,
            }
            judge_result = await self.judge.evaluate(
                target_name=self.target.name,
                conversation_transcript=transcript,
                proposed_tool_call=proposed_action,
            )

        # Combine verdicts: guard rules escalate + judge allow → escalate
        # guard rules allow + judge block → block
        # etc.
        final_verdict = self._combine_verdicts(guard_result, judge_result)

        return DefenseVerdict(
            final_verdict=final_verdict,
            guard_rules_result=guard_result,
            judge_result=judge_result,
            was_short_circuited=False,
        )

    def _combine_verdicts(
        self,
        guard: GuardRulesVerdict,
        judge: Optional[JudgeVerdict],
    ) -> str:
        """Combine guard rules and judge verdicts. Most restrictive wins."""
        if judge is None:
            return guard.overall_verdict

        verdicts = [guard.overall_verdict, judge.verdict]

        if "block" in verdicts:
            return "block"
        if "escalate" in verdicts:
            return "escalate"
        return "allow"
