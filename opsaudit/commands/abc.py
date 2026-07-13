"""opsaudit abc segment - ABC-XYZ classification with explicit thresholds."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..core import DataError, honesty, read_csv

REQUIRED = ["sku", "month", "qty"]

SCHEMA = {
    "input": "monthly demand CSV (one row per sku per month)",
    "required_columns": {
        "sku": "text",
        "month": "month start date",
        "qty": "numeric demand",
    },
    "optional_columns": {"unit_price": "numeric; without it ABC ranks by volume, not value (flagged in honesty)"},
}


def run(args) -> tuple[str, dict, dict]:
    df = read_csv(args.csv, REQUIRED, ("month",), schema_name="abc.segment")
    rows_in = len(df)
    dropped: list[dict] = []

    bad_qty = pd.to_numeric(df.qty, errors="coerce").isna()
    if bad_qty.any():
        dropped.append({"rows": int(bad_qty.sum()), "reason": "non-numeric qty - excluded"})
        df = df[~bad_qty]
    df["qty"] = df.qty.astype(float)
    if df.empty:
        raise DataError("no usable rows after validation")

    has_price = "unit_price" in df.columns
    months = df.month.nunique()

    g = df.groupby("sku").agg(total_qty=("qty", "sum"), mean_qty=("qty", "mean"), std_qty=("qty", "std"))
    g["std_qty"] = g.std_qty.fillna(0.0)
    if has_price:
        price = df.groupby("sku").unit_price.first()
        g["annual_value"] = g.total_qty * price * (12 / months)
    else:
        g["annual_value"] = g.total_qty * (12 / months)

    g = g.sort_values("annual_value", ascending=False)
    share = g.annual_value.cumsum() / g.annual_value.sum()
    g["abc"] = np.where(share <= args.value_a, "A", np.where(share <= args.value_b, "B", "C"))
    g["cv"] = np.where(g.mean_qty > 0, g.std_qty / g.mean_qty, np.inf)
    g["xyz"] = np.where(g.cv < args.cv_x, "X", np.where(g.cv < args.cv_z, "Y", "Z"))

    nine_box = {
        a: {
            x: {
                "skus": int(((g.abc == a) & (g.xyz == x)).sum()),
                "value_share_pct": round(float(g.loc[(g.abc == a) & (g.xyz == x), "annual_value"].sum() / g.annual_value.sum() * 100), 1),
            }
            for x in ("X", "Y", "Z")
        }
        for a in ("A", "B", "C")
    }

    classes = [
        {
            "sku": str(sku),
            "abc": row.abc,
            "xyz": row.xyz,
            "annual_value": round(float(row.annual_value), 1),
            "cv": round(float(row.cv), 3) if np.isfinite(row.cv) else None,
        }
        for sku, row in g.iterrows()
    ]

    n_a = int((g.abc == "A").sum())
    result = {
        "skus": int(len(g)),
        "months_of_history": int(months),
        "a_items": {"count": n_a, "sku_share_pct": round(n_a / len(g) * 100, 1)},
        "nine_box": nine_box,
        "classes": classes,
    }

    h = honesty(
        rows_in=rows_in,
        rows_used=int(len(df)),
        dropped=dropped,
        definitions={
            "abc_basis": "annual consumption value" if has_price else "annual VOLUME - unit_price column missing, value ranking not possible",
            "abc_cut_a": f"cumulative {args.value_a:.0%}",
            "abc_cut_b": f"cumulative {args.value_b:.0%}",
            "xyz_basis": "coefficient of variation of monthly demand",
            "xyz_cuts": f"X < {args.cv_x} <= Y < {args.cv_z} <= Z",
            "annualization": f"scaled from {months} months of history",
        },
        not_shown=[
            "seasonality is not removed before computing CV - strongly seasonal SKUs can land in Y/Z on rhythm alone",
            "CV thresholds are conventions, not laws - check them against the portfolio's natural breaks",
            "policy suitability per cell (see the abc-xyz-inventory project for the 9-box policy map)",
        ]
        + ([] if has_price else ["ABC here ranks by volume; with 10x price spreads, the money ranking WILL differ"]),
    )
    return "abc.segment", result, h
