# AGENTS.md

> High-signal guidance for OpenCode and future agents working with this repo. Only statements that prevent likely mistakes or accelerate ramp-up are included.

---

## Setup & Prerequisites

- **Dependency manager**: `uv` (not pip). Dependencies are in `pyproject.toml`; `requirements.txt` is deprecated.
- **Playwright browsers must be installed manually** after sync:
  ```bash
  uv sync
  uv run -- python -m playwright install
  ```
- **Configuration is mandatory**:
  - Both required for any run (main, tests):
    - `config/config.json` — all search, platform, browser, and logging settings
    - `.env` — must contain `li_at=YOUR_LINKEDIN_COOKIE` (session cookie, not password)
  - Required config sections: `search`, `application`, `platforms`, `browser`, `delays`, `logging`
  - See `src/autoapply/utils/config_loader.py:58` for exact validation rules
- **No initial code runs without valid config and .env.**

## How to Run

- **Correct entrypoint**: `uv run -- python -m src.autoapply.main` (from repository root)
  - Alternative: activate `.venv` and run `python -m src.autoapply.main`
  - NOT `python src/main.py` or `python -m src.main` — these will not resolve imports correctly
- **Browser mode**: Controlled via `config.json` (`browser.headless`), not code flags
- **Logging**: Configured in `config.json` under `logging.file_path`; directory is auto-created
- **CSV export**: Each run saves found jobs to `jobs_{platform}_{timestamp}.csv` in repository root

## Architecture Notes

- **Two main.py files** (be careful not to confuse them):
  - `src/main.py` — older entry point using `nodriver`; check if still active
  - `src/autoapply/main.py` — current entry point, uses `AutoJobFinder` class and `playwright`
  - Verify which is being imported/used in your changes
- **Plugins**: Each platform (`LinkedIn`, `Indeed`, `Glassdoor`) is in `src/autoapply/platforms/PLATFORM.py` with shared `base.py` interface
- **Config drives everything** — platform selection, search parameters, delays, and logging all come from YAML; never hardcode these
- **Async execution**: Playwright uses async (`async_playlist` context manager); tasks like `search_jobs()` and `apply_to_jobs()` are async

## Testing

- **Pytest** with `pytest-cov` and `pytest-asyncio`
- Run: `uv sync --extras test && uv run -- pytest --cov=src tests/`
- Fixtures in `tests/conftest.py` — config fixtures likely need updating if you change required config keys
- Tests may import `ConfigLoader`; verify config schema matches before running

## Style, Lint, and CI

- No lint or formatter configured; follow PEP8 by inspection
- Logging is strict: use patterns from `src/autoapply/utils/logger.py` for new modules
- Error handling and config validation are strict; see `config_loader.py:48–78` for examples

## Other Quirks

- **Config validation is strict** — missing any required section or field raises `ValueError` before any execution
- No Makefile, pre-commit hooks, or CI workflows; standard Python tooling only
- `pyproject.toml` uses setuptools backend; packages are in `src` subdirectory

## References

- [README.md](README.md) — setup, credential extraction, and run commands
- [`src/autoapply/utils/config_loader.py`](src/autoapply/utils/config_loader.py) — canonical required config fields (lines 58–78)
- [`src/autoapply/main.py`](src/autoapply/main.py) — main application logic and `AutoJobFinder` class

---

**Debugging tip**: If imports fail or config is not found, trace the working directory and Python path. Always run from repository root.