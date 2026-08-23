"""
Unit and Integration Tests for Blue Team Defense Pipeline.
"""

import unittest
import os
import shutil
import tempfile
import pandas as pd
import numpy as np

from red_team.config import RedTeamConfig
from red_team.orchestrator import RedTeamOrchestrator
from blue_team.config import BlueTeamConfig, TIER_LOW, TIER_MEDIUM, TIER_HIGH
from blue_team.preprocessor import BlueTeamPreprocessor
from blue_team.rule_engine import RuleEngine
from blue_team.models.ml_detector import MLFraudDetector
from blue_team.models.ensemble import EnsembleFraudDetector
from blue_team.pipeline import BlueTeamPipeline
from blue_team.evaluator import BlueTeamEvaluator
from blue_team.retrainer import BlueTeamRetrainer


class TestBlueTeamPipeline(unittest.TestCase):
    """Test suite for Blue Team Defense modules."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Generate synthetic test dataset via Red Team
        red_config = RedTeamConfig(
            seed=42,
            num_users=30,
            num_merchants=10,
            total_transactions=300,
            fraud_ratio=0.15,
            stealth_level=0.2,
        )
        orch = RedTeamOrchestrator(red_config)
        self.df_public, self.df_answer = orch.generate_batch()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_preprocessor(self):
        """Test feature extraction, scaling, and categorical encoding."""
        pre = BlueTeamPreprocessor()
        X = pre.fit_transform(self.df_public)

        self.assertEqual(X.shape[0], len(self.df_public))
        self.assertGreater(X.shape[1], 15)
        self.assertFalse(np.isnan(X).any())

    def test_rule_engine(self):
        """Test heuristic rule evaluations and tripwires."""
        rule_eng = RuleEngine()
        scores, rules_list, crit_flags = rule_eng.batch_evaluate(self.df_public)

        self.assertEqual(len(scores), len(self.df_public))
        self.assertEqual(len(rules_list), len(self.df_public))
        self.assertEqual(len(crit_flags), len(self.df_public))
        self.assertTrue((scores >= 0.0).all() and (scores <= 1.0).all())

    def test_pipeline_train_predict_and_persistence(self):
        """Test end-to-end training, risk triage tiering, save, and load."""
        pipeline = BlueTeamPipeline()
        pipeline.train(self.df_public, self.df_answer)
        self.assertTrue(pipeline.is_trained)

        # Predict on same batch
        preds = pipeline.predict(self.df_public)
        self.assertEqual(len(preds), len(self.df_public))
        self.assertIn("fraud_probability", preds.columns)
        self.assertIn("risk_tier", preds.columns)
        self.assertIn("fired_rules", preds.columns)

        # Validate risk tiers are only LOW, MEDIUM, or HIGH
        valid_tiers = {TIER_LOW, TIER_MEDIUM, TIER_HIGH}
        self.assertTrue(set(preds["risk_tier"]).issubset(valid_tiers))

        # Test Save & Load
        save_path = pipeline.save(self.temp_dir)
        loaded = BlueTeamPipeline.load(save_path)
        self.assertTrue(loaded.is_trained)

        preds_loaded = loaded.predict(self.df_public)
        pd.testing.assert_frame_equal(preds, preds_loaded)

    def test_evaluator_metrics(self):
        """Test performance evaluation metrics and threat breakdowns."""
        pipeline = BlueTeamPipeline()
        pipeline.train(self.df_public, self.df_answer)
        preds = pipeline.predict(self.df_public)

        evaluator = BlueTeamEvaluator(threshold=0.50)
        report = evaluator.evaluate(preds, self.df_answer)

        summary = report["summary"]
        self.assertIn("precision", summary)
        self.assertIn("recall", summary)
        self.assertIn("f1_score", summary)
        self.assertIn("roc_auc", summary)
        self.assertGreater(summary["roc_auc"], 0.70)

        threats = report["threat_breakdown"]
        self.assertIn("voice_clone_app", threats)
        self.assertIn("ephemeral_merchant", threats)
        self.assertIn("digital_arrest", threats)

    def test_retrainer_multi_cycle(self):
        """Test multi-cycle retraining loop."""
        retrainer = BlueTeamRetrainer()
        cycle1 = retrainer.initial_train(self.df_public, self.df_answer)
        self.assertEqual(cycle1["cycle"], 1)

        # Generate second adversarial batch
        orch_harder = RedTeamOrchestrator(RedTeamConfig(seed=99, total_transactions=200, fraud_ratio=0.2, stealth_level=0.8))
        df_pub2, df_ans2 = orch_harder.generate_batch()

        cycle2 = retrainer.retrain_with_adversarial_batch(
            df_pub2, df_ans2, self.df_public, self.df_answer
        )
        self.assertEqual(cycle2["cycle"], 2)
        self.assertEqual(len(retrainer.iteration_history), 2)


if __name__ == "__main__":
    unittest.main()
