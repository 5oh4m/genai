"""
Heuristic Rule Engine for Real-Time GenAI Scam & Telemetry Tripwires.
"""

from typing import List, Dict, Tuple, Any
import pandas as pd
import numpy as np


class RuleEngine:
    """
    Evaluates rule-based heuristics and telemetry safety tripwires
    designed specifically for GenAI coercion, APP, and merchant fraud patterns.
    """

    def __init__(self):
        self.rule_definitions = {
            "RULE_INSTANT_TRANSFER_NEW_PAYEE": "Transfer initiated immediately (<60s) after adding new payee",
            "RULE_HOSTAGE_CALL_COERCION": "Active concurrent call during session with high-value transfer",
            "RULE_PROLONGED_SESSION_DWELL": "Abnormally long session (>1200s) indicating coercion or digital arrest",
            "RULE_FRESH_MERCHANT_BURST": "Payment to newly created merchant (<5 days old)",
            "RULE_EXTREME_AMOUNT_DEVIATION": "Amount exceeds 3.5 standard deviations from sender baseline",
            "RULE_VELOCITY_SURGE": "Rapid velocity surge (>2 transactions in past 1 hour) to new payee",
        }

    def evaluate_transaction(self, row: Dict[str, Any]) -> Tuple[float, List[str], bool]:
        """
        Evaluate a single transaction dictionary against heuristic rules.
        
        Returns:
            Tuple of (heuristic_risk_score, fired_rules, is_critical_override)
        """
        fired_rules = []
        rule_scores = []
        is_critical = False

        amount = float(row.get("amount", 0.0))
        new_payee = bool(row.get("new_payee_flag", False))
        time_since_payee = float(row.get("time_since_payee_added_sec", 999999))
        rec_age_days = float(row.get("receiver_account_age_days", 999))
        session_dur = float(row.get("session_duration_sec", 0))
        concurrent_call = bool(row.get("concurrent_call_active", False))
        amount_dev = float(row.get("amount_deviation_score", 0.0))
        velocity_1h = int(row.get("velocity_1h", 0))
        receiver_id = str(row.get("receiver_id", ""))

        # Rule 1: Instant Transfer to New Payee
        if new_payee and time_since_payee <= 60 and rec_age_days <= 7:
            fired_rules.append("RULE_INSTANT_TRANSFER_NEW_PAYEE")
            rule_scores.append(0.88)
            if time_since_payee <= 30:
                is_critical = True

        # Rule 2: Active Call Coercion
        if concurrent_call:
            if session_dur >= 300 or amount >= 1000.0 or amount_dev >= 2.0:
                fired_rules.append("RULE_HOSTAGE_CALL_COERCION")
                rule_scores.append(0.95)
                is_critical = True
            else:
                rule_scores.append(0.50)

        # Rule 3: Prolonged Session Dwell
        if session_dur >= 1800 and (amount_dev >= 1.5 or amount >= 1500.0):
            fired_rules.append("RULE_PROLONGED_SESSION_DWELL")
            rule_scores.append(0.85)

        # Rule 4: Fresh Ephemeral Merchant
        if receiver_id.startswith("MER_") and rec_age_days <= 4 and amount >= 25.0:
            fired_rules.append("RULE_FRESH_MERCHANT_BURST")
            rule_scores.append(0.75)

        # Rule 5: Extreme Amount Deviation
        if amount_dev >= 3.5 and new_payee:
            fired_rules.append("RULE_EXTREME_AMOUNT_DEVIATION")
            rule_scores.append(0.80)

        # Rule 6: Velocity Surge
        if velocity_1h >= 2 and new_payee:
            fired_rules.append("RULE_VELOCITY_SURGE")
            rule_scores.append(0.70)

        # Aggregate score
        final_score = max(rule_scores) if rule_scores else 0.05
        return final_score, fired_rules, is_critical

    def batch_evaluate(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[List[str]], np.ndarray]:
        """
        Evaluate an entire DataFrame of transactions.
        
        Returns:
            scores array (N,), fired_rules list of lists, critical_flags array (N,)
        """
        scores = []
        all_fired = []
        critical_flags = []

        for _, row in df.iterrows():
            score, rules, is_crit = self.evaluate_transaction(row.to_dict())
            scores.append(score)
            all_fired.append(rules)
            critical_flags.append(is_crit)

        return np.array(scores, dtype=float), all_fired, np.array(critical_flags, dtype=bool)
