"""
Configuration and Hyperparameters for Blue Team Defense Pipeline.
"""

from typing import List
from dataclasses import dataclass, field

NUMERICAL_FEATURES: List[str] = [
    "amount",
    "sender_account_age_days",
    "receiver_account_age_days",
    "session_duration_sec",
    "time_since_payee_added_sec",
    "login_to_transaction_gap_sec",
    "velocity_1h",
    "velocity_24h",
    "amount_deviation_score",
    "hour_of_day",
    "day_of_week",
]

CATEGORICAL_FEATURES: List[str] = [
    "channel",
    "device_type",
    "ip_country",
]

BOOLEAN_FEATURES: List[str] = [
    "concurrent_call_active",
    "ip_change_flag",
    "new_payee_flag",
    "is_night_hour",
    "is_weekend",
]

# Risk tier thresholds for triage dashboard
TIER_LOW = "LOW"         # prob < 0.30 (auto-approve)
TIER_MEDIUM = "MEDIUM"   # 0.30 <= prob < 0.70 (step-up authentication / OTP / delay)
TIER_HIGH = "HIGH"       # prob >= 0.70 (freeze / manual fraud review)

@dataclass
class BlueTeamConfig:
    """Master configuration for Blue Team preprocessor, models, and thresholds."""
    model_type: str = "random_forest"  # "random_forest", "gradient_boosting", "logistic_regression"
    n_estimators: int = 150
    max_depth: int = 8
    random_state: int = 42
    
    # Classification threshold for binary fraud decision
    decision_threshold: float = 0.50
    
    # Risk Tier thresholds
    medium_risk_threshold: float = 0.30
    high_risk_threshold: float = 0.70
    
    # Hybrid Ensemble weights (Rule Engine vs Machine Learning)
    rule_weight: float = 0.30
    ml_weight: float = 0.70
    
    # Hard rule override: if a high-critical rule fires, force high probability
    enable_hard_rule_override: bool = True
