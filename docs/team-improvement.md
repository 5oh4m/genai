# AEGIS-AI Red Team & Blue Team Improvement Plan

> **Purpose:** This document is the master blueprint for evolving AEGIS-AI from an educational simulation into a credible, real-world-aligned adversarial fraud defense platform — modeled after how payment networks (Mastercard, Visa), card issuers (Chase, HSBC), and fraud platforms (Stripe Radar, FICO Falcon) actually operate. Each section explains *what exists today*, *what real systems do*, *what to build*, and *how to implement it*.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Real-World Payment Fraud Landscape](#2-real-world-payment-fraud-landscape)
3. [Current System Architecture Recap](#3-current-system-architecture-recap)
4. [Red Team Improvements](#4-red-team-improvements)
5. [Blue Team Improvements](#5-blue-team-improvements)
6. [Shared Data Model Evolution](#6-shared-data-model-evolution)
7. [Closed-Loop Adversarial Cycle Enhancements](#7-closed-loop-adversarial-cycle-enhancements)
8. [API & Backend Improvements](#8-api--backend-improvements)
9. [Evaluation & Metrics Framework](#9-evaluation--metrics-framework)
10. [Real-World Case Study Mappings](#10-real-world-case-study-mappings)
11. [Implementation Roadmap](#11-implementation-roadmap)
12. [Testing Strategy](#12-testing-strategy)
13. [Glossary of Real-World Terms](#13-glossary-of-real-world-terms)

---

## 1. Executive Summary

### What AEGIS-AI does today

AEGIS-AI simulates a **closed-loop adversarial fraud lab**:

```
Red Team generates synthetic transactions (normal + 3 attack types)
        ↓
Blue Team scores them (6 rules + Random Forest ML + hybrid ensemble)
        ↓
Evaluator measures detection / evasion rates
        ↓
Evasion Tuner recommends harder stealth for next iteration
        ↓
Blue Team retrains on adversarial samples
        ↓
(repeat)
```

### What real payment networks do

Mastercard's **Decision Intelligence (DI)**, Visa's **Advanced Authorization (VAA)**, and issuer systems like **FICO Falcon** operate on:

- **Billions of authorizations per day** with sub-100ms scoring
- **Multi-layered decisioning**: rules → ML → graph analytics → consortium data
- **Authorization vs settlement** lifecycle (auth hold → clearing → settlement)
- **Consortium intelligence** (shared fraud signals across banks)
- **Delayed labels** (chargebacks arrive 30–120 days later)
- **Regulatory frameworks** (PCI-DSS, PSD2 SCA, Reg E)

### The gap we need to close

AEGIS-AI captures the **adversarial dynamic** correctly but lacks the **domain richness** of real payment fraud. This plan closes that gap incrementally while keeping the simulation playable and educational.

### Improvement priorities

| Priority | Area | Impact |
|----------|------|--------|
| 🔴 P0 | Payment rail realism (auth flow, MCC, 3DS) | Makes simulation feel like real money movement |
| 🔴 P0 | Graph/network fraud (mule rings, shared devices) | Biggest gap vs production systems |
| 🔴 P0 | Per-threat narrative + real-world case studies | Makes project informational and presentable |
| 🟠 P1 | New attack types (ATO, card testing, friendly fraud) | Expands red team coverage |
| 🟠 P1 | Rule engine expansion (velocity dimensions, geo rules) | Matches production rule libraries |
| 🟠 P1 | Model ops (drift detection, champion/challenger) | Blue team maturity |
| 🟡 P2 | Consortium data simulation | Cross-bank intelligence |
| 🟡 P2 | Chargeback lifecycle + delayed labels | Realistic label quality |
| 🟢 P3 | ISO 8583 message parsing | Deep network protocol realism |

---

## 2. Real-World Payment Fraud Landscape

### 2.1 How a real card transaction flows

```
Cardholder taps "Pay $150"
        ↓
Merchant POS / E-commerce gateway
        ↓
Acquirer (merchant's bank) — adds MCC, terminal ID
        ↓
Card Network (Mastercard / Visa switch) — routes by BIN
        ↓
Issuer (cardholder's bank) — FRAUD SCORING HAPPENS HERE
        ↓
Decision: APPROVE | STEP-UP (3DS/OTP) | DECLINE | REVIEW
        ↓
Authorization hold placed (funds reserved, not moved)
        ↓
[1-3 days later] Clearing & Settlement — money actually moves
        ↓
[30-120 days later] Chargeback if fraud confirmed
```

**AEGIS-AI today:** Skips authorization/settlement split. Scores a flat transaction record instantly. **Improvement:** Add `transaction_stage` field and model the auth → settle → chargeback lifecycle.

---

### 2.2 Mastercard Decision Intelligence (DI) — What to emulate

Mastercard DI is a **network-level fraud scoring service** that issuers subscribe to. Key capabilities:

| DI Feature | Description | AEGIS-AI Equivalent to Build |
|------------|-------------|------------------------------|
| **Behavioral profiling** | Per-cardholder spending patterns over time | ✅ Partially exists (amount deviation, velocity) — extend with merchant category profiles |
| **Merchant risk scoring** | MCC-based risk, acquirer reputation | ❌ Missing — add MCC + merchant risk tier |
| **Cross-border intelligence** | BIN country vs IP country vs merchant country mismatch | ⚠️ Partial (`ip_country` only) — add BIN country + merchant country |
| **Device intelligence** | Device fingerprint, new device flag | ⚠️ Partial (`device_type` only) — add device fingerprint hash + trust score |
| **Link analysis** | Shared beneficiaries, mule networks | ❌ Missing — build entity graph (Section 4.5) |
| **Adaptive models** | Models retrained on network-wide fraud trends | ✅ Retrain cycle exists — add drift detection |
| **Real-time scoring** | Sub-100ms at authorization | N/A for simulation — but add latency metric display |

---

### 2.3 Visa Advanced Authorization (VAA) — What to emulate

| VAA Feature | AEGIS-AI Gap | Improvement |
|-------------|-------------|-------------|
| **Risk-based authentication (3DS)** | No step-up flow | Add `authentication_method` field: none / OTP / 3DS / biometric |
| **Transaction risk score (1-999)** | Uses 0-1 probability | Map to 1-999 scale in UI for realism |
| **Merchant category controls** | No MCC | Add MCC codes with risk weights |
| **Geographic velocity** | Single `ip_country` | Track country changes per session |
| **Account Takeover (ATO) detection** | Not modeled | New attack type (Section 4.3) |

---

### 2.4 Issuer-side systems (FICO Falcon, SAS Fraud Management)

Production issuer fraud systems typically have:

1. **Real-time authorization scoring** (< 100ms) — rules + ML
2. **Post-authorization monitoring** — batch review of approved txns
3. **Case management** — analyst workflow for HIGH risk
4. **Customer notification** — SMS/email for suspicious activity
5. **Account action** — freeze, limit, callback
6. **Feedback loop** — analyst confirms/denies → retrains model

**AEGIS-AI mapping:**
- Real-time scoring = Sandbox + Stream table ✅
- Post-auth monitoring = Stream filter "Evaded" ⚠️
- Case management = Transaction Inspector ✅
- Customer notification = ❌ Missing
- Account action = ❌ Missing (add `recommended_action` field)
- Feedback loop = ❌ Missing (add analyst override in UI)

---

## 3. Current System Architecture Recap

### 3.1 Red Team (today)

| Component | File | Role |
|-----------|------|------|
| Orchestrator | `red_team/orchestrator.py` | Generates baseline + attacks, computes velocity/deviation |
| Baseline Generator | `red_team/baseline_generator.py` | Normal user/merchant population |
| Voice Clone Attack | `red_team/attack_generators/voice_clone_app.py` | APP fraud via voice clone coercion |
| Ephemeral Merchant | `red_team/attack_generators/ephemeral_merchant.py` | Fake boutique bust-out |
| Digital Arrest | `red_team/attack_generators/digital_arrest.py` | Law enforcement impersonation coercion |
| Evasion Tuner | `red_team/evasion_tuner.py` | Closed-loop stealth/weight recommendations |
| Metrics | `red_team/metrics.py` | Zero-leakage validation, statistical realism |

**Public features (19 columns):** transaction_id, timestamp, sender_id, receiver_id, amount, channel, account ages, device_type, session_duration_sec, time_since_payee_added_sec, concurrent_call_active, ip_country, ip_change_flag, login_to_transaction_gap_sec, velocity_1h, velocity_24h, amount_deviation_score, new_payee_flag

**Oracle answer key (6 columns):** ground_truth_label, attack_subtype, stealth_level, evasion_technique, evasion_parameters

### 3.2 Blue Team (today)

| Component | File | Role |
|-----------|------|------|
| Pipeline | `blue_team/pipeline.py` | End-to-end train + predict |
| Rule Engine | `blue_team/rule_engine.py` | 6 heuristic tripwires |
| ML Detector | `blue_team/models/ml_detector.py` | Random Forest / GBM / LogReg |
| Ensemble | `blue_team/models/ensemble.py` | 70% ML + 30% rules, hard override |
| Preprocessor | `blue_team/preprocessor.py` | Scale numerics, one-hot categoricals |
| Retrainer | `blue_team/retrainer.py` | Initial + adversarial retrain |
| Evaluator | `blue_team/evaluator.py` | Precision, recall, AUC, per-threat breakdown |

**6 Rules today:**
1. `RULE_INSTANT_TRANSFER_NEW_PAYEE` — new payee + ≤60s + fresh receiver
2. `RULE_HOSTAGE_CALL_COERCION` — active call + high amount/session/deviation
3. `RULE_PROLONGED_SESSION_DWELL` — session ≥1800s + high amount
4. `RULE_FRESH_MERCHANT_BURST` — merchant ≤4 days + amount ≥$25
5. `RULE_EXTREME_AMOUNT_DEVIATION` — z-score ≥3.5 + new payee
6. `RULE_VELOCITY_SURGE` — ≥2 txns in 1h + new payee

---

## 4. Red Team Improvements

### 4.1 Payment Rail Realism

#### 4.1.1 Add transaction lifecycle stages

**New field:** `transaction_stage`

| Stage | Description | Real-world parallel |
|-------|-------------|-------------------|
| `authorization` | Real-time scoring decision | Mastercard auth request |
| `clearing` | Batch processing post-auth | Network clearing file |
| `settlement` | Funds movement | Interbank settlement |
| `chargeback` | Dispute filed (fraud confirmed) | Reg E / chargeback reason code |

**Implementation:**
- Add to `PUBLIC_COLUMNS` in `red_team/config.py`
- Baseline generator sets `authorization` for all new txns
- Background job (or batch endpoint) advances 95% to `settlement` after simulated delay
- Fraud txns have 15% chargeback rate within 30-120 simulated days

**Why it matters:** Real fraud detection happens primarily at **authorization**. Post-settlement detection (chargeback) is how labels arrive in production — often too late.

---

#### 4.1.2 Add Merchant Category Code (MCC)

**New fields:**
```
merchant_category_code: str    # e.g., "5411" (Grocery), "5732" (Electronics)
merchant_name: str             # e.g., "Whole Foods Market"
merchant_country: str          # ISO country code
merchant_risk_tier: str        # LOW / MEDIUM / HIGH (computed)
```

**MCC risk mapping (add to `red_team/config.py`):**

| MCC | Category | Risk Tier | Notes |
|-----|----------|-----------|-------|
| 5411 | Grocery Stores | LOW | High trust, low fraud |
| 5812 | Restaurants | LOW | Normal spending |
| 5732 | Electronics | MEDIUM | Higher ticket, some fraud |
| 5967 | Direct Marketing | HIGH | Common fraud vector |
| 6012 | Financial Institutions | HIGH | Money movement |
| 7995 | Gambling | HIGH | Restricted category |
| 7273 | Dating/Escort | HIGH | Romance scam vector |
| 9999 | Unknown/Ephemeral | CRITICAL | Red flag for fake merchants |

**Baseline generator change:** Assign MCC from merchant profile. Established merchants get LOW-MEDIUM MCCs. Ephemeral merchant attacks get MCC 9999 or 5967.

**Real-world parallel:** Mastercard maintains MCC-based risk controls. Issuers block or step-up high-risk MCCs for certain cardholder segments.

---

#### 4.1.3 Add authorization message fields

Model the key fields from an ISO 8583 authorization request (simplified):

```
card_bin: str                  # First 6 digits — identifies issuer + card type
card_present: bool             # CP vs CNP (card-not-present)
entry_mode: str                # chip, contactless, magstripe, ecom, mcommerce
authentication_method: str     # none, otp, 3ds_v2, biometric
authentication_result: str   # success, failed, not_attempted, bypass
response_code: str             # 00=approved, 05=declined, 65=step_up
```

**Red Team behavior:**
- Normal txns: 80% card-present chip/contactless, 20% CNP with 3DS
- Voice clone APP: CNP, no 3DS (victim rushed), `authentication_method: none`
- Ephemeral merchant: CNP, ecom entry, MCC 9999
- Digital arrest: CNP, long session, no 3DS

**Blue Team new rules (see Section 5.2):**
- `RULE_CNP_NO_3DS_HIGH_AMOUNT` — card-not-present + no 3DS + amount > $200
- `RULE_HIGH_RISK_MCC` — MCC in {5967, 7995, 9999} + new payee

---

#### 4.1.4 Channel-specific behavior profiles

**Current channels:** UPI, Card, Wire, P2P

**Improvement — add sub-channel and network:**

| Channel | Sub-channel | Network | Typical Amount Range | Fraud Pattern |
|---------|-------------|---------|---------------------|---------------|
| Card | Credit | Visa | $5 – $5,000 | CNP fraud, card testing |
| Card | Debit | Mastercard | $5 – $2,000 | APP fraud, ATM fraud |
| UPI | P2P | NPCI (India) | ₹100 – ₹100,000 | UPI mule accounts |
| Wire | Domestic | Fedwire/SWIFT | $1,000 – $500,000 | Business email compromise |
| Wire | International | SWIFT | $500 – $1M | Trade-based laundering |
| P2P | Wallet | Venmo/Zelle | $1 – $5,000 | ATO, scam payments |

**Implementation:** Extend `CHANNELS` in config to structured objects with metadata. Baseline generator picks channel based on user profile (geography, age).

---

### 4.2 Attack Type Enhancements (Existing 3)

#### 4.2.1 Voice Clone APP — Enhancements

**Real-world context:**
In 2024-2026, AI voice cloning scams surged globally. FBI IC3 reported APP (Authorized Push Payment) fraud losses exceeding $10B annually in the US alone. Victims receive a call sounding exactly like a family member ("Grandma, I'm in jail, wire money now") or bank representative, then authorize transfers themselves — bypassing traditional fraud filters because the victim is the authorized party.

**Current simulation:** `concurrent_call_active` flag + new payee + amount deviation.

**Enhancements to implement:**

| Enhancement | Field/Logic | Stealth Interaction |
|-------------|-------------|-------------------|
| **Call duration before transfer** | `call_duration_before_transfer_sec` | High stealth: 15-45 min (victim thinks it through). Low stealth: 2-5 min (panic) |
| **Multiple small transfers** | Generate 2-4 txns instead of 1 | High stealth: stay under $500 each |
| **Victim device change** | `device_change_mid_session: bool` | Low stealth: same device. High stealth: victim switches to banking app on phone after call on landline |
| **Payee name similarity** | `payee_name_match_score: float` | High stealth: payee named similar to known contact ("J0hn Smith" vs "John Smith") |
| **Time-of-day realism** | Already diurnal — extend: low stealth favors 22:00-04:00 | High stealth: victim's normal hours |
| **Social engineering script tag** | `coercion_script: str` | Values: family_emergency, bank_fraud_alert, tax_authority, romance |

**New evasion techniques to add:**
- `CALL_HANGUP_BEFORE_AUTH` — ends call before app authorization (already partially exists)
- `MIMIC_SPENDING_PATTERN` — amounts drawn from victim's historical distribution
- `DELAYED_PAYEE_ADD` — adds payee hours/days before transfer (already partially exists)
- `MULTI_TRanche_DRAIN` — splits into sub-threshold amounts (borrow from digital arrest)

**Real-world parallel:** UK banks implemented **Confirmation of Payee (CoP)** — checks if account name matches. Add `payee_name_verified: bool` field; voice clone attacks set this to `False`.

---

#### 4.2.2 Ephemeral Merchant — Enhancements

**Real-world context:**
AI-generated e-commerce stores (using tools like Shopify + AI product descriptions/images) appear overnight, run promotional ads on social media, collect payments from hundreds of victims over 24-72 hours, then disappear. Mastercard's Merchant Risk Analytics monitors new merchant boarding velocity.

**Current simulation:** Fresh merchant IDs (`MER_EPH_*`), burst transactions, fixed promo pricing.

**Enhancements:**

| Enhancement | Description |
|-------------|-------------|
| **AI-generated catalog signal** | `product_catalog_size: int` — fake merchants have 3-15 products (real stores have 100+) |
| **Social media ad source** | `traffic_source: str` — values: organic, social_ad, email, direct. Attacks use social_ad |
| **Refund rate anomaly** | `merchant_refund_rate: float` — fake merchants: 0% (they don't refund). Real: 2-8% |
| **Domain age** | `merchant_domain_age_days: int` — ephemeral: 0-3 days. Established: 365+ |
| **Cross-victim pattern** | Multiple senders → same receiver within burst window (already grouped by MER_EPH ID) |
| **Payment processor hopping** | Same merchant entity reappears with new ID after takedown (simulate in multi-cycle generation) |

**New evasion techniques:**
- `DORMANT_MERCHANT_PROFILE` — merchant appears 30-90 days old but inactive (already in high stealth)
- `VARIABLE_PRICING` — amounts vary to avoid fixed-amount rules
- `SLOW_BURN_CAMPAIGN` — extend burst from 24h to 7 days

**Real-world parallel:** Mastercard's **Global Merchant Audit Program** flags merchants with high chargeback rates within 90 days of boarding. Simulate by adding chargeback events 30-60 days post-attack.

---

#### 4.2.3 Digital Arrest — Enhancements

**Real-world context:**
"Digital arrest" scams target diaspora communities (especially Indian, Chinese, Korean populations in US/UK/Canada). Scammers impersonate police, embassy officials, or tax authorities via video call, convince victims they are under investigation, and coerce them to transfer "bail" or "safe account" funds. Interpol and FBI issued joint advisories in 2024-2025.

**Current simulation:** Large single drain or micro-tranches, prolonged session, concurrent call.

**Enhancements:**

| Enhancement | Description |
|-------------|-------------|
| **Video call flag** | `video_call_active: bool` — distinct from voice-only; higher coercion signal |
| **Remote access indicator** | `remote_access_app_detected: bool` — AnyDesk/TeamViewer running (scammers often install these) |
| **Isolation pattern** | `session_isolation_hours: float` — victim logged in for 4-12 hours without break (coerced continuous session) |
| **Official impersonation type** | `impersonation_entity: str` — police, embassy, tax_authority, bank_security |
| **Geographic targeting** | Target users with `ip_country != DEFAULT_HOME_COUNTRY` (diaspora profile) |
| **Safe account narrative** | Receiver named like government entity: `GOV_SAFE_*`, `POLICE_HOLD_*` |

**New evasion techniques:**
- `MICRO_TRANCHE_BELOW_THRESHOLD` — 3-4 transfers under $3,000 (already exists)
- `SESSION_RESTART_MASKING` — short session duration but multiple login events (add `login_count_in_session`)
- `CROSS_BORDER_WIRE` — use Wire channel with international corridor (higher real-world loss)

**Real-world parallel:** Singapore Police Force's **Anti-Scam Command** uses transaction delay + callback for transfers > SGD 5,000 to new payees. Model as `recommended_cooldown_minutes` in blue team output.

---

### 4.3 New Attack Types to Add

#### Attack 4: Account Takeover (ATO)

**Scenario:** Attacker obtains credentials (phishing, credential stuffing, SIM swap) and accesses victim's existing account to transfer to mule accounts.

**Why add this:** ATO is the #1 fraud type by volume at most issuers. Different from APP because the attacker, not the victim, initiates the transfer.

**Fields to simulate:**

| Signal | Normal | ATO Attack |
|--------|--------|------------|
| `login_to_transaction_gap_sec` | 60-600s | 5-30s (automated) |
| `ip_change_flag` | 1.5% rate | 95% (attacker IP) |
| `device_type` | Consistent | New device (90%) |
| `ip_country` | Home country | Different country (70%) |
| `session_duration_sec` | 60-300s | 30-120s (efficient extraction) |
| `new_payee_flag` | 15% | 100% (mule account) |
| `failed_login_attempts_24h` | 0-1 | 3-8 (before success) |

**Label:** `ground_truth_label=4`, subtype `account_takeover_credential_theft`

**Stealth levels:**
- Low: All signals fire (new device + new IP + instant transfer)
- High: Attacker uses residential proxy in victim's country, emulates victim device fingerprint

**Real-world parallel:** Mastercard Identity Check (3DS 2.0) uses device + behavioral biometrics to detect ATO. Visa's **Compromised Account Management System (CAMS)** alerts issuers to breached cards.

**File to create:** `red_team/attack_generators/account_takeover.py`

---

#### Attack 5: Card Testing / BIN Attacks

**Scenario:** Fraudster validates stolen card numbers with small transactions before maxing them out.

**Pattern:**
- 5-50 transactions in rapid succession
- Amounts: $0.01 – $5.00 (or $1.00 exactly)
- Same sender (attacker-controlled) → different receivers (merchants)
- High velocity_1h (10-50)
- CNP, no 3DS
- Multiple card BINs from same IP

**Label:** `ground_truth_label=5`, subtype `card_testing_bin_attack`

**Real-world parallel:** Visa's **Account Attack Intelligence** detects card testing within minutes and blocks the entire BIN range. Merchants see this as dozens of $1.00 auth attempts.

**File to create:** `red_team/attack_generators/card_testing.py`

---

#### Attack 6: Friendly Fraud (First-Party Fraud)

**Scenario:** Cardholder makes a legitimate purchase, receives goods, then files a chargeback claiming "unauthorized transaction."

**Why it matters:** Friendly fraud is the fastest-growing fraud category. It's extremely hard to detect at authorization because the cardholder IS the legitimate user.

**Simulation approach:**
- Transaction looks 100% normal at authorization time
- Label in oracle: `ground_truth_label=6`, subtype `friendly_fraud_chargeback`
- Add delayed `chargeback_filed: bool` and `chargeback_reason_code: str` (4853 = "Cardholder Disputes")
- Blue team CANNOT detect at auth time — only post-settlement via chargeback pattern analysis

**Real-world parallel:** Mastercard Ethoca and Visa Verifi provide merchant-issuer collaboration to resolve disputes before chargeback. Teaches that **not all fraud is detectable in real-time**.

**File to create:** `red_team/attack_generators/friendly_fraud.py`

---

#### Attack 7: Money Mule Network

**Scenario:** Layered transfers through 3-5 mule accounts to obscure fund origin (common in APP fraud and cybercrime proceeds).

**Pattern:**
- Chain: Victim → Mule Layer 1 → Mule Layer 2 → Cash-out (ATM/crypto)
- Each hop within 1-4 hours
- Mule accounts: 0-14 days old, few prior transactions
- Graph structure: tree or chain

**Label:** `ground_truth_label=7`, subtype `money_mule_layering`

**Requires:** Entity graph (Section 4.5)

**Real-world parallel:** Europol's EMMA (European Money Mule Action) operations. Banks monitor outbound payments to accounts that immediately forward funds.

**File to create:** `red_team/attack_generators/money_mule.py`

---

### 4.4 Baseline Generator Improvements

#### 4.4.1 Richer user profiles

**Add to `UserProfile` dataclass:**

```python
@dataclass
class UserProfile:
    # existing fields...
    home_country: str
    preferred_channels: List[str]
    spending_personality: str       # "conservative", "moderate", "high_spender"
    merchant_affinity: Dict[str, float]  # MCC → visit frequency
    typical_session_duration: float
    device_fingerprint: str
    has_biometric_auth: bool
    credit_limit: float
    account_status: str             # "active", "new", "dormant_reactivated"
    diaspora_flag: bool             # living abroad vs home country
    age_group: str                  # "18-25", "26-40", "41-60", "60+"
```

#### 4.4.2 Merchant profiles with lifecycle

```python
@dataclass
class MerchantProfile:
    # existing fields...
    mcc: str
    country: str
    domain_age_days: int
    boarding_date: str
    chargeback_rate: float
    avg_ticket_size: float
    product_catalog_size: int
    status: str                     # "active", "dormant", "suspended", "terminated"
    acquirer_id: str
```

#### 4.4.3 Temporal patterns

- **Weekly seasonality:** Higher spending Fri-Sun
- **Monthly seasonality:** Salary day spike (1st and 15th)
- **Holiday patterns:** Elevated e-commerce in Nov-Dec
- **Geographic time zones:** Transaction hours match user's country

---

### 4.5 Entity Graph & Network Fraud (Critical Addition)

**This is the single biggest gap vs production systems.**

Real fraud detection relies heavily on **link analysis** — connecting entities through shared attributes:

```
User A ──same device──→ User B ──same receiver──→ Mule Account
   │                                              │
   └──same IP────────→ User C ──same receiver──────┘
```

**Implementation plan:**

#### 4.5.1 Graph data structure

```python
# red_team/graph/entity_graph.py

class EntityGraph:
    def __init__(self):
        self.nodes = {}   # entity_id → {type, attributes}
        self.edges = []   # {source, target, relationship, weight}

    def add_transaction(self, txn):
        # Create/update nodes for sender, receiver, device, IP
        # Create edges: SENT_TO, USED_DEVICE, FROM_IP, etc.

    def detect_clusters(self) -> List[dict]:
        # Connected components analysis
        # Return suspicious clusters (shared receiver, shared device)

    def compute_graph_features(self, entity_id) -> dict:
        return {
            "cluster_size": int,           # nodes in connected component
            "shared_receiver_count": int,  # other senders to same receiver
            "device_reuse_count": int,     # other users on same device
            "ip_reuse_count": int,         # other users from same IP
            "mule_likelihood_score": float # composite graph risk score
        }
```

#### 4.5.2 Graph features for Blue Team

Add to public columns:
```
shared_device_user_count: int
shared_ip_user_count: int
receiver_unique_sender_count_24h: int
graph_cluster_size: int
mule_likelihood_score: float
```

**Real-world parallel:** Mastercard's **Session Intelligence** and Visa's **VisaNet + Visa Advanced Authorization** use network graph analytics. FICO Falcon NG includes link analysis modules.

---

### 4.6 Evasion Tuner Improvements

**Current:** Recommends stealth level and threat weights based on recall.

**Enhancements:**

| Enhancement | Description |
|-------------|-------------|
| **Per-rule evasion analysis** | "RULE_HOSTAGE_CALL evaded 67% — recommend CALL_HANGUP technique" |
| **Feature importance feedback** | "Blue Team relies heavily on `concurrent_call_active` — mask this signal" |
| **Multi-objective optimization** | Balance evasion rate vs realism score (don't make attacks so stealthy they're unrealistic) |
| **Attack narrative generation** | LLM-generated explanation of why attacks evaded (for UI display) |
| **Adaptive threat rotation** | Automatically shift weights toward least-detected attack type |
| **Evasion budget** | Cap stealth at realism threshold (log-normal fit must still pass) |

**New output fields for API:**
```json
{
  "recommended_stealth": 0.75,
  "adaptation_strategy": "ESCALATE_TIMING",
  "reasoning": "...",
  "per_rule_evasion": {
    "RULE_HOSTAGE_CALL_COERCION": 0.67,
    "RULE_INSTANT_TRANSFER_NEW_PAYEE": 0.23
  },
  "recommended_techniques": ["CALL_HANGUP_BEFORE_AUTH", "MIMIC_SPENDING_PATTERN"],
  "realism_score": 0.91,
  "evasion_budget_remaining": 0.15
}
```

---

### 4.7 Statistical Realism Improvements

**Current checks:** Amount skew/kurtosis, night-hours ratio, channel distribution, log-normal fit.

**Add:**

| Check | Threshold | Real-world basis |
|-------|-----------|-----------------|
| **Benford's Law on amounts** | First-digit distribution p-value > 0.05 | Forensic accounting standard |
| **Inter-arrival time distribution** | Exponential fit for txn spacing | Queueing theory / Hawkes processes |
| **Amount Gini coefficient** | 0.45-0.65 for population | Real spending inequality |
| **Merchant concentration** | Top 10 merchants < 40% of volume | Pareto principle |
| **Cross-border ratio** | 2-8% of transactions | Typical issuer portfolio |
| **3DS adoption rate** | 60-80% for CNP | PSD2 compliance baseline |
| **Chargeback rate** | 0.1-0.5% overall | Network average |

---

## 5. Blue Team Improvements

### 5.1 Rule Engine Expansion

**Current:** 6 rules. Production systems have **500-5,000+** rules. We won't build thousands, but expanding to **20-25 high-value rules** dramatically improves realism.

#### 5.1.1 New rules to add (prioritized)

| Rule ID | Trigger | Score | Critical | Real-world basis |
|---------|---------|-------|----------|-----------------|
| `RULE_CNP_NO_3DS_HIGH_AMOUNT` | CNP + no 3DS + amount > $200 | 0.82 | No | PSD2 SCA exemption abuse |
| `RULE_HIGH_RISK_MCC` | MCC in {5967, 7995, 9999} + new payee | 0.78 | No | Mastercard MCC controls |
| `RULE_ATO_DEVICE_IP_MISMATCH` | New device + IP country ≠ home + instant transfer | 0.90 | Yes | Visa ATO detection |
| `RULE_CARD_TESTING_VELOCITY` | ≥5 txns in 10 min + amount < $5 | 0.92 | Yes | Card testing detection |
| `RULE_MULE_ACCOUNT_AGE` | Receiver ≤14 days + amount > $500 + new payee | 0.85 | Yes | Mule account typology |
| `RULE_CROSS_BORDER_NEW_PAYEE` | ip_country ≠ home + new payee + amount > $300 | 0.75 | No | Cross-border APP fraud |
| `RULE_DORMANT_ACCOUNT_REACTIVATION` | Account inactive >90 days + high amount | 0.70 | No | Sleeper account fraud |
| `RULE_GEOGRAPHIC_IMPOSSIBILITY` | Two txns from different countries within 30 min | 0.95 | Yes | Impossible travel |
| `RULE_ROUND_AMOUNT_NEW_PAYEE` | Amount is round ($500, $1000) + new payee | 0.65 | No | Scam payment pattern |
| `RULE_GRAPH_MULE_CLUSTER` | mule_likelihood_score > 0.7 | 0.88 | Yes | Network graph analytics |
| `RULE_REMOTE_ACCESS_DETECTED` | remote_access_app_detected + high amount | 0.93 | Yes | Digital arrest / tech support |
| `RULE_VIDEO_CALL_COERCION` | video_call_active + new payee + high amount | 0.91 | Yes | Digital arrest v2 |
| `RULE_MERCHANT_DOMAIN_AGE` | merchant_domain_age ≤ 3 days + CNP | 0.80 | No | Ephemeral merchant |
| `RULE_SALARY_DAY_ANOMALY` | Amount > 3× daily average on non-salary day | 0.60 | No | Behavioral profiling |
| `RULE_WEEKEND_WIRE` | Wire transfer on weekend + amount > $5000 | 0.72 | No | BEC pattern |

**Implementation file:** `blue_team/rule_engine.py` — add each rule as a method following existing pattern.

**Rule priority system:** Add rule tiers:
- **Tier 1 (Block):** Score ≥ 0.90 or critical override → decline
- **Tier 2 (Step-up):** Score 0.70-0.89 → require 3DS/OTP
- **Tier 3 (Review):** Score 0.30-0.69 → queue for analyst
- **Tier 4 (Approve):** Score < 0.30 → auto-approve

---

#### 5.1.2 Velocity rules (multi-dimensional)

Production systems track velocity across many dimensions simultaneously:

| Dimension | Window | Threshold Example |
|-----------|--------|-------------------|
| Per card | 1 hour | ≤ 5 transactions |
| Per card | 24 hours | ≤ 20 transactions |
| Per card | 7 days | ≤ 100 transactions |
| Per card amount | 24 hours | ≤ $5,000 cumulative |
| Per merchant | 1 hour | ≤ 50 transactions (merchant compromise) |
| Per IP | 1 hour | ≤ 10 different cards |
| Per device | 24 hours | ≤ 3 different cards |
| Per receiver | 24 hours | ≤ 5 different senders (mule detection) |
| Per country | 1 hour | ≤ 3 country changes |

**Implementation:** Create `blue_team/velocity_engine.py` that maintains rolling windows and exposes velocity features to both rules and ML.

---

#### 5.1.3 Geographic rules

```python
GEO_RULES = {
    "HIGH_RISK_CORRIDORS": [
        ("US", "NG"),  # US → Nigeria (known mule corridor)
        ("GB", "PK"),  # UK → Pakistan
        ("SG", "CN"),  # Singapore → China (digital arrest target)
    ],
    "SANCTIONED_COUNTRIES": ["KP", "IR", "SY", "CU"],
    "TAX_HAVENS": ["VG", "KY", "PA", "SC"],
}
```

**Real-world parallel:** SWIFT sanctions screening, OFAC compliance checks on wire transfers.

---

### 5.2 ML Model Improvements

#### 5.2.1 Feature engineering expansion

**Current:** 19 raw features → 11 numerical + 3 categorical + 5 boolean (after preprocessing).

**Add derived features:**

| Feature | Formula | Captures |
|---------|---------|----------|
| `amount_to_limit_ratio` | amount / credit_limit | Spending relative to capacity |
| `is_round_amount` | amount % 100 == 0 | Scam pattern |
| `session_to_transfer_ratio` | session_duration / time_since_payee_added | Coercion speed |
| `night_weekend_combo` | is_night_hour AND is_weekend | Vulnerability window |
| `device_ip_mismatch` | device_country ≠ ip_country | ATO signal |
| `payee_age_to_amount_ratio` | amount / receiver_account_age_days | Mule signal |
| `channel_amount_zscore` | z-score within channel | Channel-specific anomaly |
| `graph_risk_composite` | weighted sum of graph features | Network fraud |

**File:** `blue_team/preprocessor.py` — add `engineer_features()` method.

---

#### 5.2.2 Model architecture options

**Current:** Random Forest (default), Gradient Boosting, Logistic Regression.

**Add:**

| Model | Use Case | Real-world parallel |
|-------|----------|-------------------|
| **XGBoost / LightGBM** | Primary tabular model (better than RF on imbalanced data) | Industry standard at most issuers |
| **Isolation Forest** | Unsupervised anomaly detection for zero-day attacks | Catches unknown fraud patterns |
| **Graph Neural Network (GNN)** | Entity graph scoring | Mastercard Session Intelligence |
| **LSTM / Temporal model** | Sequence of user transactions over time | Behavioral biometrics |
| **Stacked ensemble** | Meta-learner combining RF + XGB + rules | FICO Falcon multi-model approach |

**Phased approach:**
- Phase 1: Add XGBoost as default (drop-in replacement in `ml_detector.py`)
- Phase 2: Add Isolation Forest for anomaly score as additional feature
- Phase 3: Graph features → XGBoost (before full GNN)

---

#### 5.2.3 Class imbalance handling

**Current:** `class_weight="balanced"` in Random Forest.

**Improvements:**
- **SMOTE** or **ADASYN** oversampling during training
- **Focal loss** if switching to neural models
- **Threshold optimization** on precision-recall curve (not fixed 0.50)
- **Cost-sensitive learning** — false negative cost >> false positive cost (real-world: missing fraud costs 10-100× more than blocking legitimate)

```python
# blue_team/config.py
@dataclass
class BlueTeamConfig:
    fn_cost: float = 100.0   # Cost of missing fraud ($)
    fp_cost: float = 5.0     # Cost of blocking legitimate ($)
    optimize_threshold: bool = True  # Find optimal threshold on PR curve
```

---

### 5.3 Decision Engine Improvements

#### 5.3.1 Multi-stage decision pipeline

Replace single-score decision with staged pipeline (like production):

```
Stage 1: Hard rules (block immediately)     → 5% of txns
Stage 2: ML ensemble score                   → all remaining
Stage 3: Graph analytics boost               → adjust score ±0.15
Stage 4: Velocity checks (post-score)        → override if velocity exceeded
Stage 5: Risk tier assignment                → LOW / MEDIUM / HIGH
Stage 6: Recommended action                  → APPROVE / STEP_UP / DECLINE / REVIEW
```

**New output fields:**
```
recommended_action: str     # "APPROVE", "STEP_UP_3DS", "DECLINE", "MANUAL_REVIEW"
decision_confidence: float  # 0-1
decision_stage: str         # which stage made the final call
rule_that_blocked: str      # if declined by rule
step_up_method: str         # "3ds_v2", "otp_sms", "biometric" (if step-up)
```

---

#### 5.3.2 Risk score mapping (1-999)

Map internal 0-1 probability to industry-standard 1-999 scale for UI display:

```python
def to_network_risk_score(probability: float) -> int:
    """Map 0-1 probability to 1-999 Visa/Mastercard-style risk score."""
    return max(1, min(999, int(probability * 998) + 1))

# Thresholds:
# 1-300:   Low risk → auto-approve
# 301-600: Medium risk → step-up authentication
# 601-800: High risk → decline or manual review
# 801-999: Critical → block + alert
```

Display in UI as `"Risk Score: 742 / 999"` instead of `"74.2%"`.

---

#### 5.3.3 Explanation engine

**Current:** `fired_rules` string in output.

**Improvement:** Structured explanation for each decision:

```json
{
  "decision_explanation": {
    "primary_reason": "RULE_HOSTAGE_CALL_COERCION fired — active phone call during high-value transfer to new payee",
    "contributing_factors": [
      {"factor": "concurrent_call_active", "impact": "+0.35", "description": "Phone call active during banking session"},
      {"factor": "new_payee_flag", "impact": "+0.20", "description": "First transfer to this recipient"},
      {"factor": "amount_deviation_score", "impact": "+0.15", "description": "Amount 2.8σ above user baseline"}
    ],
    "ml_score": 0.72,
    "rule_score": 0.95,
    "final_score": 0.89,
    "confidence": 0.94
  }
}
```

**Real-world parallel:** FICO's **TRIAD Customer Manager** provides reason codes for every decision (required by FCRA/ECOA in the US).

**File to create:** `blue_team/explainer.py`

---

### 5.4 Retraining & Model Operations

#### 5.4.1 Current retraining gaps

| Gap | Real-world practice | Improvement |
|-----|--------------------|-|
| Full retrain from scratch | Incremental/online learning preferred | Add warm-start retraining option |
| No model versioning | Champion/challenger A/B testing | Add model registry with version tags |
| No drift detection | PSI/KS monitoring on features | Add drift detector |
| No holdout validation | Temporal train/test split | Split by timestamp, not random |
| Retrain on all data | Retrain on recent window (90 days) | Add configurable training window |

#### 5.4.2 Model registry

```python
# blue_team/model_registry.py

@dataclass
class ModelVersion:
    version_id: str           # "v3.2026-08-23"
    model_type: str
    trained_at: str
    training_samples: int
    metrics: dict             # roc_auc, recall, precision, f1
    feature_importance: dict
    status: str               # "champion", "challenger", "archived"
    config_hash: str

class ModelRegistry:
    def register(self, pipeline, metrics) -> ModelVersion
    def promote_to_champion(self, version_id)
    def get_champion(self) -> BlueTeamPipeline
    def compare(self, v1, v2) -> dict  # side-by-side metrics
```

**UI display:** "Model v3 (Champion) — ROC-AUC 0.891 — trained on 12,400 samples — promoted 2 cycles ago"

---

#### 5.4.3 Drift detection

```python
# blue_team/drift_detector.py

class DriftDetector:
    def compute_psi(self, expected: np.array, actual: np.array) -> float:
        """Population Stability Index. > 0.25 = significant drift."""

    def check_feature_drift(self, baseline_df, current_df) -> dict:
        """Return per-feature PSI scores."""

    def check_prediction_drift(self, baseline_probs, current_probs) -> float:
        """Detect if model scores are shifting."""

    def should_retrain(self, drift_report) -> bool:
        """Recommend retrain if any feature PSI > 0.25 or prediction drift > 0.15."""
```

**Real-world parallel:** Mastercard monitors model drift continuously. Visa requires issuers to revalidate models annually.

---

#### 5.4.4 Temporal validation

**Current:** Random train/test split (implicit in sklearn).

**Improvement:** Always split by timestamp:
```python
# Train on transactions before T, test on transactions after T
split_date = df["timestamp"].quantile(0.80)
train = df[df["timestamp"] <= split_date]
test  = df[df["timestamp"] > split_date]
```

**Why:** Fraud patterns evolve over time. Random splits leak future information into training — inflating metrics unrealistically.

---

### 5.5 Post-Authorization Monitoring

Production systems don't stop at authorization. Add a **second scoring pass**:

#### 5.5.1 Batch review queue

After authorization, run a batch job (simulated) that re-scores all APPROVED transactions with:
- Updated graph features (now that more txns exist)
- Velocity checks with full window data
- Cross-reference with newly identified mule accounts

**Output:** `post_auth_review_queue` — transactions that were approved but now flagged.

**UI:** New filter pill in Stream: **"Post-Auth Flags"**

**Real-world parallel:** Every major issuer runs nightly batch fraud detection on authorized-but-not-settled transactions. Mastercard's **Safety Net** provides a network-level safety net for issuers.

---

#### 5.5.2 Chargeback feedback loop

```
Authorization → APPROVE (fraud missed)
        ↓
[30-120 days]
        ↓
Chargeback filed → label confirmed as fraud
        ↓
Feedback to model training → "this pattern was fraud"
        ↓
Model learns from delayed label
```

**Implementation:**
- Add `chargeback_filed: bool` and `chargeback_days_after: int` to oracle
- Simulate chargebacks on 40% of evaded fraud + 5% of friendly fraud
- Retrain includes chargeback-confirmed labels
- UI shows "Chargeback Confirmed" badge on previously-approved fraud rows

---

### 5.6 Analyst Workflow Simulation

Make the Blue Team workspace feel like a real fraud operations center:

#### 5.6.1 Case management

| Feature | Description |
|---------|-------------|
| **Case creation** | HIGH risk txn auto-creates a case |
| **Case assignment** | Simulated analyst pool (Auto / Analyst-1 / Analyst-2) |
| **Case actions** | Confirm Fraud / Confirm Legitimate / Escalate / Request Info |
| **Case SLA** | Timer showing "Review within 4 hours" |
| **Case outcome feeds back to model** | Confirmed labels added to training data |

#### 5.6.2 Account actions

When fraud confirmed, simulate account actions:
- `FREEZE_ACCOUNT` — block all outgoing
- `LOWER_LIMIT` — reduce daily transfer limit
- `REQUIRE_CALLBACK` — block until customer calls
- `NOTIFY_CUSTOMER` — SMS/email alert (simulated)

---

## 6. Shared Data Model Evolution

### 6.1 Expanded public columns (target: 35-40)

```python
PUBLIC_COLUMNS_V2 = [
    # --- Existing (19) ---
    "transaction_id", "timestamp", "sender_id", "receiver_id",
    "amount", "channel", "sender_account_age_days", "receiver_account_age_days",
    "device_type", "session_duration_sec", "time_since_payee_added_sec",
    "concurrent_call_active", "ip_country", "ip_change_flag",
    "login_to_transaction_gap_sec", "velocity_1h", "velocity_24h",
    "amount_deviation_score", "new_payee_flag",

    # --- Payment rail (8) ---
    "transaction_stage",           # authorization / clearing / settlement / chargeback
    "merchant_category_code",      # MCC
    "merchant_name",
    "merchant_country",
    "card_present",                # CP vs CNP
    "entry_mode",                  # chip / contactless / ecom
    "authentication_method",       # none / otp / 3ds_v2 / biometric
    "network_risk_score",          # 1-999 (computed by blue team)

    # --- Graph features (5) ---
    "shared_device_user_count",
    "shared_ip_user_count",
    "receiver_unique_sender_count_24h",
    "graph_cluster_size",
    "mule_likelihood_score",

    # --- Behavioral (4) ---
    "device_fingerprint_hash",
    "is_round_amount",
    "cumulative_amount_24h",
    "failed_login_attempts_24h",
]
```

### 6.2 Expanded oracle columns

```python
ANSWER_KEY_COLUMNS_V2 = [
    # --- Existing (6) ---
    "transaction_id", "ground_truth_label", "attack_subtype",
    "stealth_level", "evasion_technique", "evasion_parameters",

    # --- Delayed labels (4) ---
    "chargeback_filed",
    "chargeback_days_after",
    "chargeback_reason_code",
    "analyst_confirmed_fraud",

    # --- Attack metadata (4) ---
    "coercion_script",
    "impersonation_entity",
    "mule_layer_depth",
    "attack_campaign_id",
]
```

### 6.3 Expanded prediction output

```python
PREDICTION_COLUMNS_V2 = [
    # --- Existing (8) ---
    "transaction_id", "fraud_probability", "predicted_label",
    "risk_tier", "fired_rules", "ml_probability", "rule_score",

    # --- Decision engine (6) ---
    "network_risk_score",          # 1-999
    "recommended_action",          # APPROVE / STEP_UP / DECLINE / REVIEW
    "decision_confidence",
    "decision_stage",
    "step_up_method",
    "decision_explanation_json",

    # --- Post-auth (3) ---
    "post_auth_flagged",
    "post_auth_reason",
    "analyst_case_id",
]
```

---

## 7. Closed-Loop Adversarial Cycle Enhancements

### 7.1 Current cycle

```
Generate → Score → Evaluate → Tune → Retrain → (repeat)
```

### 7.2 Enhanced cycle

```
┌─────────────────────────────────────────────────────────────┐
│                    ADVERSARIAL CYCLE v2                      │
│                                                              │
│  Red Team                          Blue Team                 │
│  ┌──────────────┐                  ┌──────────────┐         │
│  │ 1. Generate  │─── blind CSV ───→│ 4. Score     │         │
│  │    attacks   │                  │    (auth)    │         │
│  └──────┬───────┘                  └──────┬───────┘         │
│         │                                  │                 │
│  ┌──────▼───────┐                  ┌──────▼───────┐         │
│  │ 2. Validate  │                  │ 5. Post-auth │         │
│  │    realism   │                  │    review    │         │
│  └──────┬───────┘                  └──────┬───────┘         │
│         │                                  │                 │
│  ┌──────▼───────┐                  ┌──────▼───────┐         │
│  │ 3. Evasion   │◄── feedback ────│ 6. Evaluate  │         │
│  │    tuning    │                  │    + explain │         │
│  └──────────────┘                  └──────┬───────┘         │
│                                            │                 │
│                                    ┌──────▼───────┐         │
│                                    │ 7. Retrain   │         │
│                                    │    + drift   │         │
│                                    │    check     │         │
│                                    └──────┬───────┘         │
│                                            │                 │
│                                    ┌──────▼───────┐         │
│                                    │ 8. Promote   │         │
│                                    │    model if  │         │
│                                    │    improved  │         │
│                                    └──────────────┘         │
│                                                              │
│  [30-120 days later]                                         │
│  ┌──────────────┐                  ┌──────────────┐         │
│  │ Chargebacks  │─── labels ────→ │ Retrain with │         │
│  │ filed        │                  │ delayed labels│         │
│  └──────────────┘                  └──────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Cycle metrics dashboard (new UI section)

Track across cycles:

| Metric | Description |
|--------|-------------|
| **Detection rate trend** | Line chart over cycles |
| **Evasion rate trend** | Should decrease as blue team adapts |
| **Stealth escalation** | Red team stealth level over cycles |
| **Rule effectiveness** | Which rules catch most fraud per cycle |
| **Model AUC trend** | ROC-AUC over retrain cycles |
| **Attack type distribution** | How red team shifts weights |
| **Realism score trend** | Ensures attacks stay realistic |
| **Chargeback recovery rate** | Fraud caught post-authorization |

---

## 8. API & Backend Improvements

### 8.1 New endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/red-team/generate/stream` | SSE progress streaming during generation |
| GET | `/api/red-team/attack-types` | List all attack types with descriptions |
| GET | `/api/blue-team/rules` | List all rules with descriptions + fire rates |
| GET | `/api/blue-team/model/versions` | Model registry history |
| POST | `/api/blue-team/model/promote` | Promote challenger to champion |
| GET | `/api/blue-team/drift` | Current drift report |
| POST | `/api/blue-team/cases/{id}/resolve` | Analyst case resolution |
| GET | `/api/graph/cluster/{entity_id}` | Graph neighborhood for entity |
| POST | `/api/simulate/chargeback` | Simulate chargeback on a transaction |
| GET | `/api/metrics/cycle-history` | Full cycle metrics for dashboard |
| GET | `/api/export/transactions` | CSV export of current dataset |

### 8.2 Enhanced `/api/state` response

Add to existing state payload:

```json
{
  "summary": { "...existing..." },
  "metrics": { "...existing..." },
  "realism": { "...existing..." },
  "tunerEval": { "...existing..." },
  "tunerRecommendation": {
    "...existing...",
    "per_rule_evasion": {},
    "recommended_techniques": [],
    "realism_score": 0.91
  },
  "retrainHistory": ["...existing..."],
  "transactions": ["...existing..."],

  "modelInfo": {
    "version": "v3.2026-08-23",
    "type": "xgboost",
    "status": "champion",
    "feature_count": 35,
    "training_samples": 12400
  },
  "driftReport": {
    "overall_psi": 0.08,
    "features_drifted": [],
    "retrain_recommended": false
  },
  "ruleStats": [
    {"rule_id": "RULE_HOSTAGE_CALL", "fire_rate": 0.04, "precision": 0.89}
  ],
  "cycleMetrics": {
    "detection_rate_trend": [0.72, 0.78, 0.81],
    "evasion_rate_trend": [0.28, 0.22, 0.19]
  },
  "postAuthQueue": [],
  "graphSummary": {
    "total_entities": 850,
    "suspicious_clusters": 3,
    "mule_accounts_detected": 12
  }
}
```

---

## 9. Evaluation & Metrics Framework

### 9.1 Current metrics

Precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, per-threat breakdown.

### 9.2 Additional metrics to track

| Metric | Formula | Why it matters |
|--------|---------|---------------|
| **False positive rate at 95% recall** | FPR when recall = 0.95 | Real issuers target specific recall levels |
| **Detection latency** | Time from fraud to detection | Real-time vs post-auth vs chargeback |
| **Cost-weighted loss** | FN×$100 + FP×$5 | Business impact, not just statistical |
| **Evasion half-life** | Cycles until new attack 50% detected | Measures blue team adaptation speed |
| **Rule coverage** | % fraud caught by rules alone | Rules should catch obvious cases cheaply |
| **ML lift** | AUC(ensemble) - AUC(rules only) | Value added by ML |
| **Stealth break-even** | Stealth level where detection = 50% | Red team capability ceiling |
| **Realism-adjusted evasion** | Evasion × realism_score | Penalize unrealistic attacks |
| **Chargeback recovery rate** | Chargebacks / total fraud | Post-auth effectiveness |
| **Analyst review rate** | REVIEW decisions / total | Operational load |

### 9.3 Reporting format

After each cycle, generate a structured report:

```
═══════════════════════════════════════════════════
  AEGIS-AI ADVERSARIAL CYCLE REPORT — Cycle #4
═══════════════════════════════════════════════════

RED TEAM
  Generated:     1,000 transactions (80 fraud / 920 normal)
  Stealth level: 0.75 (evasive)
  Attack mix:    Voice Clone 40% | Ephemeral 35% | Digital Arrest 25%
  Realism score: 0.91 ✓

BLUE TEAM
  Model:         v4 (XGBoost champion)
  ROC-AUC:       0.891 (+0.012 vs previous)
  Recall:        0.81 (+0.03)
  Precision:     0.76 (-0.01)
  FPR@95%Recall: 0.08

EVASION ANALYSIS
  Overall evasion rate:     19% (down from 28%)
  Voice Clone evasion:      12%
  Ephemeral Merchant:       31% ← highest
  Digital Arrest evasion:   15%

RULE EFFECTIVENESS
  RULE_HOSTAGE_CALL:         34 catches (precision 0.91)
  RULE_MULE_ACCOUNT_AGE:     18 catches (precision 0.83)
  RULE_INSTANT_NEW_PAYEE:    22 catches (precision 0.77)

RECOMMENDATIONS
  → Red Team: Increase ephemeral merchant weight to 45%
  → Red Team: Escalate stealth to 0.85
  → Blue Team: Retrain recommended (ephemeral evasion > 25%)
  → Blue Team: Feature drift on `merchant_domain_age` (PSI=0.18)

═══════════════════════════════════════════════════
```

---

## 10. Real-World Case Study Mappings

Use these in the Threats tab and documentation to make the project informational:

### 10.1 Voice Clone APP

| Real Case | Details | AEGIS-AI Mapping |
|-----------|---------|-----------------|
| **Arup Patel case (2024, UK)** | £500,000 stolen via AI voice clone of company director. Multiple wire transfers authorized by finance team member who believed they were on call with CEO. | Voice clone attack, high stealth, Wire channel, multi-tranche |
| **Hong Kong deepfake (2024)** | $25M stolen in video conference call with deepfake CFO. Finance worker transferred funds believing entire leadership team was on call. | Digital arrest variant with video_call_active |
| **FTC Data (2024)** | Imposter scam losses: $2.7B reported in US. Phone calls were initiation method in 80% of cases. | concurrent_call_active signal |

### 10.2 Ephemeral Merchant

| Real Case | Details | AEGIS-AI Mapping |
|-----------|---------|-----------------|
| **Fake Shopify stores (2024-2025)** | AI-generated product images + descriptions. Facebook/Instagram ads drive traffic. Stores disappear after 48-72 hours. | Ephemeral merchant, MCC 9999, domain_age ≤ 3 days |
| **Pinduoduo scam rings (2023, China)** | Group buying platform scams with fake merchants collecting payments from thousands before vanishing. | Burst pattern, multiple victims → same merchant |
| **Mastercard Alert (2025)** | Network-wide alert on merchant boarding velocity exceeding 50 new merchants/day from single acquirer. | merchant boarding velocity rule |

### 10.3 Digital Arrest

| Real Case | Details | AEGIS-AI Mapping |
|-----------|---------|-----------------|
| **Singapore victims (2024)** | SGD 110M lost to government impersonation scams. Victims told to transfer to "safe accounts." | Digital arrest, impersonation_entity: police |
| **Indian diaspora in US (2024-2025)** | Scammers impersonate Indian embassy/consulate. Victims told their Aadhaar/PAN is linked to crime. | diaspora_flag targeting, cross-border |
| **UK "courier fraud" (ongoing)** | Scammers tell elderly victims to withdraw cash or transfer to "safe account" for "police investigation." | Digital arrest, targeting age_group: "60+" |

### 10.4 Account Takeover

| Real Case | Details | AEGIS-AI Mapping |
|-----------|---------|-----------------|
| **SIM swap + banking (2023, US)** | T-Mobile SIM swap → intercept 2FA → drain bank accounts within minutes. | ATO: new device + IP change + instant transfer |
| **Credential stuffing (2024)** | 15B stolen credentials in circulation. Automated bots test on banking sites. | Card testing + ATO hybrid |

---

## 11. Implementation Roadmap

### Phase 1 — Foundation (Weeks 1-2)
**Theme: Payment rail realism + rule expansion**

| Task | Team | Files |
|------|------|-------|
| Add MCC, merchant_name, card_present, auth_method fields | Red | config.py, baseline_generator.py |
| Add transaction_stage lifecycle | Red | config.py, orchestrator.py |
| Add 10 new rules (Section 5.1.1) | Blue | rule_engine.py |
| Add velocity engine (multi-dimensional) | Blue | velocity_engine.py (new) |
| Map risk score to 1-999 scale | Blue | pipeline.py, config.py |
| Add recommended_action to output | Blue | pipeline.py, ensemble.py |
| Update frontend to show new fields in inspector | UI | index.html, app.js |
| Bind realism card to live API data | UI | app.js |

---

### Phase 2 — Attack Expansion (Weeks 3-4)
**Theme: New attack types + graph analytics**

| Task | Team | Files |
|------|------|-------|
| Account Takeover attack generator | Red | attack_generators/account_takeover.py |
| Card Testing attack generator | Red | attack_generators/card_testing.py |
| Money Mule network generator | Red | attack_generators/money_mule.py |
| Entity graph module | Red | graph/entity_graph.py (new) |
| Graph features in public columns | Red | orchestrator.py, config.py |
| Graph-based rules | Blue | rule_engine.py |
| Feature engineering (derived features) | Blue | preprocessor.py |
| XGBoost as default model | Blue | ml_detector.py, config.py |
| Explanation engine | Blue | explainer.py (new) |

---

### Phase 3 — Operations Maturity (Weeks 5-6)
**Theme: Model ops + post-auth + analyst workflow**

| Task | Team | Files |
|------|------|-------|
| Model registry (champion/challenger) | Blue | model_registry.py (new) |
| Drift detection (PSI) | Blue | drift_detector.py (new) |
| Temporal train/test split | Blue | pipeline.py, retrainer.py |
| Post-authorization batch review | Blue | post_auth_monitor.py (new) |
| Chargeback simulation + delayed labels | Red | orchestrator.py, config.py |
| Friendly fraud attack type | Red | attack_generators/friendly_fraud.py |
| Analyst case management API | Backend | app.py |
| Cycle metrics dashboard | UI | index.html, app.js, charts.js |

---

### Phase 4 — Presentation & Polish (Weeks 7-8)
**Theme: Real-world case studies + consortium simulation**

| Task | Team | Files |
|------|------|-------|
| Real-world case studies in Threats tab | UI | index.html |
| Attack timeline visualizations | UI | index.html, charts.js |
| Consortium data simulation (shared fraud DB) | Red+Blue | consortium.py (new) |
| Cycle report generator | Blue | report_generator.py (new) |
| Enhanced API endpoints (Section 8.1) | Backend | app.py |
| Comprehensive test suite for new features | Tests | tests/ |
| Update README with architecture diagram | Docs | README.md |

---

## 12. Testing Strategy

### 12.1 Red Team tests to add

```python
# tests/test_red_team_v2.py

def test_mcc_assignment():
    """All transactions have valid MCC codes."""

def test_transaction_stages():
    """All new txns start at 'authorization' stage."""

def test_account_takeover_signals():
    """ATO attacks have new device + IP change + instant transfer."""

def test_card_testing_velocity():
    """Card testing generates ≥5 txns in 10 min with amount < $5."""

def test_money_mule_chain():
    """Mule attacks create 3+ hop chains with decreasing account ages."""

def test_entity_graph_clusters():
    """Graph detects shared-receiver clusters in mule attacks."""

def test_chargeback_simulation():
    """Fraud txns generate chargebacks within 30-120 days."""

def test_friendly_fraud_undetectable_at_auth():
    """Friendly fraud txns score < 0.30 at authorization time."""

def test_auth_method_distribution():
    """CNP txns have 60-80% 3DS adoption rate."""

def test_benfords_law():
    """Amount first-digit distribution passes Benford's test."""
```

### 12.2 Blue Team tests to add

```python
# tests/test_blue_team_v2.py

def test_new_rules_fire_correctly():
    """Each new rule fires on designed trigger and not on normal txns."""

def test_velocity_engine_windows():
    """Velocity counts accurate across 1h/24h/7d windows."""

def test_risk_score_1_to_999():
    """Network risk score always in [1, 999]."""

def test_recommended_action_mapping():
    """HIGH tier → DECLINE or REVIEW, MEDIUM → STEP_UP, LOW → APPROVE."""

def test_explanation_engine_output():
    """Every HIGH/CRITICAL decision has structured explanation."""

def test_model_registry_champion_challenger():
    """Promote challenger only if AUC improves."""

def test_drift_detection_psi():
    """PSI > 0.25 triggers retrain recommendation."""

def test_temporal_split_no_leakage():
    """Test set timestamps always after train set."""

def test_post_auth_catches_approved_fraud():
    """Post-auth review flags ≥20% of evaded fraud."""

def test_xgboost_outperforms_rf():
    """XGBoost AUC ≥ RF AUC on same data."""
```

---

## 13. Glossary of Real-World Terms

| Term | Definition | Used in AEGIS-AI |
|------|-----------|-----------------|
| **Authorization** | Real-time approve/decline decision at point of sale | `transaction_stage: authorization` |
| **Acquirer** | Bank that processes payments for merchants | Future: `acquirer_id` field |
| **APP Fraud** | Authorized Push Payment — victim authorizes fraud themselves | Voice Clone, Digital Arrest attacks |
| **BIN** | Bank Identification Number — first 6 digits of card | Future: `card_bin` field |
| **Chargeback** | Disputed transaction reversed from merchant | Delayed label in oracle |
| **CNP** | Card Not Present — online/phone transaction | `card_present: false` |
| **CoP** | Confirmation of Payee — UK name-matching service | Future: `payee_name_verified` |
| **MCC** | Merchant Category Code — 4-digit industry classifier | `merchant_category_code` |
| **Mule account** | Bank account used to receive and forward stolen funds | Money Mule attack type |
| **PSD2 SCA** | EU Strong Customer Authentication regulation | `authentication_method: 3ds_v2` |
| **PSI** | Population Stability Index — model drift metric | Drift detector |
| **ROC-AUC** | Area under Receiver Operating Characteristic curve | Primary model metric |
| **3DS** | 3-D Secure — online authentication protocol | Step-up authentication |
| **Velocity check** | Rate limiting on transaction frequency | Velocity engine |
| **Consortium data** | Shared fraud intelligence across institutions | Future: consortium module |
| **Decision Intelligence** | Mastercard's fraud scoring product | Hybrid ensemble equivalent |
| **Falcon** | FICO's fraud management platform | Blue Team pipeline equivalent |
| **Safety Net** | Mastercard's network-level fraud blocking | Post-auth monitor equivalent |

---

## Quick-Start: Top 5 Improvements to Implement First

If you can only do five things, do these — they deliver the most realism and presentation value:

1. **Add MCC + merchant fields + card_present/auth_method** (Section 4.1) — instantly makes transactions look like real payment data
2. **Add 10 new rules including ATO and mule detection** (Section 5.1.1) — makes Blue Team feel like a production rule engine
3. **Add Account Takeover attack type** (Section 4.3) — most common real-world fraud type
4. **Add entity graph with mule cluster detection** (Section 4.5) — biggest differentiator vs basic simulations
5. **Add real-world case studies to Threats tab** (Section 10) — makes the project informational and presentation-ready

---

*Last updated: 2026-08-23 | AEGIS-AI Team Improvement Plan v1.0*
