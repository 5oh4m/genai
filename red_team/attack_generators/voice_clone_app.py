"""
Threat 1 Generator: Voice-Cloned 'Family Emergency' Authorized Push Payment (APP) Fraud.
"""

from typing import List, Dict, Tuple, Any
import datetime
import json
import numpy as np

from red_team.config import LABEL_VOICE_CLONE, CHANNELS, DEVICE_TYPES
from red_team.attack_generators.base import BaseAttackGenerator


class VoiceCloneAPPGenerator(BaseAttackGenerator):
    """
    Simulates Generative Voice Cloning scams where a panic-stricken victim authorizes
    an urgent transfer to a mule account.
    """

    def generate(
        self,
        count: int,
        stealth_level: float = 0.0,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        txns: List[Dict[str, Any]] = []
        answers: List[Dict[str, Any]] = []
        
        stealth = float(np.clip(stealth_level, 0.0, 1.0))
        user_ids = list(self.users.keys())

        for i in range(count):
            victim = self.users[self.rng.choice(user_ids)]
            
            # Timestamp selection
            sim_sec = int(self.rng.uniform(0, self.config.simulation_days * 86400))
            txn_dt = self.start_dt + datetime.timedelta(seconds=sim_sec)

            # --- Naive vs Evasive Behavioral Shaping ---
            # 1. Hour of Attack
            if self.rng.rand() < (1.0 - 0.8 * stealth):
                # Naive: Panic hour (late night / early morning 23:00 - 04:00)
                hour = int(self.rng.choice([22, 23, 0, 1, 2, 3, 4]))
                timing_evasion = False
            else:
                # Evasive: Mimic victim's normal diurnal active hours
                hour = victim.sample_hour(self.rng)
                timing_evasion = True
            
            txn_dt = txn_dt.replace(
                hour=hour,
                minute=int(self.rng.randint(0, 60)),
                second=int(self.rng.randint(0, 60))
            )

            # 2. Mule / Destination Account
            # Mule account is freshly minted (0 to 3 days old)
            mule_id = f"MULE_VC_{self.rng.randint(1000, 9999)}"
            mule_age_days = int(self.rng.randint(0, 3))
            
            # 3. Time Since Payee Added
            if stealth < 0.3:
                # Naive: Immediate transfer within seconds of adding payee
                time_since_payee_sec = int(self.rng.uniform(8, 55))
                delay_evasion = "instant_unpadded"
            elif stealth < 0.7:
                # Moderate: Modest delay introduced (2 to 5 minutes)
                time_since_payee_sec = int(self.rng.uniform(120, 350))
                delay_evasion = "short_dwell_delay"
            else:
                # High Stealth: Sophisticated padding (10 to 30 minutes)
                time_since_payee_sec = int(self.rng.uniform(600, 1800))
                delay_evasion = "sophisticated_delay_padding"

            # 4. Amount Calculation
            if stealth < 0.4:
                # Naive: Round, urgent round figures ($300 - $900)
                base_round = self.rng.choice([300.0, 450.0, 500.0, 650.0, 750.0, 800.0, 950.0])
                amount = float(base_round)
                amount_evasion = "naive_round_number"
            elif stealth < 0.8:
                # Moderate: Off-round jittered urgent figure
                base_round = self.rng.choice([385.0, 492.0, 647.0, 739.0])
                amount = round(float(base_round + self.rng.uniform(0.10, 0.95)), 2)
                amount_evasion = "off_round_jitter"
            else:
                # High Stealth: Calibrated to victim's spending history + non-round cents
                multiplier = self.rng.uniform(1.2, 2.2)
                amount = round(float(victim.base_mean_amount * multiplier + self.rng.uniform(0.10, 0.99)), 2)
                amount_evasion = "historical_mean_mimicry"

            # 5. Call State & Session Telemetry
            if stealth < 0.5:
                # Naive: Victim is on an active voice call while transferring
                concurrent_call = bool(self.rng.rand() < 0.85)
                session_duration_sec = int(self.rng.uniform(40, 120))
                login_gap = int(self.rng.uniform(5, 25))
            else:
                # Evasive: Scammer instructs victim to hang up before opening banking app
                concurrent_call = False
                session_duration_sec = int(np.clip(self.rng.normal(loc=130, scale=40), 60, 400))
                login_gap = int(np.clip(self.rng.normal(loc=40, scale=15), 15, 120))

            channel = self.rng.choice(["P2P", "UPI", "Wire"], p=[0.5, 0.4, 0.1])
            victim_age_days = max(1, (txn_dt - victim.creation_date).days)

            evasion_details = {
                "delay_technique": delay_evasion,
                "amount_technique": amount_evasion,
                "timing_evasion": timing_evasion,
                "call_state_masked": not concurrent_call,
            }

            txn_row = {
                "transaction_id": "",
                "timestamp": txn_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "sender_id": victim.user_id,
                "receiver_id": mule_id,
                "amount": amount,
                "channel": channel,
                "sender_account_age_days": victim_age_days,
                "receiver_account_age_days": mule_age_days,
                "device_type": victim.preferred_device,
                "session_duration_sec": session_duration_sec,
                "time_since_payee_added_sec": time_since_payee_sec,
                "concurrent_call_active": concurrent_call,
                "ip_country": victim.home_country,
                "ip_change_flag": False,
                "login_to_transaction_gap_sec": login_gap,
                "velocity_1h": 0,
                "velocity_24h": 0,
                "amount_deviation_score": 0.0,
                "new_payee_flag": True,
            }

            evasion_summary = (
                f"{delay_evasion}+{amount_evasion}"
                if stealth > 0.0
                else "none"
            )

            ans_row = {
                "transaction_id": "",
                "ground_truth_label": LABEL_VOICE_CLONE,
                "attack_subtype": "voice_clone_emergency_app",
                "stealth_level": stealth,
                "evasion_technique": evasion_summary,
                "evasion_parameters": json.dumps(evasion_details),
            }

            txns.append(txn_row)
            answers.append(ans_row)

        return txns, answers
