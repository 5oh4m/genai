"""
Abstract Base Classifier for Blue Team Fraud Detectors.
"""

from abc import ABC, abstractmethod
import numpy as np


class BaseFraudDetector(ABC):
    """Abstract interface for all fraud classification models."""

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaseFraudDetector":
        """Fit the model on feature matrix X and binary labels y."""
        pass

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Return predicted probability of fraud for each row.
        Returns: 1D array of shape (N,) with values in [0.0, 1.0]
        """
        pass

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Return binary predicted class labels given a threshold."""
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(int)
