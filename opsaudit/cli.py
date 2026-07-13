"""opsaudit CLI - built for AI agents and pipelines.

The agent contract:
1. JSON-only stdout (results and data errors alike; usage errors go to stderr, exit 2)
2. Self-documenting: --help everywhere, `opsaudit schema <command>` prints input schemas
3. Never interactive - no prompts, ever
4. Stateless - same input, same output; nothing written anywhere
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .commands import abc as abc_cmd
from .commands import forecast as forecast_cmd
from .commands import otif as otif_cmd
from .commands import pareto as pareto_cmd
from .core import DataError, emit, fail

SCHEMAS = {
    "otif.score": otif_cmd.SCHEMA,
    "forecast.backtest": forecast_cmd.SCHEMA,
    "abc.segment": abc_cmd.SCHEMA,
    "pareto.rank": pareto_cmd.SCHEMA,
}

EPILOG = """examples:
  opsaudit otif score orders.csv --by carrier
  opsaudit forecast backtest demand.csv --horizon 6
  opsaudit abc segment demand.csv
  opsaudit pareto rank downtime.csv --category reason --weight minutes --exposure machine_hours
  opsaudit schema otif.score

every result includes an "honesty" block: rows in/used/dropped (with reasons),
every definition the numbers depend on, and what the output does NOT show.
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="opsaudit",
        description="Operations analytics that audits its own numbers. JSON-only output, built for AI agents and pipelines.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version", version=f"opsaudit {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    # otif score
    p_otif = sub.add_parser("otif", help="delivery performance").add_subparsers(dest="action", required=True)
    s = p_otif.add_parser(
        "score",
        help="compute the OTIF metric ladder (tolerant to strict) with driver breakdown",
        epilog='example: opsaudit otif score orders.csv --by carrier\nschema:  opsaudit schema otif.score',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    s.add_argument("csv", help="order-level CSV (see schema otif.score)")
    s.add_argument("--tolerance", type=int, default=3, help="tolerance days for the reported rung (default 3)")
    s.add_argument("--by", help="segment column for the OTIF breakdown (e.g. carrier, region)")
    s.set_defaults(fn=otif_cmd.run)

    # forecast backtest
    p_fc = sub.add_parser("forecast", help="forecast quality").add_subparsers(dest="action", required=True)
    s = p_fc.add_parser(
        "backtest",
        help="rolling-origin backtest of five baselines; WMAPE, bias and FVA vs naive",
        epilog='example: opsaudit forecast backtest demand.csv --horizon 6\nschema:  opsaudit schema forecast.backtest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    s.add_argument("csv", help="monthly demand CSV (see schema forecast.backtest)")
    s.add_argument("--horizon", type=int, default=6, help="months to score, one-step-ahead (default 6)")
    s.set_defaults(fn=forecast_cmd.run)

    # abc segment
    p_abc = sub.add_parser("abc", help="portfolio segmentation").add_subparsers(dest="action", required=True)
    s = p_abc.add_parser(
        "segment",
        help="ABC-XYZ classification with a 9-box summary and explicit thresholds",
        epilog='example: opsaudit abc segment demand.csv --cv-x 0.5 --cv-z 1.0\nschema:  opsaudit schema abc.segment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    s.add_argument("csv", help="monthly demand CSV (see schema abc.segment)")
    s.add_argument("--value-a", type=float, default=0.80, help="cumulative value share for class A (default 0.80)")
    s.add_argument("--value-b", type=float, default=0.95, help="cumulative value share for class B (default 0.95)")
    s.add_argument("--cv-x", type=float, default=0.5, help="CV upper bound for class X (default 0.5)")
    s.add_argument("--cv-z", type=float, default=1.0, help="CV lower bound for class Z (default 1.0)")
    s.set_defaults(fn=abc_cmd.run)

    # pareto rank
    p_par = sub.add_parser("pareto", help="root-cause ranking").add_subparsers(dest="action", required=True)
    s = p_par.add_parser(
        "rank",
        help="decision-grade Pareto: category hygiene, optional weight and exposure normalization",
        epilog='example: opsaudit pareto rank downtime.csv --category reason --weight minutes\nschema:  opsaudit schema pareto.rank',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    s.add_argument("csv", help="event-level CSV (see schema pareto.rank)")
    s.add_argument("--category", required=True, help="column to rank")
    s.add_argument("--weight", help="numeric impact column (minutes, cost); default: row count")
    s.add_argument("--exposure", help="numeric exposure column for normalization (machine_hours, orders)")
    s.add_argument("--top", type=int, default=10, help="items to return (default 10)")
    s.set_defaults(fn=pareto_cmd.run)

    # schema
    s = sub.add_parser("schema", help="print the expected input schema for a command, as JSON")
    s.add_argument("name", choices=sorted(SCHEMAS), help="command name, e.g. otif.score")
    s.set_defaults(fn=None)

    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "schema":
        print(json.dumps({"command": args.name, "schema": SCHEMAS[args.name]}, ensure_ascii=False, indent=2))
        return
    try:
        command, result, honesty_block = args.fn(args)
    except DataError as e:
        fail(str(e), hint=e.hint, code=1)
        return
    except Exception as e:  # never a traceback on stdout - keep the contract
        fail(f"internal error: {type(e).__name__}: {e}", hint="please report this at github.com/gulmezeren2-byte/opsaudit/issues", code=3)
        return
    emit(command, result, honesty_block)


if __name__ == "__main__":
    main()
