"""Statistical tests for trajectory comparison."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy import stats


_SIGNIFICANCE = 0.05


@dataclass
class StatTest:
    """Result of a statistical comparison between two trajectory metrics."""
    metric: str             # "rmsd" | "rmsf" | "rg"
    mean_a: float
    mean_b: float
    delta: float            # mean_b - mean_a
    test_name: str          # e.g. "Welch's t-test" | "KS"
    pvalue: float
    significant: bool       # True if pvalue < 0.05


def ks_test(metric: str, a: Sequence[float], b: Sequence[float]) -> StatTest:
    """Two-sample Kolmogorov–Smirnov test on the two value sequences."""
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    result = stats.ks_2samp(a_arr, b_arr)
    mean_a = float(a_arr.mean())
    mean_b = float(b_arr.mean())
    return StatTest(
        metric=metric,
        mean_a=mean_a,
        mean_b=mean_b,
        delta=mean_b - mean_a,
        test_name="KS",
        pvalue=float(result.pvalue),
        significant=bool(result.pvalue < _SIGNIFICANCE),
    )


def welch_test(metric: str, a: Sequence[float], b: Sequence[float]) -> StatTest:
    """Welch's t-test (unequal variances) on the two value sequences."""
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    result = stats.ttest_ind(a_arr, b_arr, equal_var=False)
    mean_a = float(a_arr.mean())
    mean_b = float(b_arr.mean())
    return StatTest(
        metric=metric,
        mean_a=mean_a,
        mean_b=mean_b,
        delta=mean_b - mean_a,
        test_name="Welch's t-test",
        pvalue=float(result.pvalue),
        significant=bool(result.pvalue < _SIGNIFICANCE),
    )
