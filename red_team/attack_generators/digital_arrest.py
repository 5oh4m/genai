"""
Threat 3 Generator: Deepfake 'Digital Arrest' Video/Audio Coercion Scam.
"""

from typing import List, Dict, Tuple, Any
import datetime
import json
import numpy as np

from red_team.config import LABEL_DIGITAL_ARREST
from red_team.attack_generators.base import BaseAttackGenerator


class DigitalArrestGenerator(BaseAttackGenerator):
    """
    Simulates high-pressure coercion scams where victims are kept under prolonged
    surveillance/interrogation and coerced into liquidating accounts to mule accounts.
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

        generated = 0
        incident_idx = 0

        while generated < count:
            incident_idx += 1
            victim = self.users[self.rng.choice(user_ids)]
            total_target_drain = float(self.rng.uniform(3500.0, 9500.0))

            # Incident start date
            sim_sec = int(self.rng.uniform(86400, (self.config.simulation_days - 2) * 86400))
            incident_start_dt = self.start_dt + datetime.timedelta(seconds=sim_sec)

            # Evasion 1: Single Dump vs Tranche Splitting
            if stealth < 0.4:
                # Naive: 1 large transfer that maxes out account limits
                num_splits = 1
                split_evasion = "single_massive_drain"
            elif stealth < 0.7:
                # Moderate: 2 transfers spaced by 1-3 hours
                num_splits = 2
                split_evasion = "two_tranche_split"
            else:
                # High Stealth: 3-4 transfers under common trigger thresholds (e.g. < $2,500)
                num_splits = int(self.rng.choice([3, 4]))
                split_evasion = "micro_tranche_fanout"

            # Tranche amounts
            if num_splits == 1:
                tranche_amounts = [round(total_target_drain, 2)]
            else:
                # Split total into roughly equal chunks with jitter
                proportions = self.rng.dirichlet(np.ones(num_splits))
                tranche_amounts = [round(float(total_target_drain * p), 2) for p in proportions]
                # Ensure no tranche is zero
                tranche_amounts = [max(150.0, a) for a in tranche_amounts]

            # Evasion 2: Call State Telemetry Camouflage
            if stealth < 0.5:
                # Naive: Victim is on an active VoIP/video call during the session
                concurrent_call_flag = True
                call_evasion = "concurrent_call_leaked"
            else:
                # Evasive: Scammer instructs victim to hang up before checkout
                concurrent_call_flag = False
                call_evasion = "call_hangup_before_submit"

            # Evasion 3: Session Duration Dwell Time
            if stealth < 0.3:
                # Naive: Massive session duration (30 min to 90 min)
                base_session_sec = int(self.rng.uniform(1800, 5400))
                session_evasion = "extreme_dwell_time"
            elif stealth < 0.7:
                # Moderate: 10 to 20 minutes
                base_session_sec = int(self.rng.uniform(600, 1200))
                session_evasion = "moderated_session_length"
            else:
                # High Stealth: Clean quick session (3 to 6 mins) via app restart
                base_session_sec = int(self.rng.uniform(180, 360))
                session_evasion = "app_restart_session_masking"

            # Generate each tranche
            for i, amt in enumerate(tranche_amounts):
                if generated >= count:
                    break

                # Tranche timing spacing
                spacing_hours = i * self.rng.uniform(1.5, 4.0) if num_splits > 1 else 0.0
                txn_dt = incident_start_dt + datetime.timedelta(hours=spacing_hours)
                
                # Receiver mule
                mule_id = f"MULE_DA_{incident_idx:03d}_{i+1}"
                mule_age_days = int(self.rng.randint(1, 10))

                session_duration = int(np.clip(
                    self.rng.normal(loc=base_session_sec, scale=base_session_sec * 0.1),
                    120,
                    7200
                ))
                time_since_payee = int(self.rng.uniform(45, 600))
                login_gap = int(self.rng.uniform(15, 90))
                channel = self.rng.choice(["Wire", "UPI", "P2P"], p=[0.5, 0.4, 0.1])
                
                victim_age_days = max(1, (txn_dt - victim.creation_date).days)

                evasion_details = {
                    "split_technique": split_evasion,
                    "call_evasion": call_evasion,
                    "session_evasion": session_evasion,
                    "tranche_index": i + 1,
                    "total_tranches": num_splits,
                    "total_incident_drain": round(total_target_drain, 2),
                }

                txn_row = {
                    "transaction_id": "",
                    "timestamp": txn_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "sender_id": victim.user_id,
                    "receiver_id": mule_id,
                    "amount": amt,
                    "channel": channel,
                    "sender_account_age_days": victim_age_days,
                    "receiver_account_age_days": mule_age_days,
                    "device_type": victim.preferred_device,
                    "session_duration_sec": session_duration,
                    "time_since_payee_added_sec": time_since_payee,
                    "concurrent_call_active": concurrent_call_flag,
                    "ip_country": victim.home_country,
                    "ip_change_flag": False,
                    "login_to_transaction_gap_sec": login_gap,
                    "velocity_1h": 0,
                    "velocity_24h": 0,
                    "amount_deviation_score": 0.0,
                    "new_payee_flag": True,
                }

                evasion_summary = f"{split_evasion}+{call_evasion}" if stealth > 0.0 else "none"

                ans_row = {
                    "transaction_id": "",
                    "ground_truth_label": LABEL_DIGITAL_ARREST,
                    "attack_subtype": "digital_arrest_coercion",
                    "stealth_level": stealth,
                    "evasion_technique": evasion_summary,
                    "evasion_parameters": json.dumps(evasion_details),
                }

                txns.append(txn_row)
                answers.append(ans_row)
                generated += 1

        return txns, answers
