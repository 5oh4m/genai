"""
Configuration, Data Contracts, and Constants for Red Team Generator.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field

# ---------------------------------------------------------
# Data Contract Definitions
# ---------------------------------------------------------

PUBLIC_COLUMNS: List[str] = [
    "transaction_id",
    "timestamp",
    "sender_id",
    "receiver_id",
    "amount",
    "channel",
    "sender_account_age_days",
    "receiver_account_age_days",
    "device_type",
    "session_duration_sec",
    "time_since_payee_added_sec",
    "concurrent_call_active",
    "ip_country",
    "ip_change_flag",
    "login_to_transaction_gap_sec",
    "velocity_1h",
    "velocity_24h",
    "amount_deviation_score",
    "new_payee_flag",
]

ANSWER_KEY_COLUMNS: List[str] = [
    "transaction_id",
    "ground_truth_label",
    "attack_subtype",
    "stealth_level",
    "evasion_technique",
    "evasion_parameters",
]

# ---------------------------------------------------------
# Attack Constants
# ---------------------------------------------------------

LABEL_NORMAL: int = 0
LABEL_VOICE_CLONE: int = 1
LABEL_EPHEMERAL_MERCHANT: int = 2
LABEL_DIGITAL_ARREST: int = 3

ATTACK_NAMES: Dict[int, str] = {
    LABEL_NORMAL: "normal",
    LABEL_VOICE_CLONE: "voice_clone_app",
    LABEL_EPHEMERAL_MERCHANT: "ephemeral_merchant",
    LABEL_DIGITAL_ARREST: "digital_arrest",
}

# ---------------------------------------------------------
# Categorical Distributions & Weights
# ---------------------------------------------------------

CHANNELS = ["UPI", "Card", "Wire", "P2P"]
CHANNEL_WEIGHTS_BASELINE = [0.50, 0.30, 0.05, 0.15]

DEVICE_TYPES = ["iOS", "Android", "Web", "Unknown"]
DEVICE_WEIGHTS_BASELINE = [0.45, 0.45, 0.08, 0.02]

COUNTRIES = ["US", "GB", "IN", "CA", "DE", "SG", "AU"]
DEFAULT_HOME_COUNTRY = "US"

# ---------------------------------------------------------
# Generator Default Configurations
# ---------------------------------------------------------

@dataclass
class RedTeamConfig:
    """Master configuration for the Red Team synthetic generator."""
    seed: int = 42
    start_date: str = "2026-08-01 00:00:00"
    simulation_days: int = 14
    num_users: int = 500
    num_merchants: int = 100
    total_transactions: int = 10000
    fraud_ratio: float = 0.05
    
    # Threat distribution among fraud cases (proportions sum to 1.0)
    threat_weights: Dict[str, float] = field(default_factory=lambda: {
        "voice_clone_app": 0.40,
        "ephemeral_merchant": 0.35,
        "digital_arrest": 0.25,
    })
    
    # Global stealth level (0.0 = naive/noisy, 1.0 = highly evasive)
    stealth_level: float = 0.0
