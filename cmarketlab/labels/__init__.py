"""Targets for evaluation, built ex post from future prices: swing pivots, forward outcomes, cycle phases.
Never use these as inputs to a signal."""
from .cycles import cycle_targets, forward_outcomes, pivot_context, zigzag

__all__ = ["cycle_targets", "forward_outcomes", "pivot_context", "zigzag"]
