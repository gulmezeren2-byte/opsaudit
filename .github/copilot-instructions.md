# Copilot instructions — opsaudit

Agent-facing operations-analytics CLI (Python 3.10+) that computes OTIF, forecast accuracy, ABC-XYZ and Pareto and returns JSON-only stdout where every result carries a mandatory `honesty` block; the only runtime deps are pandas and numpy.

## Build, test, lint

```bash
pip install -e .              # editable install; exposes console script: opsaudit
python -m pytest tests/ -q    # 8 end-to-end tests; run before committing
opsaudit otif score tests/data/orders.csv --by carrier   # or: python -m opsaudit ...
```

No linter/formatter is configured. CI (`.github/workflows/ci.yml`) only installs `pip install -e . pytest` and runs the tests above on Python 3.10 and 3.12.

## Architecture

- `opsaudit/cli.py` — argparse parser (`build_parser`) + `main`; dispatches to command modules via `args.fn`, serves the `schema` command, and maps exceptions to exit codes.
- `opsaudit/core.py` — shared plumbing: `DataError`, `read_csv` (validates required columns), the `honesty()` builder, `emit()` (writes the JSON envelope), `fail()`, and numpy/pandas JSON encoding.
- `opsaudit/commands/{otif,forecast,abc,pareto}.py` — one module per command; each exposes a module-level `SCHEMA` dict and `run(args) -> (command, result, honesty)`.
- `opsaudit/__main__.py` enables `python -m opsaudit`; `tests/test_cli.py` invokes the CLI as a subprocess against `tests/data/*.csv` and asserts the contract.

## CLI surface

`otif score`, `forecast backtest`, `abc segment`, `pareto rank <csv> --category COL`, and `schema <name>` — where schema names use dot form (`otif.score`, `forecast.backtest`, `abc.segment`, `pareto.rank`) registered in `cli.SCHEMAS`.

## Conventions

- **JSON-only stdout.** Success envelope: `{tool, version, command, result, honesty}`. Data error -> `{"error": {message, hint?}}` on stdout, exit 1; usage error -> argparse text on stderr, exit 2; internal error -> JSON, exit 3. Never print anything else and never let a traceback reach stdout.
- **The `honesty` block is mandatory and non-empty**: `rows_in`, `rows_used`, `dropped[{rows, reason}]`, `definitions{}`, `not_shown[]`. Build it with `core.honesty()`; tests assert `definitions` and `not_shown` are non-empty.
- **Stateless & non-interactive:** same input -> same output; no file writes, no network, no prompts/TTY assumptions.
- Commands `raise core.DataError(msg, hint=...)` for bad user input (never `sys.exit`) and load CSVs via `core.read_csv(..., schema_name=...)` so missing-column errors carry the `schema` hint; emit results only through `core.emit()`.
- **Adding a command:** register its `SCHEMA` in `cli.SCHEMAS`, wire the subparser with `set_defaults(fn=...)`, include an honesty block, and add at least one end-to-end test (per `AGENTS.md`).
