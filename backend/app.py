"""
FastAPI Backend Server for AEGIS-AI Cyber Defense & Fraud Lab.
Bridges the Red Team generator, Blue Team defense pipeline, rule engine,
and evasion feedback loops to the interactive desktop frontend.
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

# Ensure root directory is on Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from red_team.config import (
    RedTeamConfig,
    PUBLIC_COLUMNS,
    ANSWER_KEY_COLUMNS,
    LABEL_NORMAL,
    LABEL_VOICE_CLONE,
    LABEL_EPHEMERAL_MERCHANT,
    LABEL_DIGITAL_ARREST,
    ATTACK_NAMES,
)
from red_team.orchestrator import RedTeamOrchestrator
from red_team.evasion_tuner import EvasionTuner
from red_team.metrics import compute_statistical_realism, validate_zero_leakage

from blue_team.config import (
    BlueTeamConfig,
    TIER_LOW,
    TIER_MEDIUM,
    TIER_HIGH,
)
from blue_team.pipeline import BlueTeamPipeline
from blue_team.rule_engine import RuleEngine
from blue_team.evaluator import BlueTeamEvaluator
from blue_team.retrainer import BlueTeamRetrainer


app = FastAPI(
    title="AEGIS-AI Command Center API",
    description="Adversarial Cyber Defense and Financial Fraud Detection Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global In-Memory State
# ---------------------------------------------------------------------------

class SystemState:
    def __init__(self):
        self.df_public: Optional[pd.DataFrame] = None
        self.df_answer: Optional[pd.DataFrame] = None
        self.df_predictions: Optional[pd.DataFrame] = None
        
        self.pipeline: Optional[BlueTeamPipeline] = None
        self.retrainer: BlueTeamRetrainer = BlueTeamRetrainer()
        self.evasion_tuner: EvasionTuner = EvasionTuner()
        self.evaluator: BlueTeamEvaluator = BlueTeamEvaluator()
        self.rule_engine: RuleEngine = RuleEngine()
        
        self.last_red_config: Optional[RedTeamConfig] = None
        self.last_eval_report: Optional[Dict[str, Any]] = None
        self.last_realism_report: Optional[Dict[str, Any]] = None
        self.retrain_history: List[Dict[str, Any]] = []

state = SystemState()


def initialize_default_system():
    """Bootstraps the system with initial synthesized baseline dataset and trained pipeline."""
    print("Bootstrapping AEGIS-AI with default dataset & trained model...")
    cfg = RedTeamConfig(
        seed=42,
        num_users=100,
        num_merchants=30,
        total_transactions=1200,
        fraud_ratio=0.08,
        stealth_level=0.35,
    )
    state.last_red_config = cfg
    orch = RedTeamOrchestrator(cfg)
    df_pub, df_ans = orch.generate_batch()
    state.df_public = df_pub
    state.df_answer = df_ans
    state.last_realism_report = compute_statistical_realism(df_pub)

    # Train initial Blue Team pipeline
    state.pipeline = BlueTeamPipeline()
    state.pipeline.train(df_pub, df_ans)
    
    # Predict and evaluate
    state.df_predictions = state.pipeline.predict(df_pub)
    state.last_eval_report = state.evaluator.evaluate(state.df_predictions, df_ans)
    
    # Record baseline retrain cycle
    state.retrain_history.append({
        "cycle": 1,
        "type": "Initial Baseline Model",
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "samples": len(df_pub),
        "stealth": 0.35,
        "metrics": state.last_eval_report["summary"],
        "threat_breakdown": state.last_eval_report["threat_breakdown"],
    })
    print("Initialization complete.")


# ---------------------------------------------------------------------------
# Request/Response Schemas
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    total_transactions: int = Field(default=1000, ge=50, le=50000)
    fraud_ratio: float = Field(default=0.08, ge=0.01, le=0.60)
    stealth_level: float = Field(default=0.35, ge=0.0, le=1.0)
    seed: int = Field(default=42)
    voice_clone_weight: float = Field(default=0.40, ge=0.0, le=1.0)
    ephemeral_merchant_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    digital_arrest_weight: float = Field(default=0.25, ge=0.0, le=1.0)


class RetrainRequest(BaseModel):
    adversarial_samples: int = Field(default=400, ge=50, le=5000)
    stealth_level: float = Field(default=0.75, ge=0.0, le=1.0)
    fraud_ratio: float = Field(default=0.20, ge=0.05, le=0.50)


class SingleTransactionRequest(BaseModel):
    amount: float = Field(default=485.50, ge=0.01)
    channel: str = Field(default="UPI")
    sender_account_age_days: int = Field(default=120, ge=0)
    receiver_account_age_days: int = Field(default=2, ge=0)
    device_type: str = Field(default="Android")
    session_duration_sec: int = Field(default=95, ge=1)
    time_since_payee_added_sec: int = Field(default=35, ge=0)
    concurrent_call_active: bool = Field(default=True)
    ip_country: str = Field(default="US")
    ip_change_flag: bool = Field(default=False)
    login_to_transaction_gap_sec: int = Field(default=20, ge=0)
    velocity_1h: int = Field(default=2, ge=0)
    velocity_24h: int = Field(default=4, ge=0)
    amount_deviation_score: float = Field(default=2.8)
    new_payee_flag: bool = Field(default=True)
    receiver_id: str = Field(default="MULE_DA_001")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def get_health():
    return {
        "status": "ONLINE",
        "timestamp": datetime.datetime.now().isoformat(),
        "model_loaded": state.pipeline is not None and state.pipeline.is_trained,
        "total_transactions": len(state.df_public) if state.df_public is not None else 0,
        "current_cycle": len(state.retrain_history),
    }


@app.get("/api/state")
def get_state():
    if state.df_public is None or state.df_predictions is None:
        initialize_default_system()

    # Merge predictions with public and answer key for UI consumption
    merged = pd.merge(state.df_public, state.df_predictions, on="transaction_id")
    if state.df_answer is not None:
        merged = pd.merge(merged, state.df_answer, on="transaction_id")

    # Format records for UI (limit list to latest 500 for high speed DOM rendering)
    records = merged.to_dict(orient="records")

    summary_stats = {
        "total_transactions": len(merged),
        "high_risk_count": int((merged["risk_tier"] == TIER_HIGH).sum()),
        "medium_risk_count": int((merged["risk_tier"] == TIER_MEDIUM).sum()),
        "low_risk_count": int((merged["risk_tier"] == TIER_LOW).sum()),
        "predicted_fraud_count": int((merged["predicted_label"] == 1).sum()),
        "ground_truth_fraud_count": int((merged["ground_truth_label"] != LABEL_NORMAL).sum()) if "ground_truth_label" in merged else 0,
        "rules_fired_count": int((merged["fired_rules"] != "none").sum()),
    }

    # Closed-loop evasion tuner evaluation
    tuner_eval = None
    tuner_rec = None
    if state.df_answer is not None and state.df_predictions is not None:
        try:
            tuner_eval = state.evasion_tuner.evaluate_blue_team(state.df_answer, state.df_predictions)
            stealth_now = state.last_red_config.stealth_level if state.last_red_config else 0.4
            tuner_rec = state.evasion_tuner.suggest_next_iteration(tuner_eval, current_stealth=stealth_now)
        except Exception as e:
            print("Tuner error:", e)

    return {
        "summary": summary_stats,
        "metrics": state.last_eval_report,
        "realism": state.last_realism_report,
        "tuner_eval": tuner_eval,
        "tuner_recommendation": tuner_rec,
        "retrain_history": state.retrain_history,
        "transactions": records[:600],
    }


@app.post("/api/red-team/generate")
def generate_stream(req: GenerateRequest):
    weights = {
        "voice_clone_app": req.voice_clone_weight,
        "ephemeral_merchant": req.ephemeral_merchant_weight,
        "digital_arrest": req.digital_arrest_weight,
    }
    cfg = RedTeamConfig(
        seed=req.seed,
        total_transactions=req.total_transactions,
        fraud_ratio=req.fraud_ratio,
        stealth_level=req.stealth_level,
        threat_weights=weights,
    )
    state.last_red_config = cfg
    
    orch = RedTeamOrchestrator(cfg)
    df_pub, df_ans = orch.generate_batch()
    state.df_public = df_pub
    state.df_answer = df_ans
    state.last_realism_report = compute_statistical_realism(df_pub)

    # Score newly generated batch with current Blue Team pipeline
    if state.pipeline is not None and state.pipeline.is_trained:
        state.df_predictions = state.pipeline.predict(df_pub)
        state.last_eval_report = state.evaluator.evaluate(state.df_predictions, df_ans)

    leakage_check = validate_zero_leakage(df_pub)

    return {
        "status": "SUCCESS",
        "generated_count": len(df_pub),
        "fraud_count": int((df_ans["ground_truth_label"] != LABEL_NORMAL).sum()),
        "stealth_level": req.stealth_level,
        "zero_leakage": leakage_check,
        "realism_report": state.last_realism_report,
        "eval_report": state.last_eval_report,
    }


@app.post("/api/blue-team/train")
def train_pipeline():
    if state.df_public is None or state.df_answer is None:
        raise HTTPException(status_code=400, detail="No dataset available to train on. Generate data first.")

    state.pipeline = BlueTeamPipeline()
    state.pipeline.train(state.df_public, state.df_answer)
    state.df_predictions = state.pipeline.predict(state.df_public)
    state.last_eval_report = state.evaluator.evaluate(state.df_predictions, state.df_answer)

    return {
        "status": "TRAINED",
        "metrics": state.last_eval_report,
    }


@app.post("/api/blue-team/retrain")
def active_retrain(req: RetrainRequest):
    """
    Synthesizes an evasive adversarial batch, evaluates baseline weakness,
    and runs BlueTeamRetrainer to adapt and harden defenses.
    """
    if state.df_public is None or state.df_answer is None:
        initialize_default_system()

    # 1. Generate harder adversarial stream
    harder_cfg = RedTeamConfig(
        seed=int(np.random.randint(100, 99999)),
        total_transactions=req.adversarial_samples,
        fraud_ratio=req.fraud_ratio,
        stealth_level=req.stealth_level,
    )
    orch = RedTeamOrchestrator(harder_cfg)
    df_adv_pub, df_adv_ans = orch.generate_batch()

    # 2. Retrain active retrainer
    cycle_result = state.retrainer.retrain_with_adversarial_batch(
        df_new_public=df_adv_pub,
        df_new_answer=df_adv_ans,
        historical_public=state.df_public,
        historical_answer=state.df_answer,
    )

    # 3. Update active pipeline
    state.pipeline = state.retrainer.pipeline
    state.df_public = pd.concat([state.df_public, df_adv_pub], ignore_index=True)
    state.df_answer = pd.concat([state.df_answer, df_adv_ans], ignore_index=True)
    state.df_predictions = state.pipeline.predict(state.df_public)
    state.last_eval_report = state.evaluator.evaluate(state.df_predictions, state.df_answer)

    cycle_entry = {
        "cycle": len(state.retrain_history) + 1,
        "type": "Adversarial Ingestion & Hardening",
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "samples": len(state.df_public),
        "stealth": req.stealth_level,
        "metrics": state.last_eval_report["summary"],
        "threat_breakdown": state.last_eval_report["threat_breakdown"],
    }
    state.retrain_history.append(cycle_entry)

    return {
        "status": "RETRAINED",
        "cycle": cycle_entry["cycle"],
        "metrics": state.last_eval_report,
        "cycle_entry": cycle_entry,
    }


@app.post("/api/sandbox/simulate")
def simulate_single(req: SingleTransactionRequest):
    """
    Evaluates a single crafted transaction in sub-millisecond real-time,
    returning Rule Engine tripwire telemetry and ML ensemble scoring breakdown.
    """
    row_dict = {
        "transaction_id": "TXN_SIMULATED",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sender_id": "USR_SIM_001",
        "receiver_id": req.receiver_id,
        "amount": req.amount,
        "channel": req.channel,
        "sender_account_age_days": req.sender_account_age_days,
        "receiver_account_age_days": req.receiver_account_age_days,
        "device_type": req.device_type,
        "session_duration_sec": req.session_duration_sec,
        "time_since_payee_added_sec": req.time_since_payee_added_sec,
        "concurrent_call_active": req.concurrent_call_active,
        "ip_country": req.ip_country,
        "ip_change_flag": req.ip_change_flag,
        "login_to_transaction_gap_sec": req.login_to_transaction_gap_sec,
        "velocity_1h": req.velocity_1h,
        "velocity_24h": req.velocity_24h,
        "amount_deviation_score": req.amount_deviation_score,
        "new_payee_flag": req.new_payee_flag,
    }

    # 1. Rule Engine Evaluation
    rule_score, fired_rules, is_critical = state.rule_engine.evaluate_transaction(row_dict)

    # 2. Pipeline ML Evaluation
    if state.pipeline is None or not state.pipeline.is_trained:
        initialize_default_system()

    df_single = pd.DataFrame([row_dict])
    preds = state.pipeline.predict(df_single)
    pred_res = preds.iloc[0].to_dict()

    # Rule definitions dictionary for tooltip explanation
    rule_explanations = {
        rule: state.rule_engine.rule_definitions.get(rule, "Heuristic Trigger")
        for rule in fired_rules
    }

    return {
        "transaction": row_dict,
        "final_fraud_probability": round(float(pred_res["fraud_probability"]), 4),
        "predicted_label": int(pred_res["predicted_label"]),
        "risk_tier": str(pred_res["risk_tier"]),
        "ml_probability": round(float(pred_res["ml_probability"]), 4),
        "rule_score": round(float(rule_score), 4),
        "is_critical_override": bool(is_critical),
        "fired_rules": fired_rules,
        "rule_explanations": rule_explanations,
        "rule_weight": state.pipeline.config.rule_weight,
        "ml_weight": state.pipeline.config.ml_weight,
    }


# ---------------------------------------------------------------------------
# Static Files & SPA Mounting
# ---------------------------------------------------------------------------

FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "Frontend index.html not yet created."})


if __name__ == "__main__":
    import uvicorn
    initialize_default_system()
    uvicorn.run(app, host="127.0.0.1", port=8000)
