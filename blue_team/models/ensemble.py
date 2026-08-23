"""
Hybrid Ensemble Classifier: Blends Machine Learning with Deterministic Rule Heuristics.
"""

from typing import Optional, List, Dict, Any, Tuple
import numpy as np

from blue_team.config import BlueTeamConfig
from blue_team.models.base import BaseFraudDetector
from blue_team.models.ml_detector import MLFraudDetector
from blue_team.rule_engine import RuleEngine


class EnsembleFraudDetector(BaseFraudDetector):
    """
    Combines ML tabular probability estimates with RuleEngine heuristics,
    supporting soft weighted blending and hard safety tripwire overrides.
    """

    def __init__(self, config: Optional[BlueTeamConfig] = None):
        self.config = config or BlueTeamConfig()
        self.ml_model = MLFraudDetector(self.config)
        self.rule_engine = RuleEngine()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "EnsembleFraudDetector":
        self.ml_model.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Standard ML predict_proba (without rule contextual features)."""
        return self.ml_model.predict_proba(X)

    def predict_ensemble(
        self,
        X: np.ndarray,
        rule_scores: np.ndarray,
        critical_overrides: np.ndarray,
    ) -> np.ndarray:
        """
        Calculates hybrid ensemble probabilities.
        
        Args:
            X: Scaled feature tensor.
            rule_scores: Array of rule heuristic scores (N,).
            critical_overrides: Boolean array indicating critical rule triggers (N,).
            
        Returns:
            Blended probability array of shape (N,).
        """
        ml_probs = self.ml_model.predict_proba(X)
        w_ml = self.config.ml_weight
        w_rule = self.config.rule_weight

        # Weighted soft blend
        blended = (w_ml * ml_probs) + (w_rule * rule_scores)
        blended = np.clip(blended, 0.0, 1.0)

        # Apply hard overrides if enabled
        if self.config.enable_hard_rule_override:
            blended[critical_overrides] = np.maximum(blended[critical_overrides], 0.96)

        return blended
