"""
Blue Team evaluator — computes defense performance metrics.
Adapted from the old evaluator.py to work with attack attempts instead of tabular predictions.
"""

from typing import Any
from collections import Counter


class BlueTeamEvaluator:
    """Computes defense metrics from attack attempt records."""

    @staticmethod
    def evaluate(attempts: list[dict]) -> dict[str, Any]:
        """
        Compute defense performance metrics from a list of attempt dicts.

        Args:
            attempts: List of AttackAttempt.to_dict() results.

        Returns:
            Metrics dict with overall and per-category breakdowns.
        """
        if not attempts:
            return {
                "total_attempts": 0,
                "success_rate": 0.0,
                "block_rate": 0.0,
                "escalation_rate": 0.0,
            }

        total = len(attempts)
        successes = sum(1 for a in attempts if a.get("success", False))
        blocked = sum(1 for a in attempts if a.get("blue_team_verdict") == "blocked")
        escalated = sum(1 for a in attempts if a.get("blue_team_verdict") == "escalated")
        allowed = sum(1 for a in attempts if a.get("blue_team_verdict") == "allowed")

        # Per-category breakdown
        categories = set(a.get("objective_category", "unknown") for a in attempts)
        category_breakdown = {}
        for cat in categories:
            cat_attempts = [a for a in attempts if a.get("objective_category") == cat]
            cat_total = len(cat_attempts)
            cat_success = sum(1 for a in cat_attempts if a.get("success", False))
            cat_blocked = sum(1 for a in cat_attempts if a.get("blue_team_verdict") == "blocked")
            category_breakdown[cat] = {
                "total": cat_total,
                "successes": cat_success,
                "blocked": cat_blocked,
                "success_rate": round(cat_success / max(1, cat_total), 4),
                "block_rate": round(cat_blocked / max(1, cat_total), 4),
            }

        # Per-target breakdown
        targets = set(a.get("target_name", "unknown") for a in attempts)
        target_breakdown = {}
        for tgt in targets:
            tgt_attempts = [a for a in attempts if a.get("target_name") == tgt]
            tgt_total = len(tgt_attempts)
            tgt_success = sum(1 for a in tgt_attempts if a.get("success", False))
            tgt_blocked = sum(1 for a in tgt_attempts if a.get("blue_team_verdict") == "blocked")
            target_breakdown[tgt] = {
                "total": tgt_total,
                "successes": tgt_success,
                "blocked": tgt_blocked,
                "success_rate": round(tgt_success / max(1, tgt_total), 4),
                "block_rate": round(tgt_blocked / max(1, tgt_total), 4),
            }

        # Converter effectiveness
        converter_counts = Counter()
        converter_successes = Counter()
        for a in attempts:
            conv = a.get("converter_used", "none")
            converter_counts[conv] += 1
            if a.get("success", False):
                converter_successes[conv] += 1

        converter_breakdown = {
            conv: {
                "total": converter_counts[conv],
                "successes": converter_successes[conv],
                "success_rate": round(converter_successes[conv] / max(1, converter_counts[conv]), 4),
            }
            for conv in converter_counts
        }

        return {
            "total_attempts": total,
            "successful_attacks": successes,
            "blocked_attacks": blocked,
            "escalated_attacks": escalated,
            "allowed_attacks": allowed,
            "success_rate": round(successes / max(1, total), 4),
            "block_rate": round(blocked / max(1, total), 4),
            "escalation_rate": round(escalated / max(1, total), 4),
            "category_breakdown": category_breakdown,
            "target_breakdown": target_breakdown,
            "converter_breakdown": converter_breakdown,
        }
