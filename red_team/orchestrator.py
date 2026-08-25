"""
Red Team orchestrator — wraps attack execution, transcript collection, and scoring.
Coordinates between objectives, converters, target agents, and the defense layer.
"""

import uuid
import random
import logging
import datetime
from typing import Optional

from red_team.config import (
    AttackConfig,
    BatchAttackConfig,
    ALL_OBJECTIVES,
    ALL_TARGETS,
    STRATEGY_SINGLE_TURN,
    STRATEGY_MULTI_TURN,
)
from red_team.objectives import impersonation, injected_instruction, coercion
from red_team.converters import apply_converter
from targets.support_chatbot import SupportChatbot
from targets.invoice_agent import InvoiceAgent
from targets.merchant_onboarding import MerchantOnboarding
from blue_team.defense_wrapper import DefenseWrapper
from blue_team.guard_rules import GuardRules
from blue_team.judge_agent import JudgeAgent
from red_team.agent import RedTeamAgent

logger = logging.getLogger(__name__)

# Objective data lookup (we only need success_indicators and descriptions now)
OBJECTIVE_DATA = {
    "impersonation": {
        "description": impersonation.OBJECTIVE_DESCRIPTION,
        "success_indicators": impersonation.SUCCESS_INDICATORS,
    },
    "injected_instruction": {
        "description": injected_instruction.OBJECTIVE_DESCRIPTION,
        "success_indicators": injected_instruction.SUCCESS_INDICATORS,
    },
    "coercion": {
        "description": coercion.OBJECTIVE_DESCRIPTION,
        "success_indicators": coercion.SUCCESS_INDICATORS,
    },
}

# Target factory
TARGET_FACTORY = {
    "support_chatbot": SupportChatbot,
    "invoice_agent": InvoiceAgent,
    "merchant_onboarding": MerchantOnboarding,
}


class RedTeamOrchestrator:
    """
    Orchestrates red-team attack attempts against defended targets.
    Handles prompt selection, converter application, multi-turn execution,
    and success scoring.
    """

    def __init__(
        self,
        guard_rules: Optional[GuardRules] = None,
        judge: Optional[JudgeAgent] = None,
    ):
        self.guard_rules = guard_rules or GuardRules()
        self.judge = judge

    async def run_single_attack(self, config: AttackConfig) -> dict:
        """
        Execute a single attack attempt.

        Returns:
            Dict matching the AttackAttempt schema.
        """
        session_id = uuid.uuid4()

        # Create target + defense wrapper
        target_cls = TARGET_FACTORY.get(config.target)
        if target_cls is None:
            raise ValueError(f"Unknown target: {config.target}")

        target = target_cls()
        defended = DefenseWrapper(target, self.guard_rules, self.judge)

        # Initialize Red Team Agent
        obj_data = OBJECTIVE_DATA.get(config.objective)
        if not obj_data:
            raise ValueError(f"Unknown objective: {config.objective}")

        converter_name = config.converters[0] if config.converters else "none"

        red_team_agent = RedTeamAgent()
        red_team_agent.set_context(
            objective=obj_data["description"],
            strategy=config.strategy,
            converter=converter_name,
            target=config.target,
        )

        all_verdicts = []
        target_reply = None
        attack_success = False
        action_taken = None

        max_turns = config.max_turns if config.strategy in (STRATEGY_MULTI_TURN, "crescendo") else 1

        for turn in range(max_turns):
            # 1. Attacker generates next message based on target's last reply (or None for start)
            attack_msg = await red_team_agent.generate_next_message(target_reply)

            # 2. Defense Wrapper processes the attack message
            response, verdict = await defended.process_message(attack_msg)
            if verdict:
                all_verdicts.append(verdict)

            # 3. Check if target performed the sensitive action
            action_taken = target.get_last_action()
            if action_taken in obj_data["success_indicators"]:
                attack_success = True
                break  # Win condition met

            # 4. If defense blocked it, the attack stops
            if verdict and verdict.final_verdict in ("block", "blocked"):
                break

            # 5. Otherwise, pass the target's response back to the attacker for the next turn
            target_reply = response

        # Determine blue team verdict
        if all_verdicts:
            last_verdict = all_verdicts[-1]
            bt_verdict = last_verdict.final_verdict
            bt_reasoning = (
                last_verdict.judge_result.reasoning
                if last_verdict.judge_result
                else "; ".join(last_verdict.guard_rules_result.reasons)
            )
            rules_fired = last_verdict.guard_rules_result.rules_fired
            judge_analysis = (
                last_verdict.judge_result.reasoning
                if last_verdict.judge_result
                else ""
            )
            scorer_confidence = (
                last_verdict.judge_result.confidence
                if last_verdict.judge_result
                else (1.0 if last_verdict.was_short_circuited else 0.5)
            )
        else:
            bt_verdict = "allowed"
            bt_reasoning = "No tool calls detected — no defense evaluation triggered."
            rules_fired = []
            judge_analysis = ""
            scorer_confidence = 0.5

        # If defense blocked the action, the attack didn't truly succeed
        if bt_verdict == "block" or bt_verdict == "blocked":
            attack_success = False
            bt_verdict = "blocked"

        return {
            "id": str(uuid.uuid4()),
            "session_id": str(session_id),
            "target_name": config.target,
            "objective_category": config.objective,
            "strategy": config.strategy,
            "converter_used": converter_name,
            "full_transcript": target.get_transcript(),
            "target_action_taken": action_taken,
            "blue_team_verdict": bt_verdict,
            "blue_team_reasoning": bt_reasoning,
            "rules_fired": rules_fired,
            "judge_analysis": judge_analysis,
            "scorer_confidence": scorer_confidence,
            "success": attack_success,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

    async def run_batch(self, config: BatchAttackConfig) -> list[dict]:
        """Run a batch of attack attempts with varied configurations."""
        rng = random.Random(config.seed)
        results = []

        for i in range(config.num_attempts):
            attack_cfg = AttackConfig(
                target=rng.choice(config.targets),
                objective=rng.choice(config.objectives),
                strategy=rng.choice(config.strategies),
                max_turns=config.max_turns,
                converters=[rng.choice(config.converters)],
                seed=config.seed + i,
            )

            try:
                result = await self.run_single_attack(attack_cfg)
                results.append(result)
                logger.info(
                    f"Attack {i+1}/{config.num_attempts}: "
                    f"{attack_cfg.objective} vs {attack_cfg.target} "
                    f"[{attack_cfg.strategy}] → "
                    f"{'SUCCESS' if result['success'] else 'BLOCKED'}"
                )
            except Exception as e:
                logger.error(f"Attack {i+1} failed: {e}")
                results.append({
                    "id": str(uuid.uuid4()),
                    "session_id": str(uuid.uuid4()),
                    "target_name": attack_cfg.target,
                    "objective_category": attack_cfg.objective,
                    "strategy": attack_cfg.strategy,
                    "converter_used": attack_cfg.converters[0] if attack_cfg.converters else "none",
                    "full_transcript": [],
                    "target_action_taken": "error",
                    "blue_team_verdict": "error",
                    "blue_team_reasoning": str(e),
                    "rules_fired": [],
                    "judge_analysis": "",
                    "scorer_confidence": 0.0,
                    "success": False,
                    "created_at": datetime.datetime.utcnow().isoformat(),
                })

        return results
