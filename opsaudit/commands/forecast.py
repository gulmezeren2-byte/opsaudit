"""opsaudit forecast backtest - five baselines, rolling origin, FVA verdict."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..core import DataError, honesty, read_csv

REQUIRED = ["sku", "month", "qty"]
SEASON = 12

SCHEMA = {
    "input": "monthly demand CSV (one row per sku per month)",
    "required_columns": {
        "sku": "text",
        "month": "month start date (e.g. 2026-01-01)",
        "qty": "numeric demand",
    },
    "notes": f"SKUs need at least horizon+{SEASON} months of history; shorter SKUs are excluded and reported in honesty.dropped",
}


def _ses(hist: np.ndarray, alpha: float) -> float:
    level = hist[0]
    for x in hist[1:]:
        level = alpha * x + (1 - alpha) * level
    return float(level)


def f_naive(h: np.ndarray) -> float:
    return float(h[-1])


def f_snaive(h: np.ndarray) -> float:
    return float(h[-SEASON]) if len(h) >= SEASON else float(h[-1])


def f_ma3(h: np.ndarray) -> float:
    return float(h[-3:].mean())


def f_ses(h: np.ndarray) -> float:
    best_a, best_err = 0.3, np.inf
    for a in (0.1, 0.2, 0.3, 0.4, 0.5):
        level, err = h[0], 0.0
        for x in h[1:]:
            err += abs(x - level)
            level = a * x + (1 - a) * level
        if err < best_err:
            best_a, best_err = a, err
    return _ses(h, best_a)


def f_seasonal_ses(h: np.ndarray) -> float:
    n = len(h)
    if n < 2 * SEASON:
        return f_ses(h)
    idx_month = np.arange(n) % SEASON
    overall = h.mean() if h.mean() > 0 else 1.0
    idx = np.array([
        h[idx_month == m].mean() / overall if h[idx_month == m].mean() > 0 else 1.0
        for m in range(SEASON)
    ])
    idx = np.where(idx <= 0, 1.0, idx)
    return float(max(0.0, _ses(h / idx[idx_month], 0.3) * idx[n % SEASON]))


MODELS = {
    "naive": f_naive,
    "seasonal_naive": f_snaive,
    "ma3": f_ma3,
    "ses": f_ses,
    "seasonal_ses": f_seasonal_ses,
}


def run(args) -> tuple[str, dict, dict]:
    df = read_csv(args.csv, REQUIRED, ("month",), schema_name="forecast.backtest")
    rows_in = len(df)
    horizon = int(args.horizon)
    min_hist = horizon + SEASON

    dropped: list[dict] = []
    bad_qty = pd.to_numeric(df.qty, errors="coerce").isna()
    if bad_qty.any():
        dropped.append({"rows": int(bad_qty.sum()), "reason": "non-numeric qty - excluded"})
        df = df[~bad_qty]
    df["qty"] = df.qty.astype(float)

    lengths = df.groupby("sku").month.nunique()
    short = lengths[lengths < min_hist]
    if len(short):
        n_rows = int(df.sku.isin(short.index).sum())
        dropped.append({
            "rows": n_rows,
            "reason": f"{len(short)} SKUs with fewer than {min_hist} months of history - excluded from the backtest",
        })
        df = df[~df.sku.isin(short.index)]
    if df.empty:
        raise DataError("no SKUs with enough history to backtest", hint=f"need at least {min_hist} months per SKU")

    records = []
    for sku, g in df.groupby("sku"):
        y = g.sort_values("month").qty.to_numpy()
        n = len(y)
        for origin in range(n - horizon, n):
            hist, actual = y[:origin], y[origin]
            for name, fn in MODELS.items():
                records.append((name, actual, max(0.0, fn(hist))))
    bt = pd.DataFrame(records, columns=["model", "actual", "forecast"])

    def scores(g: pd.DataFrame) -> pd.Series:
        err = g.forecast - g.actual
        nz = g.actual > 0
        return pd.Series({
            "wmape_pct": round(float(err.abs().sum() / g.actual.sum() * 100), 1),
            "bias_pct": round(float(err.sum() / g.actual.sum() * 100), 1),
            "mape_nonzero_pct": round(float((err[nz].abs() / g.actual[nz]).mean() * 100), 1),
            "zero_actual_forecasts_dropped_by_mape": int((~nz).sum()),
        })

    m = bt.groupby("model").apply(scores, include_groups=False).sort_values("wmape_pct")
    naive_wmape = float(m.loc["naive", "wmape_pct"])
    best = m.index[0]

    result = {
        "skus_scored": int(df.sku.nunique()),
        "forecasts_scored": int(len(bt)),
        "scoreboard": [
            {"model": idx, **{k: (int(v) if k.startswith("zero") else float(v)) for k, v in row.items()}}
            for idx, row in m.iterrows()
        ],
        "naive_wmape_pct": naive_wmape,
        "best_model": str(best),
        "fva_vs_naive_pts": {
            str(idx): round(naive_wmape - float(row.wmape_pct), 1) for idx, row in m.iterrows() if idx != "naive"
        },
        "verdict": (
            f"best baseline ({best}) adds {round(naive_wmape - float(m.iloc[0].wmape_pct), 1)} WMAPE points over naive"
            if best != "naive"
            else "no baseline beats naive - forecasting effort is currently subtracting value"
        ),
    }

    h = honesty(
        rows_in=rows_in,
        rows_used=int(len(df)),
        dropped=dropped,
        definitions={
            "backtest": f"rolling origin, expanding window, one-month-ahead, last {horizon} months",
            "wmape": "sum(|error|) / sum(actual), zeros included",
            "mape": "plain mean of |error|/actual over nonzero-actual months ONLY - zero months silently drop, which is why WMAPE leads",
            "fva": "naive WMAPE minus model WMAPE (positive = value added)",
        },
        not_shown=[
            "intermittent-demand methods (Croston/SBA) - volatile SKUs may need them",
            "a forecastability ceiling per SKU (how much accuracy is achievable)",
            "your production forecast's timestamps (hindsight-leak check requires them)",
        ],
    )
    return "forecast.backtest", result, h
