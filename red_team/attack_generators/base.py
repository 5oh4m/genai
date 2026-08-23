"""
Base Attack Generator Interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any
import datetime
import numpy as np
from faker import Faker

from red_team.config import RedTeamConfig
from red_team.baseline_generator import UserProfile, MerchantProfile


class BaseAttackGenerator(ABC):
    """Abstract Base Class for Red Team Attack Generators."""

    def __init__(
        self,
        config: RedTeamConfig,
        users: Dict[str, UserProfile],
        merchants: Dict[str, MerchantProfile],
        rng: np.random.RandomState,
        fake: Faker,
    ):
        self.config = config
        self.users = users
        self.merchants = merchants
        self.rng = rng
        self.fake = fake
        self.start_dt = datetime.datetime.fromisoformat(config.start_date)

    @abstractmethod
    def generate(
        self,
        count: int,
        stealth_level: float = 0.0,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate synthetic attack transactions and corresponding oracle answer keys.
        
        Args:
            count: Number of attack transactions to synthesize.
            stealth_level: Adversarial stealth coefficient (0.0 = naive/loud, 1.0 = stealthiest).
            
        Returns:
            Tuple of (transactions, answer_key_rows)
        """
        pass
