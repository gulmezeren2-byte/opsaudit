"""Regenerate the seeded test fixtures in tests/data/. Run from the repo root."""

from __future__ import annotations

import numpy as np
import pandas as pd

RNG = np.random.default_rng(3)


def orders() -> None:
    n = 300
    start = np.datetime64("2026-01-01")
    order_dates = start + RNG.integers(0, 150, n).astype("timedelta64[D]")
    requested = order_dates + RNG.integers(3, 12, n).astype("timedelta64[D]")
    pad = np.where(RNG.random(n) < 0.5, RNG.integers(1, 3, n), 0)
    promised = requested + pad.astype("timedelta64[D]")
    delay = np.clip(np.round(RNG.normal(-1.0, 1.5, n)), -3, 12).astype(int)
    carrier = RNG.choice(["Carrier A", "Carrier B", "Carrier C"], n, p=[0.45, 0.3, 0.25])
    delay = delay + np.where((carrier == "Carrier B") & (RNG.random(n) < 0.35), RNG.integers(1, 5, n), 0)
    actual = promised + delay.astype("timedelta64[D]")
    lines = RNG.integers(1, 7, n)
    complete = lines - np.where(RNG.random(n) < 0.08, 1, 0)
    cancelled = RNG.random(n) < 0.04
    df = pd.DataFrame({
        "order_id": [f"SO-{i:05d}" for i in range(n)],
        "requested_delivery_date": requested,
        "promised_delivery_date": promised,
        "actual_delivery_date": actual.astype("datetime64[D]").astype(object),
        "carrier": carrier,
        "lines_total": lines,
        "lines_delivered_complete": np.where(cancelled, 0, complete),
        "status": np.where(cancelled, "cancelled", "delivered"),
    })
    df.loc[cancelled, "actual_delivery_date"] = None
    df.to_csv("tests/data/orders.csv", index=False)


def demand() -> None:
    months = pd.date_range("2023-07-01", periods=30, freq="MS")
    rows = []
    for i in range(12):
        base = RNG.uniform(50, 400)
        season = 1 + 0.2 * np.sin(2 * np.pi * np.arange(30) / 12 + RNG.uniform(0, 6))
        noise = RNG.normal(1, 0.15, 30)
        qty = np.maximum(0, base * season * noise).round()
        if i >= 9:  # a few intermittent SKUs
            qty = np.where(RNG.random(30) < 0.5, 0, qty * 0.3).round()
        price = round(float(RNG.uniform(10, 120)), 2)
        for m, q in zip(months, qty):
            rows.append((f"SKU-{i+1:02d}", m.date().isoformat(), int(q), price))
    pd.DataFrame(rows, columns=["sku", "month", "qty", "unit_price"]).to_csv(
        "tests/data/demand.csv", index=False
    )


def downtime() -> None:
    reasons = ["Setup", "setup ", "No material", "Breakdown", "Quality stop", "Other"]
    p = [0.28, 0.07, 0.22, 0.2, 0.13, 0.1]
    n = 400
    df = pd.DataFrame({
        "reason": RNG.choice(reasons, n, p=p),
        "minutes": np.round(RNG.gamma(2.0, 15.0, n), 1),
        "machine_hours": np.round(RNG.uniform(6, 9, n), 1),
    })
    df.to_csv("tests/data/downtime.csv", index=False)


if __name__ == "__main__":
    orders()
    demand()
    downtime()
    print("fixtures written to tests/data/")
