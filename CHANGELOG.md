# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/); versioning follows [SemVer](https://semver.org/).

## [0.1.0] — 2026-07-14

### Added
- `otif score` — the 5-rung OTIF metric ladder with segment breakdown, promise-padding and tail stats
- `forecast backtest` — rolling-origin backtest of five baselines; WMAPE, bias, disclosed MAPE, FVA vs naive
- `abc segment` — ABC-XYZ classification with a 9-box summary and explicit, overridable thresholds
- `pareto rank` — decision-grade Pareto with label hygiene, optional weight and exposure normalization
- `schema` — machine-readable input schemas per command
- The mandatory **honesty block** on every result: rows in/used/dropped (with reasons), all definitions, and `not_shown`
- 8 end-to-end CLI tests; seeded fixtures
- Turkish README (`README.tr.md`)
