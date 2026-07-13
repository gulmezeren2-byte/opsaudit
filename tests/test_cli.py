"""End-to-end CLI tests: the agent contract, the honesty block, the numbers."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "data"


def run(*args: str):
    return subprocess.run(
        [sys.executable, "-m", "opsaudit", *args],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )


def run_json(*args: str) -> dict:
    proc = run(*args)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)  # stdout must be pure JSON


def assert_contract(payload: dict, command: str):
    assert payload["tool"] == "opsaudit"
    assert payload["command"] == command
    h = payload["honesty"]
    assert h["rows_in"] >= h["rows_used"] > 0
    assert isinstance(h["dropped"], list)
    assert isinstance(h["definitions"], dict) and h["definitions"]
    assert isinstance(h["not_shown"], list) and h["not_shown"]


def test_help_is_clean():
    proc = run("--help")
    assert proc.returncode == 0
    assert "honesty" in proc.stdout


def test_schema_command():
    payload = json.loads(run("schema", "otif.score").stdout)
    assert "required_columns" in payload["schema"]


def test_otif_score():
    p = run_json("otif", "score", str(DATA / "orders.csv"), "--by", "carrier")
    assert_contract(p, "otif.score")
    ladder = p["result"]["ladder"]
    shares = [r["share_pct"] for r in ladder]
    assert shares == sorted(shares, reverse=True), "ladder must be monotone non-increasing"
    assert len(ladder) == 5
    assert "Carrier B" in p["result"]["by"]
    assert any("cancelled" in d["reason"] for d in p["honesty"]["dropped"])


def test_forecast_backtest():
    p = run_json("forecast", "backtest", str(DATA / "demand.csv"))
    assert_contract(p, "forecast.backtest")
    board = p["result"]["scoreboard"]
    assert {m["model"] for m in board} == {"naive", "seasonal_naive", "ma3", "ses", "seasonal_ses"}
    wmapes = [m["wmape_pct"] for m in board]
    assert wmapes == sorted(wmapes), "scoreboard must be sorted by WMAPE"
    assert "mape" in p["honesty"]["definitions"]


def test_abc_segment():
    p = run_json("abc", "segment", str(DATA / "demand.csv"))
    assert_contract(p, "abc.segment")
    nb = p["result"]["nine_box"]
    total_skus = sum(nb[a][x]["skus"] for a in "ABC" for x in "XYZ")
    assert total_skus == p["result"]["skus"] == 12
    total_share = sum(nb[a][x]["value_share_pct"] for a in "ABC" for x in "XYZ")
    assert abs(total_share - 100.0) < 0.5


def test_pareto_rank_with_hygiene():
    p = run_json("pareto", "rank", str(DATA / "downtime.csv"), "--category", "reason", "--weight", "minutes")
    assert_contract(p, "pareto.rank")
    items = p["result"]["items"]
    assert items[0]["category"].strip().lower() == "setup", "variant labels must merge into the top category"
    assert items[-1]["cumulative_pct"] <= 100.1
    assert p["result"]["unit_of_measure"] == "minutes"


def test_data_error_is_json():
    proc = run("otif", "score", "does-not-exist.csv")
    assert proc.returncode == 1
    err = json.loads(proc.stdout)
    assert "error" in err and "file not found" in err["error"]["message"]


def test_missing_columns_hint():
    proc = run("otif", "score", str(DATA / "demand.csv"))
    assert proc.returncode == 1
    err = json.loads(proc.stdout)
    assert "missing required columns" in err["error"]["message"]
    assert "schema" in err["error"]["hint"]
