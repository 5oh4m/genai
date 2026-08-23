"""
Statistical Realism and Schema Quality Validation Metrics.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from scipy import stats

from red_team.config import PUBLIC_COLUMNS, ANSWER_KEY_COLUMNS, LABEL_NORMAL


def validate_zero_leakage(df_public: pd.DataFrame) -> Dict[str, Any]:
    """
    Verifies that the public blind transaction dataset contains zero private labels
    or metadata columns.
    """
    forbidden_keys = [
        "ground_truth_label",
        "attack_subtype",
        "stealth_level",
        "evasion_technique",
        "evasion_parameters",
        "is_fraud",
        "label",
    ]

    leaked = [col for col in forbidden_keys if col in df_public.columns]
    
    return {
        "passed": len(leaked) == 0,
        "leaked_columns": leaked,
        "public_column_count": len(df_public.columns),
        "expected_column_count": len(PUBLIC_COLUMNS),
    }


def compute_statistical_realism(df_public: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes statistical moments and behavioral realism scores on the public dataset.
    """
    amounts = df_public["amount"].values
    
    # 1. Amount moments
    mean_amt = float(np.mean(amounts))
    median_amt = float(np.median(amounts))
    std_amt = float(np.std(amounts))
    skewness = float(stats.skew(amounts))
    kurtosis = float(stats.kurtosis(amounts))
    
    # Check log-normal fit (log of positive amounts)
    log_amounts = np.log(amounts[amounts > 0])
    _, log_shapiro_p = stats.normaltest(log_amounts)
    
    # 2. Hourly distribution check (percentage of txns during night hours 01:00 - 05:00)
    timestamps = pd.to_datetime(df_public["timestamp"])
    night_ratio = float((timestamps.dt.hour.isin([1, 2, 3, 4, 5])).mean())

    # 3. Channel & Device breakdown
    channel_dist = df_public["channel"].value_counts(normalize=True).round(3).to_dict()
    device_dist = df_public["device_type"].value_counts(normalize=True).round(3).to_dict()

    realism_report = {
        "total_transactions": len(df_public),
        "amount_moments": {
            "mean": round(mean_amt, 2),
            "median": round(median_amt, 2),
            "std": round(std_amt, 2),
            "skewness": round(skewness, 2),
            "kurtosis": round(kurtosis, 2),
        },
        "night_hours_activity_ratio": round(night_ratio, 4),
        "channel_distribution": channel_dist,
        "device_distribution": device_dist,
        "is_realistically_skewed": skewness > 1.0,
        "is_diurnal_suppressed": night_ratio < 0.12,
    }

    return realism_report
