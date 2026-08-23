"""
Blue Team Performance & Defense Evaluation Metrics.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)

from red_team.config import (
    LABEL_NORMAL,
    LABEL_VOICE_CLONE,
    LABEL_EPHEMERAL_MERCHANT,
    LABEL_DIGITAL_ARREST,
    ATTACK_NAMES,
)


class BlueTeamEvaluator:
    """Evaluates Blue Team model predictions against oracle ground truth."""

    def __init__(self, threshold: float = 0.50):
        self.threshold = threshold

    def evaluate(
        self,
        df_predictions: pd.DataFrame,
        df_answer_key: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Calculates defense performance metrics and threat-level breakdowns.
        """
        merged = pd.merge(df_predictions, df_answer_key, on="transaction_id", how="inner")
        if merged.empty:
            raise ValueError("No matching transaction IDs between predictions and answer key!")

        y_true = (merged["ground_truth_label"] != LABEL_NORMAL).astype(int).values
        y_prob = merged["fraud_probability"].values
        y_pred = (y_prob >= self.threshold).astype(int)

        # Standard binary metrics
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        try:
            roc_auc = roc_auc_score(y_true, y_prob)
            pr_auc = average_precision_score(y_true, y_prob)
        except Exception:
            roc_auc = 0.5
            pr_auc = float(np.mean(y_true))

        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)

        # Per-threat breakdown
        threat_breakdown = {}
        for label, name in ATTACK_NAMES.items():
            if label == LABEL_NORMAL:
                continue
            subset = merged[merged["ground_truth_label"] == label]
            if not subset.empty:
                n_total = len(subset)
                n_caught = int((subset["fraud_probability"] >= self.threshold).sum())
                threat_rec = n_caught / n_total
                threat_breakdown[name] = {
                    "total_attacks": n_total,
                    "caught": n_caught,
                    "bypassed": n_total - n_caught,
                    "detection_rate": round(threat_rec, 4),
                    "evasion_rate": round(1.0 - threat_rec, 4),
                    "mean_fraud_score": round(float(subset["fraud_probability"].mean()), 4),
                }

        results = {
            "summary": {
                "total_transactions": len(merged),
                "total_fraud": int(y_true.sum()),
                "total_normal": int((1 - y_true).sum()),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(roc_auc, 4),
                "pr_auc": round(pr_auc, 4),
            },
            "confusion_matrix": {
                "true_positives": int(tp),
                "false_positives": int(fp),
                "true_negatives": int(tn),
                "false_negatives": int(fn),
            },
            "threat_breakdown": threat_breakdown,
        }

        return results
