"""
Baseline Transaction Generator.
Produces high-fidelity, statistically realistic baseline consumer transaction streams.
"""

from typing import List, Dict, Tuple, Any
import datetime
import random
import numpy as np
from faker import Faker

from red_team.config import (
    RedTeamConfig,
    LABEL_NORMAL,
    CHANNELS,
    CHANNEL_WEIGHTS_BASELINE,
    DEVICE_TYPES,
    DEVICE_WEIGHTS_BASELINE,
    COUNTRIES,
    DEFAULT_HOME_COUNTRY,
)

class UserProfile:
    """Represents a simulated consumer account with consistent behavioral habits."""
    def __init__(self, user_id: str, fake: Faker, rng: np.random.RandomState, start_dt: datetime.datetime):
        self.user_id = user_id
        self.name = fake.name()
        self.initial_account_age_days = int(rng.randint(90, 2500))
        self.home_country = DEFAULT_HOME_COUNTRY
        self.preferred_device = rng.choice(DEVICE_TYPES, p=DEVICE_WEIGHTS_BASELINE)
        
        # Financial behavior
        # Mean transaction amount between $15 and $180
        self.base_mean_amount = float(rng.uniform(15.0, 180.0))
        self.amount_sigma = float(rng.uniform(0.3, 0.7))
        
        # Diurnal schedule (mean peak hour 12:00 - 19:00)
        self.peak_hour = float(rng.uniform(12.0, 19.0))
        self.hour_std = float(rng.uniform(2.5, 4.5))
        
        # Daily transaction activity rate (Poisson lambda)
        self.txns_per_day = float(rng.uniform(0.5, 3.5))
        
        # Frequent payees: list of receiver_ids and their initial relationship ages
        self.frequent_payees: List[str] = []
        self.payee_added_timestamps: Dict[str, datetime.datetime] = {}
        self.creation_date = start_dt - datetime.timedelta(days=self.initial_account_age_days)

    def sample_amount(self, rng: np.random.RandomState) -> float:
        """Sample a spending amount from user's log-normal distribution."""
        mu = np.log(self.base_mean_amount) - (self.amount_sigma ** 2) / 2
        amt = float(rng.lognormal(mu, self.amount_sigma))
        return max(1.0, round(amt, 2))

    def sample_hour(self, rng: np.random.RandomState) -> int:
        """Sample transaction hour according to normal diurnal preference."""
        hour = int(rng.normal(self.peak_hour, self.hour_std)) % 24
        # Depress midnight to early morning (1 AM - 6 AM)
        if 1 <= hour <= 5 and rng.rand() > 0.15:
            hour = (hour + int(rng.randint(6, 14))) % 24
        return hour


class MerchantProfile:
    """Represents a legitimate, established merchant or service provider."""
    def __init__(self, merchant_id: str, fake: Faker, rng: np.random.RandomState, start_dt: datetime.datetime):
        self.merchant_id = merchant_id
        self.business_name = fake.company()
        self.category = rng.choice(["grocery", "retail", "utility", "dining", "subscription", "transport"])
        self.initial_account_age_days = int(rng.randint(180, 3650))
        self.country = DEFAULT_HOME_COUNTRY
        self.creation_date = start_dt - datetime.timedelta(days=self.initial_account_age_days)


class BaselineGenerator:
    """Generates normal consumer transactions and user population."""
    def __init__(self, config: RedTeamConfig):
        self.config = config
        self.rng = np.random.RandomState(config.seed)
        self.fake = Faker()
        Faker.seed(config.seed)
        self.start_dt = datetime.datetime.fromisoformat(config.start_date)
        
        self.users: Dict[str, UserProfile] = {}
        self.merchants: Dict[str, MerchantProfile] = {}
        self._initialize_population()

    def _initialize_population(self):
        """Create initial cohorts of users and merchants."""
        for i in range(1, self.config.num_users + 1):
            uid = f"USR_{i:05d}"
            self.users[uid] = UserProfile(uid, self.fake, self.rng, self.start_dt)

        for j in range(1, self.config.num_merchants + 1):
            mid = f"MER_{j:05d}"
            self.merchants[mid] = MerchantProfile(mid, self.fake, self.rng, self.start_dt)

        # Pre-populate familiar payees for each user
        merchant_ids = list(self.merchants.keys())
        user_ids = list(self.users.keys())

        for user in self.users.values():
            num_fav_merchants = self.rng.randint(3, 8)
            num_fav_peers = self.rng.randint(2, 5)
            
            fav_m = list(self.rng.choice(merchant_ids, size=min(num_fav_merchants, len(merchant_ids)), replace=False))
            peer_pool = [u for u in user_ids if u != user.user_id]
            fav_p = list(self.rng.choice(peer_pool, size=min(num_fav_peers, len(peer_pool)), replace=False))
            
            user.frequent_payees = fav_m + fav_p
            for payee in user.frequent_payees:
                days_ago = self.rng.randint(30, max(31, user.initial_account_age_days))
                user.payee_added_timestamps[payee] = self.start_dt - datetime.timedelta(days=days_ago)

    def generate_baseline_transactions(self, count: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate `count` baseline transactions and matching oracle answer keys.
        """
        txns: List[Dict[str, Any]] = []
        answers: List[Dict[str, Any]] = []
        user_ids = list(self.users.keys())
        merchant_ids = list(self.merchants.keys())

        for _ in range(count):
            user = self.users[self.rng.choice(user_ids)]
            
            # Sample timestamp across simulation duration
            sim_sec = int(self.rng.uniform(0, self.config.simulation_days * 86400))
            txn_dt = self.start_dt + datetime.timedelta(seconds=sim_sec)
            
            # Adjust hour to user's diurnal pattern
            user_hour = user.sample_hour(self.rng)
            txn_dt = txn_dt.replace(hour=user_hour, minute=int(self.rng.randint(0, 60)), second=int(self.rng.randint(0, 60)))
            
            # Receiver selection (85% known payee, 15% new established merchant/peer)
            is_known = (self.rng.rand() < 0.85) and (len(user.frequent_payees) > 0)
            if is_known:
                receiver_id = self.rng.choice(user.frequent_payees)
                new_payee = False
                payee_add_dt = user.payee_added_timestamps[receiver_id]
                time_since_payee_added_sec = max(3600, int((txn_dt - payee_add_dt).total_seconds()))
            else:
                if self.rng.rand() < 0.7:
                    receiver_id = self.rng.choice(merchant_ids)
                else:
                    receiver_id = self.rng.choice([u for u in user_ids if u != user.user_id])
                new_payee = True
                # Added earlier in session or earlier today
                time_since_payee_added_sec = int(self.rng.exponential(scale=7200)) + 120

            # Calculate account ages at timestamp
            sender_age_days = (txn_dt - user.creation_date).days
            if receiver_id.startswith("MER_"):
                rec_age_days = (txn_dt - self.merchants[receiver_id].creation_date).days
            else:
                rec_age_days = (txn_dt - self.users[receiver_id].creation_date).days

            # Device
            if self.rng.rand() < 0.92:
                device = user.preferred_device
            else:
                device = self.rng.choice(DEVICE_TYPES)

            # Session telemetry
            session_duration_sec = int(np.clip(self.rng.normal(loc=120, scale=45), 20, 600))
            login_gap = int(np.clip(self.rng.normal(loc=35, scale=15), 5, min(180, session_duration_sec)))
            
            # Channel
            channel = self.rng.choice(CHANNELS, p=CHANNEL_WEIGHTS_BASELINE)
            
            # Coercion proxy (baseline is almost zero)
            concurrent_call = bool(self.rng.rand() < 0.01)
            
            # Geo anomaly
            ip_change = bool(self.rng.rand() < 0.015)
            ip_country = user.home_country if not ip_change else self.rng.choice(COUNTRIES)

            amount = user.sample_amount(self.rng)

            txn_row = {
                "transaction_id": "",  # Orchestrator assigns sequential ID after sorting
                "timestamp": txn_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "sender_id": user.user_id,
                "receiver_id": receiver_id,
                "amount": amount,
                "channel": channel,
                "sender_account_age_days": max(1, sender_age_days),
                "receiver_account_age_days": max(1, rec_age_days),
                "device_type": device,
                "session_duration_sec": session_duration_sec,
                "time_since_payee_added_sec": time_since_payee_added_sec,
                "concurrent_call_active": concurrent_call,
                "ip_country": ip_country,
                "ip_change_flag": ip_change,
                "login_to_transaction_gap_sec": login_gap,
                "velocity_1h": 0,  # Computed in orchestrator
                "velocity_24h": 0, # Computed in orchestrator
                "amount_deviation_score": 0.0, # Computed in orchestrator
                "new_payee_flag": new_payee,
            }

            ans_row = {
                "transaction_id": "",
                "ground_truth_label": LABEL_NORMAL,
                "attack_subtype": "none",
                "stealth_level": 0.0,
                "evasion_technique": "none",
                "evasion_parameters": "{}",
            }

            txns.append(txn_row)
            answers.append(ans_row)

        return txns, answers
