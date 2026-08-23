"""
Unit and Integration Tests for Red Team Adversarial Generator.
"""

import unittest
import os
import shutil
import tempfile
import pandas as pd
import numpy as np

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
from red_team.orchestrator import RedTeamOrchestrator
from red_team.evasion_tuner import EvasionTuner
from red_team.metrics import validate_zero_leakage, compute_statistical_realism


class TestRedTeamEngine(unittest.TestCase):
    """Test suite verifying Red Team generator functionality and constraints."""

    def setUp(self):
        self.config = RedTeamConfig(
            seed=123,
            simulation_days=7,
            num_users=50,
            num_merchants=20,
            total_transactions=500,
            fraud_ratio=0.10,
            stealth_level=0.0,
        )
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_schema_and_zero_leakage(self):
        """Verify public columns match data contract exactly and zero ground truth leaks."""
        orch = RedTeamOrchestrator(self.config)
        df_pub, df_ans = orch.generate_batch()

        # Check column equality
        self.assertListEqual(list(df_pub.columns), PUBLIC_COLUMNS)
        self.assertListEqual(list(df_ans.columns), ANSWER_KEY_COLUMNS)
        self.assertEqual(len(df_pub), 500)
        self.assertEqual(len(df_ans), 500)

        # Check zero leakage
        leakage = validate_zero_leakage(df_pub)
        self.assertTrue(leakage["passed"])
        self.assertEqual(len(leakage["leaked_columns"]), 0)

        # Check 1-to-1 foreign key mapping
        self.assertListEqual(
            list(df_pub["transaction_id"]),
            list(df_ans["transaction_id"])
        )

    def test_chronological_ordering_and_velocity(self):
        """Verify transactions are strictly sorted in time and velocity is computed."""
        orch = RedTeamOrchestrator(self.config)
        df_pub, _ = orch.generate_batch()

        timestamps = pd.to_datetime(df_pub["timestamp"])
        self.assertTrue(timestamps.is_monotonic_increasing)

        # Check velocity columns are non-negative integers
        self.assertTrue((df_pub["velocity_1h"] >= 0).all())
        self.assertTrue((df_pub["velocity_24h"] >= df_pub["velocity_1h"]).all())

    def test_threat_generators_present_in_output(self):
        """Verify all 3 attack threats appear in expected proportions."""
        orch = RedTeamOrchestrator(self.config)
        _, df_ans = orch.generate_batch()

        labels = df_ans["ground_truth_label"].value_counts().to_dict()
        
        self.assertIn(LABEL_NORMAL, labels)
        self.assertIn(LABEL_VOICE_CLONE, labels)
        self.assertIn(LABEL_EPHEMERAL_MERCHANT, labels)
        self.assertIn(LABEL_DIGITAL_ARREST, labels)

        # 10% fraud of 500 = 50 fraud rows
        self.assertEqual(labels[LABEL_NORMAL], 450)
        total_fraud = labels[LABEL_VOICE_CLONE] + labels[LABEL_EPHEMERAL_MERCHANT] + labels[LABEL_DIGITAL_ARREST]
        self.assertEqual(total_fraud, 50)

    def test_stealth_adaptation_effects(self):
        """Verify that higher stealth levels alter attack feature values as intended."""
        # Low Stealth
        orch_low = RedTeamOrchestrator(RedTeamConfig(seed=42, total_transactions=200, fraud_ratio=1.0, stealth_level=0.0))
        df_pub_low, df_ans_low = orch_low.generate_batch()

        # High Stealth
        orch_high = RedTeamOrchestrator(RedTeamConfig(seed=42, total_transactions=200, fraud_ratio=1.0, stealth_level=1.0))
        df_pub_high, df_ans_high = orch_high.generate_batch()

        # Filter Digital Arrest rows
        da_low_ids = df_ans_low[df_ans_low["ground_truth_label"] == LABEL_DIGITAL_ARREST]["transaction_id"]
        da_high_ids = df_ans_high[df_ans_high["ground_truth_label"] == LABEL_DIGITAL_ARREST]["transaction_id"]

        da_low_pub = df_pub_low[df_pub_low["transaction_id"].isin(da_low_ids)]
        da_high_pub = df_pub_high[df_pub_high["transaction_id"].isin(da_high_ids)]

        # Low stealth Digital Arrest has concurrent calls active (100%), High stealth masks it (0%)
        self.assertTrue(da_low_pub["concurrent_call_active"].mean() > 0.8)
        self.assertEqual(da_high_pub["concurrent_call_active"].mean(), 0.0)

    def test_csv_export(self):
        """Verify CSV export writes valid files."""
        orch = RedTeamOrchestrator(self.config)
        pub_path, ans_path = orch.export_to_csv(output_dir=self.temp_dir)

        self.assertTrue(os.path.exists(pub_path))
        self.assertTrue(os.path.exists(ans_path))

        df_p = pd.read_csv(pub_path)
        df_a = pd.read_csv(ans_path)

        self.assertEqual(len(df_p), 500)
        self.assertEqual(len(df_a), 500)

    def test_evasion_tuner_feedback_loop(self):
        """Verify closed-loop feedback evaluates Blue Team scores and adjusts stealth."""
        orch = RedTeamOrchestrator(self.config)
        df_pub, df_ans = orch.generate_batch()

        # Simulate a naive Blue Team model that flags high amounts and new payees
        pred_rows = []
        for _, row in df_pub.iterrows():
            prob = 0.9 if (row["amount"] > 400 and row["new_payee_flag"]) else 0.05
            pred_rows.append({"transaction_id": row["transaction_id"], "fraud_probability": prob})
        df_preds = pd.DataFrame(pred_rows)

        tuner = EvasionTuner(self.config)
        eval_result = tuner.evaluate_blue_team(df_ans, df_preds, decision_threshold=0.5)

        self.assertIn("overall_recall", eval_result)
        self.assertIn("threat_breakdown", eval_result)
        self.assertTrue(eval_result["total_fraud"] == 50)

        # Suggest next iteration
        next_iter = tuner.suggest_next_iteration(eval_result, current_stealth=0.0, step_size=0.2)
        self.assertGreater(next_iter["recommended_stealth"], 0.0)
        self.assertEqual(len(tuner.history), 1)


if __name__ == "__main__":
    unittest.main()
