"""Statistical evaluation of indicators and signals against targets (AUC, conditional tables, episodes,
autocorrelation-preserving shift tests)."""
from .signals import auc, episodes, feature_tests, pivot_profiles, quantile_table, shift_test

__all__ = ["auc", "episodes", "feature_tests", "pivot_profiles", "quantile_table", "shift_test"]
