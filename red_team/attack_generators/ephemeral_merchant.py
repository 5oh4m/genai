"""
Threat 2 Generator: AI-Generated 'Pop-Up' Boutique (Ephemeral Merchant Fraud).
"""

from typing import List, Dict, Tuple, Any
import datetime
import json
import numpy as np

from red_team.config import LABEL_EPHEMERAL_MERCHANT
from red_team.attack_generators.base import BaseAttackGenerator


class EphemeralMerchantGenerator(BaseAttackGenerator):
    """
    Simulates AI-Generated storefront scams where a freshly minted merchant ID
    harvests transactions across multiple victims in a synchronized or staggered bust-out.
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

        # Determine number of ephemeral merchant campaigns
        # Typically 5 to 15 victims per fake merchant campaign
        txns_per_merchant = int(np.clip(8 + self.rng.randint(-2, 5), 3, 20))
        num_merchants = max(1, count // txns_per_merchant)

        generated = 0
        merchant_idx = 0

        while generated < count:
            merchant_idx += 1
            fake_merchant_id = f"MER_EPH_{merchant_idx:04d}_{self.rng.randint(100, 999)}"
            fake_shop_name = f"{self.fake.word().capitalize()} {self.rng.choice(['Boutique', 'Apparel', 'Gadgets', 'Deals', 'Studio'])}"

            # Campaign start date within simulation window
            campaign_start_sec = int(self.rng.uniform(86400, (self.config.simulation_days - 4) * 86400))
            campaign_start_dt = self.start_dt + datetime.timedelta(seconds=campaign_start_sec)

            # Evasion 1: Merchant Account Age
            if stealth < 0.4:
                # Naive: Merchant created the same day or 1-2 days ago
                merchant_age_base = int(self.rng.randint(0, 3))
                age_evasion = "fresh_account_naive"
            elif stealth < 0.7:
                # Moderate: Pre-registered a week earlier
                merchant_age_base = int(self.rng.randint(7, 18))
                age_evasion = "preaged_1_2_weeks"
            else:
                # High Stealth: Matured dormant merchant profile
                merchant_age_base = int(self.rng.randint(30, 90))
                age_evasion = "matured_dormant_merchant"

            # Evasion 2: Burst Window Duration
            if stealth < 0.3:
                # Naive: Tight 12-24 hour burst
                burst_duration_hours = self.rng.uniform(6, 24)
                burst_evasion = "tight_flash_burst"
            elif stealth < 0.7:
                # Moderate: 2-4 days burst
                burst_duration_hours = self.rng.uniform(48, 96)
                burst_evasion = "multi_day_burst"
            else:
                # High Stealth: 5-8 days organic Poisson arrival
                burst_duration_hours = self.rng.uniform(120, 192)
                burst_evasion = "organic_poisson_pacing"

            # Fixed promotional price vs randomized basket
            is_fixed_promo = (stealth < 0.5) and (self.rng.rand() < 0.7)
            promo_price = float(self.rng.choice([29.99, 49.99, 59.99, 79.99, 99.00]))

            # Determine victims for this campaign
            batch_size = min(txns_per_merchant, count - generated)
            victim_cohort = list(self.rng.choice(user_ids, size=batch_size, replace=False))

            for victim_id in victim_cohort:
                victim = self.users[victim_id]

                # Transaction time within burst window
                offset_sec = int(self.rng.uniform(0, burst_duration_hours * 3600))
                txn_dt = campaign_start_dt + datetime.timedelta(seconds=offset_sec)
                
                # Check that txn_dt is within simulation window
                max_sim_sec = self.config.simulation_days * 86400
                if (txn_dt - self.start_dt).total_seconds() > max_sim_sec:
                    txn_dt = self.start_dt + datetime.timedelta(seconds=int(self.rng.uniform(max_sim_sec - 86400, max_sim_sec)))

                # Amount
                if is_fixed_promo:
                    amount = promo_price
                    amt_evasion = "fixed_ad_price"
                else:
                    base_price = float(self.rng.uniform(18.0, 140.0))
                    amount = round(base_price + self.rng.choice([0.49, 0.95, 0.99]), 2)
                    amt_evasion = "varied_retail_basket"

                # Telemetry
                session_duration = int(np.clip(self.rng.normal(loc=180, scale=60), 45, 600))
                time_since_payee = int(self.rng.uniform(30, 300))  # standard e-commerce checkout dwell
                login_gap = int(self.rng.uniform(15, 60))
                channel = self.rng.choice(["Card", "UPI"], p=[0.7, 0.3])
                
                victim_age_days = max(1, (txn_dt - victim.creation_date).days)
                merchant_age_days = max(1, merchant_age_base + int((txn_dt - campaign_start_dt).days))

                evasion_details = {
                    "merchant_shop_name": fake_shop_name,
                    "age_evasion": age_evasion,
                    "burst_evasion": burst_evasion,
                    "amount_technique": amt_evasion,
                }

                txn_row = {
                    "transaction_id": "",
                    "timestamp": txn_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "sender_id": victim.user_id,
                    "receiver_id": fake_merchant_id,
                    "amount": amount,
                    "channel": channel,
                    "sender_account_age_days": victim_age_days,
                    "receiver_account_age_days": merchant_age_days,
                    "device_type": victim.preferred_device,
                    "session_duration_sec": session_duration,
                    "time_since_payee_added_sec": time_since_payee,
                    "concurrent_call_active": False,
                    "ip_country": victim.home_country,
                    "ip_change_flag": False,
                    "login_to_transaction_gap_sec": login_gap,
                    "velocity_1h": 0,
                    "velocity_24h": 0,
                    "amount_deviation_score": 0.0,
                    "new_payee_flag": True,
                }

                evasion_summary = f"{age_evasion}+{burst_evasion}" if stealth > 0.0 else "none"

                ans_row = {
                    "transaction_id": "",
                    "ground_truth_label": LABEL_EPHEMERAL_MERCHANT,
                    "attack_subtype": "ephemeral_merchant_boutique",
                    "stealth_level": stealth,
                    "evasion_technique": evasion_summary,
                    "evasion_parameters": json.dumps(evasion_details),
                }

                txns.append(txn_row)
                answers.append(ans_row)
                generated += 1

        return txns, answers
