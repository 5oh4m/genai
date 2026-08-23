"""
Machine Learning Fraud Detector.
Supports Random Forest, Gradient Boosting, and Logistic Regression with class-balance weighting.
"""

from typing import Optional, Dict, Any, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from blue_team.config import BlueTeamConfig
from blue_team.models.base import BaseFraudDetector


class MLFraudDetector(BaseFraudDetector):
    """Supervised tabular ML fraud detection model."""

    def __init__(self, config: Optional[BlueTeamConfig] = None):
        self.config = config or BlueTeamConfig()
        self.model = self._create_estimator()
        self.feature_importances_: Optional[np.ndarray] = None
        self.is_fitted: bool = False

    def _create_estimator(self):
        m_type = self.config.model_type.lower()
        if m_type == "random_forest":
            return RandomForestClassifier(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                class_weight="balanced",
                random_state=self.config.random_state,
                n_jobs=-1,
            )
        elif m_type == "gradient_boosting":
            return GradientBoostingClassifier(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                random_state=self.config.random_state,
            )
        elif m_type == "logistic_regression":
            return LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=self.config.random_state,
            )
        else:
            raise ValueError(f"Unknown model_type: {self.config.model_type}")

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MLFraudDetector":
        self.model.fit(X, y)
        if hasattr(self.model, "feature_importances_"):
            self.feature_importances_ = self.model.feature_importances_
        elif hasattr(self.model, "coef_"):
            self.feature_importances_ = np.abs(self.model.coef_[0])
        self.is_fitted = True
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predicting!")
        probs = self.model.predict_proba(X)
        # Class 1 is fraud
        if probs.shape[1] == 2:
            return probs[:, 1]
        elif probs.shape[1] == 1:
            # Single class edge case
            return np.zeros(X.shape[0])
        return probs[:, 1]

    def get_top_features(self, feature_names: List[str], top_k: int = 10) -> List[Dict[str, Any]]:
        """Return the top-K most influential features according to model weights."""
        if self.feature_importances_ is None or len(feature_names) != len(self.feature_importances_):
            return []
        
        indices = np.argsort(self.feature_importances_)[::-1][:top_k]
        top_features = [
            {"feature": feature_names[i], "importance": round(float(self.feature_importances_[i]), 4)}
            for i in indices
        ]
        return top_features
