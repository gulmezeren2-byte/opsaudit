"""opsaudit otif score - the OTIF metric ladder with a self-audit."""

from __future__ import annotations

from ..core import DataError, honesty, pct, read_csv

REQUIRED = [
    "order_id",
    "requested_delivery_date",
    "promised_delivery_date",
    "actual_delivery_date",
    "lines_total",
    "lines_delivered_complete",
    "status",
]
DATES = ("requested_delivery_date", "promised_delivery_date", "actual_delivery_date")

SCHEMA = {
    "input": "order-level CSV",
    "required_columns": {
        "order_id": "text, unique",
        "requested_delivery_date": "date the customer asked for",
        "promised_delivery_date": "date that was confirmed",
        "actual_delivery_date": "date delivered (empty if cancelled)",
        "lines_total": "int, order lines",
        "lines_delivered_complete": "int, lines delivered complete",
        "status": "'delivered' or 'cancelled'",
    },
    "optional_columns": {"any segment column": "use with --by (e.g. carrier, region)"},
}


def run(args) -> tuple[str, dict, dict]:
    df = read_csv(args.csv, REQUIRED, DATES, schema_name="otif.score")
    rows_in = len(df)
    dropped: list[dict] = []

    dupes = int(df.duplicated().sum())
    if dupes:
        dropped.append({"rows": 0, "reason": f"{dupes} fully duplicated rows detected (kept in the analysis - verify upstream)"})

    cancelled = df[df.status == "cancelled"]
    delivered = df[df.status == "delivered"].copy()

    bad_dates = delivered[DATES[0]].isna() | delivered[DATES[1]].isna() | delivered[DATES[2]].isna()
    if bad_dates.any():
        dropped.append({"rows": int(bad_dates.sum()), "reason": "delivered orders with unparseable/missing dates - excluded"})
        delivered = delivered[~bad_dates]
    if delivered.empty:
        raise DataError("no usable delivered orders after validation")

    dropped.append({"rows": int(len(cancelled)), "reason": "cancelled orders - excluded from rungs 1-4, included in rung 5"})

    tol = int(args.tolerance)
    late_prom = (delivered.actual_delivery_date - delivered.promised_delivery_date).dt.days
    late_req = (delivered.actual_delivery_date - delivered.requested_delivery_date).dt.days
    in_full = delivered.lines_delivered_complete >= delivered.lines_total

    n_del, n_all = len(delivered), len(delivered) + len(cancelled)
    m1 = pct((late_prom <= tol).mean())
    m2 = pct((late_prom <= 0).mean())
    m3 = pct((late_req <= 0).mean())
    m4 = pct(((late_req <= 0) & in_full).mean())
    m5 = round(((late_req <= 0) & in_full).sum() / n_all * 100, 1)

    ladder = [
        {"rung": 1, "definition": f"promised date, +{tol}-day tolerance", "share_pct": m1, "cause_of_drop": None},
        {"rung": 2, "definition": "promised date, strict", "share_pct": m2, "cause_of_drop": "tolerance window removed"},
        {"rung": 3, "definition": "requested date, strict", "share_pct": m3, "cause_of_drop": "promise padding vs customer request exposed"},
        {"rung": 4, "definition": "OTIF: requested date + order complete", "share_pct": m4, "cause_of_drop": "partial shipments counted"},
        {"rung": 5, "definition": "OTIF incl. cancellations in denominator", "share_pct": m5, "cause_of_drop": "cancelled orders stop hiding"},
    ]
    for i in range(1, len(ladder)):
        ladder[i]["delta_pts"] = round(ladder[i]["share_pct"] - ladder[i - 1]["share_pct"], 1)

    result: dict = {
        "orders_delivered": n_del,
        "orders_cancelled": int(len(cancelled)),
        "ladder": ladder,
        "reported_vs_otif_gap_pts": round(m1 - m4, 1),
        "avg_promise_padding_days": round(float((delivered.promised_delivery_date - delivered.requested_delivery_date).dt.days.mean()), 2),
        "tail": {
            "avg_days_vs_requested": round(float(late_req.mean()), 2),
            "pct_4plus_days_late": pct((late_req > 3).mean()),
        },
    }

    if args.by:
        if args.by not in df.columns:
            raise DataError(f"--by column not found: {args.by}")
        seg = (
            delivered.assign(otif=((late_req <= 0) & in_full))
            .groupby(args.by)["otif"]
            .agg(otif_pct=lambda s: round(s.mean() * 100, 1), orders="size")
        )
        result["by"] = {str(k): {"otif_pct": float(v.otif_pct), "orders": int(v.orders)} for k, v in seg.iterrows()}
        result["segment_spread_pts"] = round(float(seg.otif_pct.max() - seg.otif_pct.min()), 1)

    h = honesty(
        rows_in=rows_in,
        rows_used=n_del,
        dropped=dropped,
        definitions={
            "anchor_rungs_1_2": "promised_delivery_date",
            "anchor_rungs_3_5": "requested_delivery_date",
            "tolerance_days_rung_1": tol,
            "in_full_level": "order (all lines complete)",
            "cancellations": "excluded from rungs 1-4, in denominator of rung 5",
        },
        not_shown=[
            "line-level fill rate (a complementary metric, not computed here)",
            "whether requested dates were renegotiated after order entry",
            "root causes beyond the optional --by segmentation",
        ],
    )
    return "otif.score", result, h
