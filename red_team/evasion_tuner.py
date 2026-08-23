"""
Evasion Tuner: Closed-Loop Adversarial Mutator.
Analyzes Blue Team predictions, isolates False Negatives (successful evasions),
and dynamically optimizes attack evasion parameters to drive model retraining.
"""

from typing import Dict, List, Tuple, Any, Optional
import json
import pandas as pd
import numpy as np

from red_team.config import (
    RedTeamConfig,
    LABEL_NORMAL,
    LABEL_VOICE_CLONE,
    LABEL_EPHEMERAL_MERCHANT,
    LABEL_DIGITAL_ARREST,
    ATTACK_NAMES,
)


class EvasionTuner:
    """
    Closed-loop feedback engine that evaluates Blue Team detection performance
    and evolves attack strategies for the next generation.
    """

    def __init__(self, config: Optional[RedTeamConfig] = None):
        self.config = config or RedTeamConfig()
        self.history: List[Dict[str, Any]] = []

    def evaluate_blue_team(
        self,
        df_answer_key: pd.DataFrame,
        df_predictions: pd.DataFrame,
        decision_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Evaluate Blue Team predictions against the confidential oracle answer key.
        
        Args:
            df_answer_key: Oracle ground truth answer key.
            df_predictions: Blue Team output containing 'transaction_id' and 'fraud_probability'.
            decision_threshold: Classification threshold for fraud.
            
        Returns:
            Dictionary containing metrics breakdown, false negatives, and evasion recommendations.
        """
        merged = pd.merge(df_answer_key, df_predictions, on="transaction_id", how="inner")
        
        if merged.empty:
            raise ValueError("No matching transaction IDs between answer key and predictions!")

        # Categorize outcomes
        merged["is_actual_fraud"] = merged["ground_truth_label"] != LABEL_NORMAL
        merged["is_pred_fraud"] = merged["fraud_probability"] >= decision_threshold

        # Attack breakdown
        attack_metrics = {}
        total_fraud_count = int(merged["is_actual_fraud"].sum())
        detected_fraud_count = int((merged["is_actual_fraud"] & merged["is_pred_fraud"]).sum())
        overall_recall = detected_fraud_count / max(1, total_fraud_count)
        overall_evasion_rate = 1.0 - overall_recall

        for label, name in ATTACK_NAMES.items():
            if label == LABEL_NORMAL:
                continue
            subset = merged[merged["ground_truth_label"] == label]
            if not subset.empty:
                n_total = len(subset)
                n_detected = int(subset["is_pred_fraud"].sum())
                rec = n_detected / n_total
                evasion_rate = 1.0 - rec
                avg_prob = float(subset["fraud_probability"].mean())
                attack_metrics[name] = {
                    "total": n_total,
                    "detected": n_detected,
                    "evaded": n_total - n_detected,
                    "recall": round(rec, 4),
                    "evasion_rate": round(evasion_rate, 4),
                    "avg_fraud_probability": round(avg_prob, 4),
                }

        # Analyze False Negatives (Bypassed Attacks)
        false_negatives = merged[merged["is_actual_fraud"] & (~merged["is_pred_fraud"])]
        
        # Successful evasion technique frequencies
        top_evasion_tricks = (
            false_negatives["evasion_technique"].value_counts().to_dict()
            if not false_negatives.empty
            else {}
        )

        evaluation_result = {
            "total_evaluated": len(merged),
            "total_fraud": total_fraud_count,
            "detected_fraud": detected_fraud_count,
            "overall_recall": round(overall_recall, 4),
            "overall_evasion_rate": round(overall_evasion_rate, 4),
            "threat_breakdown": attack_metrics,
            "top_evasion_techniques": top_evasion_tricks,
            "bypassed_sample_count": len(false_negatives),
        }

        return evaluation_result

    def suggest_next_iteration(
        self,
        eval_result: Dict[str, Any],
        current_stealth: float,
        step_size: float = 0.25,
    ) -> Dict[str, Any]:
        """
        Calculates the next adversarial iteration based on model weaknesses.
        """
        overall_recall = eval_result["overall_recall"]
        threat_breakdown = eval_result["threat_breakdown"]

        # If Blue Team has high detection (e.g. recall > 80%), increase stealth
        if overall_recall >= 0.70:
            new_stealth = min(1.0, current_stealth + step_size)
            strategy = "escalate_stealth_and_timing_padding"
        elif overall_recall <= 0.30:
            # Model is already failing, refine around current stealth
            new_stealth = current_stealth
            strategy = "maintain_heavy_evasion_pressure"
        else:
            new_stealth = min(1.0, current_stealth + (step_size / 2))
            strategy = "moderate_adversarial_nudging"

        # Threat re-weighting: Focus attacks on whichever threat has highest evasion success
        new_weights = {}
        total_evasions = 0
        for threat, m in threat_breakdown.items():
            evasion_count = m.get("evaded", 1) + 1  # Laplace smoothing
            new_weights[threat] = evasion_count
            total_evasions += evasion_count

        normalized_weights = {k: round(v / total_evasions, 3) for k, v in new_weights.items()}

        recommendation = {
            "current_stealth": current_stealth,
            "recommended_stealth": round(new_stealth, 2),
            "adaptation_strategy": strategy,
            "recommended_threat_weights": normalized_weights,
            "reasoning": (
                f"Blue Team achieved {overall_recall:.1%} detection. "
                f"Escalating stealth to {new_stealth:.2f} with emphasis on '{max(normalized_weights, key=normalized_weights.get)}'."
            ),
        }

        # Log to evolution history
        iteration_log = {
            "iteration": len(self.history) + 1,
            "evaluation": eval_result,
            "recommendation": recommendation,
        }
        self.history.append(iteration_log)

        return recommendation
