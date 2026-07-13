"""Shared plumbing: the JSON contract, the honesty block, checked CSV loading."""

from __future__ import annotations

import json
import sys
from typing import Any

import numpy as np
import pandas as pd


class DataError(Exception):
    """User-facing data problem. Rendered as a JSON error on stdout, exit 1."""

    def __init__(self, message: str, hint: str | None = None):
        super().__init__(message)
        self.hint = hint


def read_csv(
    path: str,
    required: list[str],
    date_cols: tuple[str, ...] = (),
    schema_name: str | None = None,
) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise DataError(f"file not found: {path}")
    except Exception as exc:  # malformed CSV, encoding, etc.
        raise DataError(f"could not parse CSV: {exc}")
    missing = [c for c in required if c not in df.columns]
    if missing:
        hint = f"run 'opsaudit schema {schema_name}' for the expected input" if schema_name else None
        raise DataError(f"missing required columns: {missing}", hint=hint)
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def honesty(
    rows_in: int,
    rows_used: int,
    dropped: list[dict[str, Any]],
    definitions: dict[str, Any],
    not_shown: list[str],
) -> dict[str, Any]:
    """The mandatory self-audit attached to every result.

    dropped: [{"rows": int, "reason": str}, ...] - every row that left the
    analysis, with why. definitions: every anchor/threshold/denominator choice
    the numbers depend on. not_shown: what this output deliberately does not
    claim - the section that keeps readers from over-reading the result.
    """
    return {
        "rows_in": int(rows_in),
        "rows_used": int(rows_used),
        "dropped": dropped,
        "definitions": definitions,
        "not_shown": not_shown,
    }


def _json_default(o: Any):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (pd.Timestamp,)):
        return o.date().isoformat()
    return str(o)


def emit(command: str, result: dict[str, Any], honesty_block: dict[str, Any]) -> None:
    from . import __version__

    payload = {
        "tool": "opsaudit",
        "version": __version__,
        "command": command,
        "result": result,
        "honesty": honesty_block,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))


def fail(message: str, hint: str | None = None, code: int = 1) -> None:
    err: dict[str, Any] = {"message": message}
    if hint:
        err["hint"] = hint
    print(json.dumps({"error": err}, ensure_ascii=False, indent=2))
    sys.exit(code)


def pct(x: float) -> float:
    return round(float(x) * 100, 1)
