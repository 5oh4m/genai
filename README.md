# Adversarial AI Defense Lab: Red Team vs. Blue Team

A complete, production-grade closed-loop adversarial simulation and defense platform for detecting GenAI-enabled financial fraud (Voice-Clone APP Scams, AI Ephemeral Merchants, and Deepfake Digital Arrest Coercion).

---

## Repository Structure

```
genai/
├── red_team/                 # Data Factory & Adversarial Attack Generator
│   ├── __init__.py
│   ├── config.py             # Public vs Answer Key schemas, labels, defaults
│   ├── baseline_generator.py # Realistic consumer cohorts & spending distributions
│   ├── attack_generators/    # Modular GenAI attack vector engines
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract Base Attack Generator
│   │   ├── voice_clone_app.py    # Threat 1: Voice Clone APP Scams
│   │   ├── ephemeral_merchant.py # Threat 2: AI Ephemeral Boutique Stores
│   │   └── digital_arrest.py     # Threat 3: Deepfake Digital Arrest Coercion
│   ├── orchestrator.py       # Stream mixer, velocity engine, & CSV exporter
│   ├── evasion_tuner.py      # Closed-loop mutator (adapts attacks to bypass models)
│   └── metrics.py            # Statistical realism & zero-leakage validator
├── blue_team/                # Detection Engine, Rules, ML & Retraining Loop
│   ├── __init__.py
│   ├── config.py             # Feature sets, thresholds (Low/Med/High), hyperparameters
│   ├── preprocessor.py       # Datetime expansion, categorical encoding, scaling
│   ├── rule_engine.py        # GenAI telemetry tripwires & deterministic rules
│   ├── models/               # Tabular ML & Hybrid Ensemble Classifiers
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract Base Fraud Detector
│   │   ├── ml_detector.py    # Balanced Tabular Classifiers (RF, GBDT, LR)
│   │   └── ensemble.py       # Rule-ML Hybrid Ensemble with Critical Overrides
│   ├── pipeline.py           # End-to-end Training, Inference, Risk Tiers, & Persistence
│   ├── evaluator.py          # Precision, Recall, F1, ROC-AUC, & Threat Breakdown
│   └── retrainer.py          # Active retraining loop triggered by Red Team evasions
├── tests/                    # Comprehensive Test Suites
│   ├── test_red_team.py      # Red Team generator & schema tests
│   └── test_blue_team.py     # Blue Team pipeline, rules, and retrainer tests
├── data/                     # Output Datasets & Predictions
│   ├── blind_transactions.csv# 19 Public Features (Blind stream for Blue Team)
│   ├── oracle_answer_key.csv # 6 Confidential Oracle Ground Truth Columns
│   └── predictions.csv       # Blue Team risk scores, labels, and rule reasons
└── models/                   # Serialized Blue Team Model Artifacts
    └── blue_team/
        └── blue_team_pipeline.joblib
```

---

## 1. Unified Data Contract

### Public Blind Transaction Stream (`data/blind_transactions.csv`)
Features exposed to Blue Team at scoring time (19 columns):
- `transaction_id`, `timestamp`, `sender_id`, `receiver_id`, `amount`, `channel`
- `sender_account_age_days`, `receiver_account_age_days`
- `device_type`, `session_duration_sec`, `time_since_payee_added_sec`, `concurrent_call_active`
- `ip_country`, `ip_change_flag`, `login_to_transaction_gap_sec`
- `velocity_1h`, `velocity_24h`, `amount_deviation_score`, `new_payee_flag`

### Confidential Oracle Answer Key (`data/oracle_answer_key.csv`)
Hidden from Blue Team at scoring time (6 columns):
- `transaction_id`, `ground_truth_label`, `attack_subtype`, `stealth_level`, `evasion_technique`, `evasion_parameters`

---

## 2. Attack Vectors & Evasion Mechanics

1. **Threat 1 — Voice-Cloned "Family Emergency" (Authorized Push Payment)**
   - *Baseline Signal*: Instant transfer to new payee ($< 60\text{s}$), off-hours panic, round urgent amounts ($500).
   - *Evasion*: Delay padding (10–30 mins), historical spending mean matching ($487.35), diurnal curve matching.
2. **Threat 2 — AI-Generated "Pop-Up" Boutique (Ephemeral Merchant)**
   - *Baseline Signal*: Fresh merchant account ($< 3$ days), rapid multi-sender transaction burst.
   - *Evasion*: Dormant pre-aged merchant accounts, multi-day Poisson arrival pacing, varied retail basket amounts.
3. **Threat 3 — Deepfake "Digital Arrest" Coercion**
   - *Baseline Signal*: Excessive session dwell time ($> 1800\text{s}$), `concurrent_call_active = True`, max limit drain.
   - *Evasion*: Micro-tranche fan-out (splitting into 2–4 spaced transfers), call hangup masking (`concurrent_call_active = False`), app restart session masking.

---

## 3. Quick Start & Execution

### 1. Run Complete Test Suite
```bash
.venv/bin/python3 -m unittest discover tests/
```

### 2. Generate Red Team Adversarial Stream
```bash
.venv/bin/python3 -m red_team.orchestrator --total-txns 10000 --fraud-ratio 0.05 --stealth 0.4 --output-dir data/
```

### 3. Train Blue Team Defense Pipeline & Score Transactions
```bash
.venv/bin/python3 -m blue_team.pipeline --train-data data/blind_transactions.csv --answer-key data/oracle_answer_key.csv --save-dir models/blue_team --output-preds data/predictions.csv
```

### 4. Closed-Loop Evasion Adaptation
```python
from red_team.evasion_tuner import EvasionTuner
import pandas as pd

df_preds = pd.read_csv("data/predictions.csv")
df_ans = pd.read_csv("data/oracle_answer_key.csv")

tuner = EvasionTuner()
eval_result = tuner.evaluate_blue_team(df_ans, df_preds)
rec = tuner.suggest_next_iteration(eval_result, current_stealth=0.4)
print(rec)
```
