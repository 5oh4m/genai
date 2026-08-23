"""
Red Team Orchestrator.
Coordinates baseline traffic and adversarial attack generators,
computes dynamic behavioral velocity/deviation features, and outputs
cleanly separated blind transaction features and confidential answer keys.
"""

import os
import argparse
import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from faker import Faker

from red_team.config import (
    RedTeamConfig,
    PUBLIC_COLUMNS,
    ANSWER_KEY_COLUMNS,
    LABEL_NORMAL,
    LABEL_VOICE_CLONE,
    LABEL_EPHEMERAL_MERCHANT,
    LABEL_DIGITAL_ARREST,
)
from red_team.baseline_generator import BaselineGenerator
from red_team.attack_generators.voice_clone_app import VoiceCloneAPPGenerator
from red_team.attack_generators.ephemeral_merchant import EphemeralMerchantGenerator
from red_team.attack_generators.digital_arrest import DigitalArrestGenerator


class RedTeamOrchestrator:
    """Master controller for the Red Team synthetic transaction engine."""

    def __init__(self, config: Optional[RedTeamConfig] = None):
        self.config = config or RedTeamConfig()
        self.rng = np.random.RandomState(self.config.seed)
        self.fake = Faker()
        Faker.seed(self.config.seed)

        # Initialize baseline foundation & population
        self.baseline_gen = BaselineGenerator(self.config)
        self.users = self.baseline_gen.users
        self.merchants = self.baseline_gen.merchants

        # Initialize attack generators
        self.attack_generators = {
            "voice_clone_app": VoiceCloneAPPGenerator(
                self.config, self.users, self.merchants, self.rng, self.fake
            ),
            "ephemeral_merchant": EphemeralMerchantGenerator(
                self.config, self.users, self.merchants, self.rng, self.fake
            ),
            "digital_arrest": DigitalArrestGenerator(
                self.config, self.users, self.merchants, self.rng, self.fake
            ),
        }

    def generate_batch(
        self,
        total_transactions: Optional[int] = None,
        fraud_ratio: Optional[float] = None,
        stealth_level: Optional[float] = None,
        threat_weights: Optional[Dict[str, float]] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Synthesizes a complete labeled stream of transactions and separates it into
        public features and the confidential answer key.
        """
        total = total_transactions if total_transactions is not None else self.config.total_transactions
        ratio = fraud_ratio if fraud_ratio is not None else self.config.fraud_ratio
        stealth = stealth_level if stealth_level is not None else self.config.stealth_level
        weights = threat_weights or self.config.threat_weights

        num_fraud = int(round(total * ratio))
        num_baseline = total - num_fraud

        # 1. Generate Baseline Transactions
        txns_all, answers_all = self.baseline_gen.generate_baseline_transactions(num_baseline)

        # 2. Generate Attack Transactions partitioned across threats
        if num_fraud > 0:
            total_weight = sum(weights.values())
            normalized_weights = {k: v / total_weight for k, v in weights.items()}
            
            allocated_counts = {}
            remaining = num_fraud
            threat_keys = list(normalized_weights.keys())
            
            for k in threat_keys[:-1]:
                c = int(round(num_fraud * normalized_weights[k]))
                allocated_counts[k] = c
                remaining -= c
            allocated_counts[threat_keys[-1]] = max(0, remaining)

            for threat_name, threat_count in allocated_counts.items():
                if threat_count > 0 and threat_name in self.attack_generators:
                    gen = self.attack_generators[threat_name]
                    a_txns, a_answers = gen.generate(threat_count, stealth_level=stealth)
                    txns_all.extend(a_txns)
                    answers_all.extend(a_answers)

        # 3. Combine and Chronologically Sort
        combined = []
        for t, a in zip(txns_all, answers_all):
            combined.append((t, a))

        combined.sort(key=lambda item: datetime.datetime.fromisoformat(item[0]["timestamp"]))

        # 4. Assign sequential Transaction IDs & Dynamic Derived Features
        # Track historical transactions per user for velocity and new_payee
        user_txn_history: Dict[str, List[Tuple[datetime.datetime, float, str]]] = {
            u: [] for u in self.users.keys()
        }
        
        # Pre-seed history with baseline familiar payees
        for user in self.users.values():
            for payee in user.frequent_payees:
                seed_dt = user.payee_added_timestamps.get(
                    payee, self.baseline_gen.start_dt - datetime.timedelta(days=60)
                )
                user_txn_history[user.user_id].append((seed_dt, user.base_mean_amount, payee))

        final_public_rows: List[Dict] = []
        final_answer_rows: List[Dict] = []

        for idx, (t, a) in enumerate(combined, start=1):
            txn_id = f"TXN_{idx:07d}"
            t["transaction_id"] = txn_id
            a["transaction_id"] = txn_id

            sender_id = t["sender_id"]
            receiver_id = t["receiver_id"]
            txn_amount = float(t["amount"])
            curr_dt = datetime.datetime.fromisoformat(t["timestamp"])

            # Compute Velocity & Amount Deviation
            if sender_id in user_txn_history:
                history = user_txn_history[sender_id]
                one_hour_ago = curr_dt - datetime.timedelta(seconds=3600)
                twenty_four_hours_ago = curr_dt - datetime.timedelta(seconds=86400)

                v_1h = sum(1 for dt, _, _ in history if one_hour_ago <= dt < curr_dt)
                v_24h = sum(1 for dt, _, _ in history if twenty_four_hours_ago <= dt < curr_dt)

                # Prior receiver history
                seen_receivers = {rec for _, _, rec in history}
                is_new_payee = receiver_id not in seen_receivers

                # Amount deviation z-score vs user baseline
                user_profile = self.users.get(sender_id)
                if user_profile:
                    mean_amt = user_profile.base_mean_amount
                    std_amt = mean_amt * user_profile.amount_sigma
                    z_score = (txn_amount - mean_amt) / max(1.0, std_amt)
                else:
                    z_score = 0.0

                # Record in history
                history.append((curr_dt, txn_amount, receiver_id))
            else:
                v_1h = 0
                v_24h = 0
                is_new_payee = True
                z_score = 0.0

            t["velocity_1h"] = v_1h
            t["velocity_24h"] = v_24h
            t["amount_deviation_score"] = round(float(z_score), 3)
            t["new_payee_flag"] = bool(is_new_payee)

            final_public_rows.append({col: t[col] for col in PUBLIC_COLUMNS})
            final_answer_rows.append({col: a[col] for col in ANSWER_KEY_COLUMNS})

        df_public = pd.DataFrame(final_public_rows)[PUBLIC_COLUMNS]
        df_answer = pd.DataFrame(final_answer_rows)[ANSWER_KEY_COLUMNS]

        return df_public, df_answer

    def export_to_csv(
        self,
        output_dir: str = "data",
        total_transactions: Optional[int] = None,
        fraud_ratio: Optional[float] = None,
        stealth_level: Optional[float] = None,
    ) -> Tuple[str, str]:
        """
        Generates and saves `blind_transactions.csv` and `oracle_answer_key.csv`.
        """
        os.makedirs(output_dir, exist_ok=True)
        df_public, df_answer = self.generate_batch(
            total_transactions=total_transactions,
            fraud_ratio=fraud_ratio,
            stealth_level=stealth_level,
        )

        public_path = os.path.join(output_dir, "blind_transactions.csv")
        answer_path = os.path.join(output_dir, "oracle_answer_key.csv")

        df_public.to_csv(public_path, index=False)
        df_answer.to_csv(answer_path, index=False)

        return public_path, answer_path


def main():
    parser = argparse.ArgumentParser(description="Red Team Synthetic Data & Adversarial Stream Generator")
    parser.add_argument("--total-txns", type=int, default=10000, help="Total transactions to generate")
    parser.add_argument("--fraud-ratio", type=float, default=0.05, help="Proportion of fraudulent transactions (0.0 - 1.0)")
    parser.add_argument("--stealth", type=float, default=0.0, help="Adversarial stealth level (0.0 to 1.0)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="data", help="Directory to save CSV outputs")
    
    args = parser.parse_args()

    config = RedTeamConfig(
        seed=args.seed,
        total_transactions=args.total_txns,
        fraud_ratio=args.fraud_ratio,
        stealth_level=args.stealth,
    )

    orchestrator = RedTeamOrchestrator(config)
    pub_path, ans_path = orchestrator.export_to_csv(
        output_dir=args.output_dir,
        total_transactions=args.total_txns,
        fraud_ratio=args.fraud_ratio,
        stealth_level=args.stealth,
    )

    print("==================================================")
    print("  RED TEAM ADVERSARIAL GENERATOR COMPLETED")
    print("==================================================")
    print(f"Total Transactions: {args.total_txns}")
    print(f"Fraud Ratio:        {args.fraud_ratio:.1%}")
    print(f"Stealth Level:      {args.stealth:.2f}")
    print(f"Random Seed:        {args.seed}")
    print("--------------------------------------------------")
    print(f"Public Blind Data:  {pub_path}")
    print(f"Oracle Answer Key:  {ans_path}")
    print("==================================================")


if __name__ == "__main__":
    main()
