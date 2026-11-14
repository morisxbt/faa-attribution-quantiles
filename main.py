#!/usr/bin/env python3
"""Forecast bounded Polymarket prices with a calibrated, asymmetric step spread."""

import json
import math
import os
from pathlib import Path


QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)
VOLATILITY_FLOOR = 0.0005
INNER_WIDTH = 0.4
OUTER_WIDTH = 1.3
DOWNSIDE_MULTIPLIER = 1.5
HORIZON_EXPONENT = 0.4


def price(value: float) -> float:
    """Clamp and round a forecast to the contest's six decimal places."""
    return round(min(1.0, max(0.0, value)), 6)


def population_std(changes: list[float]) -> float:
    if len(changes) < 2:
        return 0.0
    mean = sum(changes) / len(changes)
    variance = sum((change - mean) ** 2 for change in changes) / len(changes)
    return math.sqrt(variance)


def spread_scale(prices: list[float]) -> float:
    """Blend recent volatility and shrink it near the probability boundaries."""
    changes = [b - a for a, b in zip(prices, prices[1:])]
    sigma_120 = population_std(changes[-120:])
    sigma_360 = population_std(changes[-360:])
    level = max(0.1, 2.0 * math.sqrt(max(0.0, prices[-1] * (1.0 - prices[-1]))))
    return max(VOLATILITY_FLOOR, 0.5 * (sigma_120 + sigma_360) * level)


def forecast(prices: list[float], horizon: int) -> list[list[float]]:
    if not prices:
        raise ValueError("market has no prices")
    center = prices[-1]
    scale = spread_scale(prices)
    rows: list[list[float]] = []
    for minute in range(1, horizon + 1):
        outer = OUTER_WIDTH * scale * minute**HORIZON_EXPONENT
        inner = INNER_WIDTH * outer
        rows.append(
            [
                price(center - DOWNSIDE_MULTIPLIER * outer),
                price(center - DOWNSIDE_MULTIPLIER * inner),
                price(center),
                price(center + inner),
                price(center + outer),
            ]
        )
    return rows


def main() -> None:
    input_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    for input_path in sorted(input_dir.glob("*.in"), key=lambda path: path.name):
        case = json.loads(input_path.read_text(encoding="utf-8"))
        if tuple(case["quantiles"]) != QUANTILES:
            raise ValueError(f"unexpected quantile levels in {input_path.name}")
        horizon = case["horizon_minutes"]
        forecasts = [
            {"id": market["id"], "q": forecast(market["prices"], horizon)}
            for market in case["markets"]
        ]
        payload = json.dumps({"forecasts": forecasts}, separators=(",", ":")) + "\n"
        (output_dir / (input_path.stem + ".out")).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
