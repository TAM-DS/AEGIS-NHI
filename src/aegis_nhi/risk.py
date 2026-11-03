"""Seeded FAIR-inspired annual loss-frequency/loss-magnitude scenario model.

This is not a validated FAIR assessment, an observed bank loss, or actuarial advice.
"""

from __future__ import annotations

import math
import random
from typing import Any


def _poisson(rng: random.Random, annual_rate: float) -> int:
    if annual_rate == 0:
        return 0
    threshold = math.exp(-annual_rate)
    product, count = 1.0, 0
    while product > threshold:
        count += 1
        product *= rng.random()
    return count - 1


def _percentile(sorted_values: list[float], quantile: float) -> float:
    point = (len(sorted_values) - 1) * quantile
    lower = math.floor(point)
    upper = math.ceil(point)
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (point - lower)


def quantify_annual_loss(
    config: dict[str, Any],
    *,
    frequency_multiplier: float = 1.0,
    hypothetical_control_effectiveness: float = 0.0,
) -> dict[str, Any]:
    """Return reproducible yearly modeled-loss quantiles, not confidence intervals.

    A separate hypothetical control-effectiveness adjustment is a what-if input.
    """
    required = (
        "annual_event_frequency",
        "loss_min_usd",
        "loss_mode_usd",
        "loss_max_usd",
        "simulations",
        "seed",
    )
    if any(key not in config for key in required):
        raise ValueError("Incomplete annual loss model")
    rate = float(config["annual_event_frequency"])
    low, mode, high = (
        float(config["loss_min_usd"]),
        float(config["loss_mode_usd"]),
        float(config["loss_max_usd"]),
    )
    multiplier = float(frequency_multiplier)
    effectiveness = float(hypothetical_control_effectiveness)
    numeric = (rate, low, mode, high, multiplier, effectiveness)
    if not all(math.isfinite(v) for v in numeric):
        raise ValueError("Scenario parameters must be finite")
    if not 0 <= low <= mode <= high or rate < 0 or multiplier < 0:
        raise ValueError("Invalid frequency or loss magnitude assumptions")
    if not 0 <= effectiveness <= 1:
        raise ValueError("Control effectiveness must lie in [0, 1]")
    effective_rate = rate * multiplier * (1.0 - effectiveness)
    if effective_rate > 10:
        raise ValueError("Annual event frequency must be <= 10 for bounded simulation")
    runs = int(config["simulations"])
    if isinstance(config["simulations"], bool) or runs != config["simulations"]:
        raise ValueError("Simulation count must be an integer")
    if not 100 <= runs <= 50000:
        raise ValueError("Simulation count outside bounded range (100..50000)")
    if isinstance(config["seed"], bool) or not isinstance(config["seed"], int):
        raise ValueError("Random seed must be an integer")

    rng = random.Random(config["seed"])
    samples = []
    for _ in range(runs):
        event_count = _poisson(rng, effective_rate)
        samples.append(sum(rng.triangular(low, high, mode) for _ in range(event_count)))
    samples.sort()
    expected = effective_rate * (low + mode + high) / 3.0
    return {
        "basis": "hypothetical_conditional_annual_loss_if_controls_fail",
        "currency": "USD",
        "period": "year",
        "model_version": "seeded-poisson-triangular-v1",
        "annual_event_frequency_assumption": round(effective_rate, 6),
        "baseline_annual_frequency_assumption": rate,
        "frequency_multiplier_assumption": multiplier,
        "hypothetical_control_effectiveness": effectiveness,
        "loss_min_usd": low,
        "loss_mode_usd": mode,
        "loss_max_usd": high,
        "expected_annual_loss_usd": round(expected, 2),
        "simulated_mean_usd": round(sum(samples) / runs, 2),
        "p10_annual_loss_usd": round(_percentile(samples, 0.1), 2),
        "p50_annual_loss_usd": round(_percentile(samples, 0.5), 2),
        "p90_annual_loss_usd": round(_percentile(samples, 0.9), 2),
        "simulations": runs,
        "seed": config["seed"],
        "limitations": (
            "Inputs are synthetic subjective assumptions. P10/P50/P90 are quantiles of "
            "simulated annual outcomes, not statistical confidence intervals. "
            "A denied request does not establish an actual financial loss."
        ),
    }
