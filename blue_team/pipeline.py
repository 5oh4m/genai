"""
End-to-End Blue Team Defense Pipeline.
Handles training, real-time inference, explanation tags, and prediction export.
"""

import os
import argparse
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import joblib

from blue_team.config import (
    BlueTeamConfig,
    TIER_LOW,
    TIER_MEDIUM,
    TIER_HIGH,
)
from blue_team.preprocessor import BlueTeamPreprocessor
from blue_team.rule_engine import RuleEngine
from blue_team.models.ensemble import EnsembleFraudDetector


class BlueTeamPipeline:
    """Master pipeline for training, model persistence, and real-time transaction scoring."""

    def __init__(self, config: Optional[BlueTeamConfig] = None):
        self.config = config or BlueTeamConfig()
        self.preprocessor = BlueTeamPreprocessor(self.config)
        self.rule_engine = RuleEngine()
        self.ensemble = EnsembleFraudDetector(self.config)
        self.is_trained: bool = False

    def train(
        self,
        df_public: pd.DataFrame,
        df_answer_key: pd.DataFrame,
    ) -> "BlueTeamPipeline":
        """
        Train the Blue Team defense model using public transaction features
        and confidential labels provided during supervised training phases.
        """
        # Ensure aligned on transaction_id
        merged = pd.merge(df_public, df_answer_key[["transaction_id", "ground_truth_label"]], on="transaction_id")
        
        # Binary target: 0 = Normal, 1 = Any Fraud
        y = (merged["ground_truth_label"] != 0).astype(int).values

        # Preprocess features
        X = self.preprocessor.fit_transform(merged)

        # Fit Ensemble / ML model
        self.ensemble.fit(X, y)
        self.is_trained = True
        return self

    def predict(self, df_public: pd.DataFrame) -> pd.DataFrame:
        """
        Scores a blind transaction batch, returning calibrated probabilities,
        risk tiers, and rule explanations.
        """
        if not self.is_trained:
            raise RuntimeError("Pipeline must be trained or loaded before making predictions!")

        # 1. Rule Engine evaluation
        rule_scores, fired_rules_list, crit_flags = self.rule_engine.batch_evaluate(df_public)

        # 2. ML feature transform and prediction
        X = self.preprocessor.transform(df_public)
        ml_probs = self.ensemble.ml_model.predict_proba(X)

        # 3. Ensemble blending
        final_probs = self.ensemble.predict_ensemble(X, rule_scores, crit_flags)

        # 4. Construct Output DataFrame
        pred_labels = (final_probs >= self.config.decision_threshold).astype(int)

        # Assign risk tiers
        risk_tiers = []
        for p in final_probs:
            if p >= self.config.high_risk_threshold:
                risk_tiers.append(TIER_HIGH)
            elif p >= self.config.medium_risk_threshold:
                risk_tiers.append(TIER_MEDIUM)
            else:
                risk_tiers.append(TIER_LOW)

        fired_rules_str = ["; ".join(rules) if rules else "none" for rules in fired_rules_list]

        df_preds = pd.DataFrame({
            "transaction_id": df_public["transaction_id"].values,
            "fraud_probability": np.round(final_probs, 4),
            "predicted_label": pred_labels,
            "risk_tier": risk_tiers,
            "fired_rules": fired_rules_str,
            "ml_probability": np.round(ml_probs, 4),
            "rule_score": np.round(rule_scores, 4),
        })

        return df_preds

    def save(self, model_dir: str = "models/blue_team") -> str:
        """Serializes the entire pipeline to disk."""
        os.makedirs(model_dir, exist_ok=True)
        bundle = {
            "config": self.config,
            "preprocessor": self.preprocessor,
            "ensemble": self.ensemble,
            "is_trained": self.is_trained,
        }
        out_path = os.path.join(model_dir, "blue_team_pipeline.joblib")
        joblib.dump(bundle, out_path)
        return out_path

    @classmethod
    def load(cls, model_path: str = "models/blue_team/blue_team_pipeline.joblib") -> "BlueTeamPipeline":
        """Loads a serialized pipeline from disk."""
        bundle = joblib.load(model_path)
        instance = cls(config=bundle["config"])
        instance.preprocessor = bundle["preprocessor"]
        instance.ensemble = bundle["ensemble"]
        instance.is_trained = bundle["is_trained"]
        return instance


def main():
    parser = argparse.ArgumentParser(description="Blue Team Defense Model Training & Inference CLI")
    parser.add_argument("--train-data", type=str, default="data/blind_transactions.csv", help="Path to public features CSV")
    parser.add_argument("--answer-key", type=str, default="data/oracle_answer_key.csv", help="Path to oracle answer key CSV")
    parser.add_argument("--save-dir", type=str, default="models/blue_team", help="Directory to save trained model")
    parser.add_argument("--output-preds", type=str, default="data/predictions.csv", help="Path to write inference output")
    
    args = parser.parse_args()

    df_pub = pd.read_csv(args.train_data)
    df_ans = pd.read_csv(args.answer_key)

    pipeline = BlueTeamPipeline()
    print("Training Blue Team defense pipeline...")
    pipeline.train(df_pub, df_ans)

    saved_path = pipeline.save(args.save_dir)
    print(f"Model successfully saved to: {saved_path}")

    # Generate predictions
    df_preds = pipeline.predict(df_pub)
    os.makedirs(os.path.dirname(args.output_preds) or ".", exist_ok=True)
    df_preds.to_csv(args.output_preds, index=False)
    print(f"Predictions saved to: {args.output_preds}")


if __name__ == "__main__":
    main()
