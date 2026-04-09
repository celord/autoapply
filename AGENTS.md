# AGENTS.md

> High-signal guidance for OpenCode and future agents working with this repo. Only statements that prevent likely mistakes or accelerate ramp-up are included.

---

## Setup & Prerequisites

- **Virtualenv required**: Always activate a virtual environment before installing dependencies. Packages are pinned in `requirements.txt`.
- **Configuration is mandatory**:
  - All main runs and tests require both:
    - `config/config.yaml` (controls all search, apply, and platform behaviors)
    - `.env` file (for credentials/secrets)
  - If any required config section or key is missing, the code will fail to start (see `src/utils/config_loader.py` for required fields).
- **Credentials**: `.env` file is required and must include at least LinkedIn credentials (see `README.md`).
- **No initial code will work without valid config and .env, even for test runs.**

## How to Run

- **Main entrypoint:** `python src/main.py` (always run from repository root).
- Application logic lives in the `AutoJobFinder` class, but invoking `src/main.py` as a script is the canonical way.
- Headless / non-headless browsing is toggled via `config/config.yaml` (`browser.headless`), NOT code flags.
- Log output is written to the path specified in `config.yaml` under `logging.file_path` (directory is created if missing).

## Architecture Notes

- **Plugins**: Each job platform (`LinkedIn`, `Indeed`, `Glassdoor`) is implemented in `src/platforms/PLATFORM.py`, using a shared base class.
- **YAML config powers nearly all execution** – search targets, job types, and platform enablement all come from config, never hardcode or patch these in scripts.
- **Tests**: Use pytest. Some tests rely on importing a valid config file; update config fixtures if you add/remove required config keys.
- **No advanced infra (tox, Makefile, lockfile, monorepo, or extra orchestrator) exists. Use only README/requirements.txt guidance.**

## Style, Lint, and CI

- No lint command, style checker, or pre-commit hooks are present. Adhere to PEP8 and repo conventions by inspection only.
- Logging, error handling, and config validation are strict – follow patterns in `src/utils/logger.py` and `src/utils/config_loader.py` if making new modules.

## Other Quirks

- **Do not trust any config that gets out of sync with executable logic.** Always defer to actual validation code in `src/utils/config_loader.py` and `src/main.py` if docs/config disagree.
- No special task runner, script aliasing, or workspace setup beyond the above. Standard CLI only.

## References

- [README.md](README.md) (primary usage & setup instructions)
- [`src/utils/config_loader.py`](src/utils/config_loader.py) (canonical list of required config keys)

---

If in doubt, trace config and control/data flow via YAML/config-driven classes first, then verify with executable code. Avoid adding generic advice here.