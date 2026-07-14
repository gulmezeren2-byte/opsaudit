# Agent Guide

`opsaudit` is built to be called by AI agents. The contract:

- **stdout is always JSON** — results and data errors alike. Parse it; never scrape human text.
- **Exit codes:** 0 = success · 1 = data error (JSON `{"error": {message, hint?}}` on stdout) · 2 = usage error (argparse text on stderr) · 3 = internal error (JSON on stdout; please report).
- **Discover inputs first:** `opsaudit schema <command>` (e.g. `otif.score`) prints the required/optional columns as JSON. Map the user's export to that schema before calling.
- **Surface the honesty block.** Every result carries `honesty` (rows in/used/dropped with reasons, every definition the numbers depend on, and `not_shown`). When you summarize a result for a human, include the definitions and the `not_shown` caveats — that is what keeps your summary from over-claiming.
- **Stateless:** same input, same output; nothing is written anywhere; no network calls.

Development conventions: run `python -m pytest tests/ -q` before committing; a new command needs a schema entry, an honesty block and at least one end-to-end test.
