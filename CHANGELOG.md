# Changelog

## v1.1.0

### Added

- `--direction maximize|minimize` for objective direction control.
- Exploit-only, diversity, and oracle upper-bound baselines.
- More conservative descriptor validation and manual feature validation.
- Stronger leakage audit: near-duplicate target features, duplicate rows, missing group column, low group count, and dominant-paper risk.
- `.gitignore` for generated outputs, caches, virtual environments, and build artifacts.
- Local `pytest` compatibility for the `src/` package layout.
- Build-system and setuptools package discovery in `pyproject.toml`.

### Changed

- Decision report now includes final improvement, AUC improvement, random p10/p90, objective direction, and a conservative scientific boundary statement.
- README was rewritten around reproducibility, scientific boundary, and GitHub readiness.

### Removed from release archive

- `__pycache__/`
- `.pytest_cache/`
- `*.egg-info/`
- generated `outputs/`
