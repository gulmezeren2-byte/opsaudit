"""opsaudit pareto rank - a decision-grade Pareto with category hygiene."""

from __future__ import annotations

import pandas as pd

from ..core import DataError, honesty, read_csv

SCHEMA = {
    "input": "event/record-level CSV (downtime events, defects, complaints, delays...)",
    "required_columns": {"<--category COL>": "the column to rank (passed via --category)"},
    "optional_columns": {
        "<--weight COL>": "numeric impact per row (minutes, cost); without it, rows are counted",
        "<--exposure COL>": "numeric exposure base per row (machine-hours, orders) - enables normalized comparison",
    },
}


def run(args) -> tuple[str, dict, dict]:
    df = read_csv(args.csv, [args.category], schema_name="pareto.rank")
    rows_in = len(df)
    dropped: list[dict] = []
    warnings: list[str] = []

    null_cat = df[args.category].isna() | (df[args.category].astype(str).str.strip() == "")
    if null_cat.any():
        dropped.append({"rows": int(null_cat.sum()), "reason": "empty category - excluded"})
        df = df[~null_cat]
    if df.empty:
        raise DataError("no rows with a category value")

    # category hygiene: merge case/whitespace variants, report the merges
    raw = df[args.category].astype(str)
    canon = raw.str.strip().str.casefold()
    mapping = raw.groupby(canon).agg(lambda s: s.value_counts().idxmax())
    merges = int((mapping.groupby(level=0).size() > 0).sum())
    variants_merged = int(raw.nunique() - canon.nunique())
    df = df.assign(_cat=canon.map(mapping))
    if variants_merged:
        warnings.append(f"{variants_merged} category label variants merged (case/whitespace) - check honesty.definitions")

    if args.weight:
        if args.weight not in df.columns:
            raise DataError(f"--weight column not found: {args.weight}")
        w = pd.to_numeric(df[args.weight], errors="coerce")
        bad_w = w.isna()
        if bad_w.any():
            dropped.append({"rows": int(bad_w.sum()), "reason": f"non-numeric {args.weight} - excluded"})
            df, w = df[~bad_w], w[~bad_w]
        impact = df.assign(_w=w).groupby("_cat")._w.sum()
        unit = args.weight
    else:
        impact = df.groupby("_cat").size().astype(float)
        unit = "count"
        warnings.append("ranking by COUNT of rows - if one category costs 10x more per event, pass --weight")

    if args.exposure:
        if args.exposure not in df.columns:
            raise DataError(f"--exposure column not found: {args.exposure}")
        exp = pd.to_numeric(df[args.exposure], errors="coerce")
        exposure_base = df.assign(_e=exp).groupby("_cat")._e.sum()
        impact = impact / exposure_base.replace(0, pd.NA)
        impact = impact.dropna()
        unit = f"{unit} per {args.exposure}"

    impact = impact.sort_values(ascending=False)
    total = float(impact.sum())
    items = []
    cum = 0.0
    for cat, val in impact.head(args.top).items():
        cum += float(val)
        items.append({
            "category": str(cat),
            "impact": round(float(val), 2),
            "share_pct": round(float(val) / total * 100, 1),
            "cumulative_pct": round(cum / total * 100, 1),
        })
    other = total - cum
    other_pct = round(other / total * 100, 1) if total else 0.0

    named_other = impact[impact.index.astype(str).str.casefold().isin(("other", "misc", "miscellaneous", "diğer", "diger"))].sum()
    if total and named_other / total > 0.15:
        warnings.append(f"'Other/Diğer'-type categories carry {round(named_other/total*100,1)}% of impact (>15%) - the categorization needs splitting before this ranking is trusted")

    result = {
        "unit_of_measure": unit,
        "categories_total": int(len(impact)),
        "items": items,
        "beyond_top_share_pct": other_pct,
        "warnings": warnings,
    }

    h = honesty(
        rows_in=rows_in,
        rows_used=int(len(df)),
        dropped=dropped,
        definitions={
            "unit_of_measure": unit,
            "exposure_base": args.exposure or "none (raw totals - do not compare entities with different volumes)",
            "category_normalization": "trimmed + case-folded; most frequent original spelling kept",
            "top_n": args.top,
        },
        not_shown=[
            "stability across periods - a ranking from one window is an anecdote; rerun on a second period before investing",
            "sub-causes inside the top category - go one level deeper before acting",
            "semantic duplicates beyond case/whitespace (e.g. 'sensor fault' vs 'sensor failure') - merge manually",
        ],
    )
    return "pareto.rank", result, h
