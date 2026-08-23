"""
Feature Engineering and Preprocessing Pipeline for Blue Team Detection.
"""

from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from blue_team.config import (
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    BOOLEAN_FEATURES,
    BlueTeamConfig,
)


class BlueTeamPreprocessor:
    """Prepares raw transaction data into clean numerical feature tensors for ML models."""

    def __init__(self, config: Optional[BlueTeamConfig] = None):
        self.config = config or BlueTeamConfig()
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

    def _extract_engineered_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract datetime, temporal, and interaction signals."""
        df_out = df.copy()
        
        # Datetime expansion
        ts = pd.to_datetime(df_out["timestamp"])
        df_out["hour_of_day"] = ts.dt.hour
        df_out["day_of_week"] = ts.dt.dayofweek
        df_out["is_night_hour"] = ts.dt.hour.isin([22, 23, 0, 1, 2, 3, 4, 5]).astype(int)
        df_out["is_weekend"] = ts.dt.dayofweek.isin([5, 6]).astype(int)

        # Convert booleans to 0/1 integers
        for col in ["concurrent_call_active", "ip_change_flag", "new_payee_flag"]:
            if col in df_out.columns:
                df_out[col] = df_out[col].astype(int)

        return df_out

    def fit(self, df_raw: pd.DataFrame) -> "BlueTeamPreprocessor":
        """Fits encoder and scaler on training data."""
        df_eng = self._extract_engineered_features(df_raw)

        # Fit Categorical Encoder
        cat_data = df_eng[CATEGORICAL_FEATURES].fillna("Unknown")
        self.encoder.fit(cat_data)
        encoded_cat_names = list(self.encoder.get_feature_names_out(CATEGORICAL_FEATURES))

        # Fit Numerical Scaler
        num_data = df_eng[NUMERICAL_FEATURES].fillna(0.0)
        self.scaler.fit(num_data)

        # Compile final feature list
        self.feature_names = NUMERICAL_FEATURES + BOOLEAN_FEATURES + encoded_cat_names
        self.is_fitted = True
        return self

    def transform(self, df_raw: pd.DataFrame) -> np.ndarray:
        """Transforms raw transaction DataFrame into scaled feature matrix X."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted before calling transform()!")

        df_eng = self._extract_engineered_features(df_raw)

        # Numerical transform
        num_data = df_eng[NUMERICAL_FEATURES].fillna(0.0)
        num_scaled = self.scaler.transform(num_data)

        # Boolean transform (as float)
        bool_data = df_eng[BOOLEAN_FEATURES].fillna(0).astype(float).values

        # Categorical transform
        cat_data = df_eng[CATEGORICAL_FEATURES].fillna("Unknown")
        cat_encoded = self.encoder.transform(cat_data)

        # Stack columns
        X = np.hstack([num_scaled, bool_data, cat_encoded])
        return X

    def fit_transform(self, df_raw: pd.DataFrame) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(df_raw).transform(df_raw)
