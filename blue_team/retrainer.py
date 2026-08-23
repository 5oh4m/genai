"""
Blue Team Active Retraining Engine.
Executes closed-loop retraining when Red Team evasion attacks bypass the defense model.
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from blue_team.config import BlueTeamConfig
from blue_team.pipeline import BlueTeamPipeline
from blue_team.evaluator import BlueTeamEvaluator


class BlueTeamRetrainer:
    """Manages active retraining cycles and tracks iteration metrics."""

    def __init__(self, config: Optional[BlueTeamConfig] = None):
        self.config = config or BlueTeamConfig()
        self.pipeline: Optional[BlueTeamPipeline] = None
        self.evaluator = BlueTeamEvaluator(threshold=self.config.decision_threshold)
        self.iteration_history: List[Dict[str, Any]] = []

    def initial_train(
        self,
        df_train_public: pd.DataFrame,
        df_train_answer: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Runs the initial baseline training cycle."""
        self.pipeline = BlueTeamPipeline(self.config)
        self.pipeline.train(df_train_public, df_train_answer)
        
        preds = self.pipeline.predict(df_train_public)
        metrics = self.evaluator.evaluate(preds, df_train_answer)
        
        record = {
            "cycle": 1,
            "type": "initial_baseline",
            "training_samples": len(df_train_public),
            "metrics": metrics,
        }
        self.iteration_history.append(record)
        return record

    def retrain_with_adversarial_batch(
        self,
        df_new_public: pd.DataFrame,
        df_new_answer: pd.DataFrame,
        historical_public: Optional[pd.DataFrame] = None,
        historical_answer: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        Retrains the model incorporating newly discovered adversarial evasion samples.
        """
        if historical_public is not None and historical_answer is not None:
            df_combined_pub = pd.concat([historical_public, df_new_public], ignore_index=True)
            df_combined_ans = pd.concat([historical_answer, df_new_answer], ignore_index=True)
        else:
            df_combined_pub = df_new_public
            df_combined_ans = df_new_answer

        # Train updated pipeline
        self.pipeline = BlueTeamPipeline(self.config)
        self.pipeline.train(df_combined_pub, df_combined_ans)

        # Evaluate on the new adversarial batch
        preds_new = self.pipeline.predict(df_new_public)
        metrics_new = self.evaluator.evaluate(preds_new, df_new_answer)

        record = {
            "cycle": len(self.iteration_history) + 1,
            "type": "adversarial_retrain",
            "training_samples": len(df_combined_pub),
            "metrics": metrics_new,
        }
        self.iteration_history.append(record)
        return record
