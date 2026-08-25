"""
Configuration for the Red Team attack engine.
Replaces the old tabular RedTeamConfig with agentic attack configuration.
"""

from typing import Literal, Optional
from dataclasses import dataclass, field

# Target service identifiers
TARGET_SUPPORT_CHATBOT = "support_chatbot"
TARGET_INVOICE_AGENT = "invoice_agent"
TARGET_MERCHANT_ONBOARDING = "merchant_onboarding"

ALL_TARGETS = [TARGET_SUPPORT_CHATBOT, TARGET_INVOICE_AGENT, TARGET_MERCHANT_ONBOARDING]

# Objective categories (map to old fraud themes)
OBJECTIVE_IMPERSONATION = "impersonation"           # successor to voice_clone_app
OBJECTIVE_INJECTED_INSTRUCTION = "injected_instruction"  # successor to ephemeral_merchant
OBJECTIVE_COERCION = "coercion"                     # successor to digital_arrest

ALL_OBJECTIVES = [OBJECTIVE_IMPERSONATION, OBJECTIVE_INJECTED_INSTRUCTION, OBJECTIVE_COERCION]

# Attack strategies
STRATEGY_SINGLE_TURN = "single_turn"
STRATEGY_MULTI_TURN = "multi_turn_escalation"
STRATEGY_CRESCENDO = "crescendo"

ALL_STRATEGIES = [STRATEGY_SINGLE_TURN, STRATEGY_MULTI_TURN, STRATEGY_CRESCENDO]

# Converter names
CONVERTER_NONE = "none"
CONVERTER_BASE64 = "base64"
CONVERTER_ROLEPLAY = "roleplay"
CONVERTER_PARAPHRASE = "paraphrase"
CONVERTER_UNICODE = "unicode_substitution"
CONVERTER_TRANSLATION = "translation"

ALL_CONVERTERS = [
    CONVERTER_NONE,
    CONVERTER_BASE64,
    CONVERTER_ROLEPLAY,
    CONVERTER_PARAPHRASE,
    CONVERTER_UNICODE,
    CONVERTER_TRANSLATION,
]


@dataclass
class AttackConfig:
    """Configuration for a single attack run."""
    target: str = TARGET_SUPPORT_CHATBOT
    objective: str = OBJECTIVE_IMPERSONATION
    strategy: str = STRATEGY_SINGLE_TURN
    max_turns: int = 10
    converters: list[str] = field(default_factory=lambda: [CONVERTER_NONE])
    seed: int = 42


@dataclass
class BatchAttackConfig:
    """Configuration for a batch of attack runs."""
    num_attempts: int = 10
    targets: list[str] = field(default_factory=lambda: [TARGET_SUPPORT_CHATBOT])
    objectives: list[str] = field(default_factory=lambda: ALL_OBJECTIVES)
    strategies: list[str] = field(default_factory=lambda: [STRATEGY_SINGLE_TURN, STRATEGY_MULTI_TURN])
    converters: list[str] = field(default_factory=lambda: [CONVERTER_NONE, CONVERTER_ROLEPLAY])
    max_turns: int = 10
    seed: int = 42
