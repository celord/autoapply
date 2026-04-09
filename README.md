# AutoApply (Standalone Edition)

An automated job search and extraction tool that streamlines the job hunting process on LinkedIn, with Playwright browser automation. This version is a substantially refactored and modernized fork, rebuilt for clarity, maintainability, and reliability with Playwright Python.

## Features

- **LinkedIn Automation** — Automated job search and extraction from LinkedIn
- **Browser Automation** — Modern, Playwright-powered browser automation (Selenium fully removed)
- **Configurable Search** — YAML-based search and platform configuration
- **Cookie-based Login** — Log in to LinkedIn by providing your `li_at` session cookie in the `.env` file
- **Logging** — Structured and robust log output for monitoring and debugging
- **Extensible** — Clean, modular code structure to allow future additions or platform integrations

## Tech Stack

| Component          | Technology         |
|--------------------|-------------------|
| Language           | Python 3.10+       |
| Browser Automation | Playwright         |
| HTML Parsing       | (built-in, minimal)|
| Logging            | Loguru             |
| Configuration      | PyYAML, python-dotenv |
| Dependency Manager | [uv](https://astral.sh/uv/) + pyproject.toml |

## LinkedIn Support Only

> This version currently supports LinkedIn. Indeed/Glassdoor code is not guaranteed to be current or maintained.

## Getting Started

### 1. Install uv (one-time, if you haven’t)

[Install uv using their recommended method. Official docs: https://docs.astral.sh/uv/getting-started/installation/]

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
**Windows (powershell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
**Alternatively (using pipx):**
```bash
pipx install uv
```

### 2. Clone Your Repository
```bash
git clone https://github.com/YOUR-USER/YOUR-REPO.git
cd YOUR-REPO
```

### 3. Create Virtual Environment & Install Dependencies
```bash
uv venv              # Creates (or reuses) a project .venv
uv sync              # Installs dependencies from pyproject.toml (fast!)
```

### 4. (Important) Install Playwright Browsers
Playwright requires a one-time manual browser install, which cannot be handled automatically via uv:
```bash
uv run -- python -m playwright install
```
(You must run this inside your `.venv`/project environment after dependency sync.)

### 5. Configure Settings

Edit `config/config.yaml` with your job search preferences, for example:
```yaml
search:
  job_title: "Software Engineer"
  location: "Remote"
  platforms:
    - linkedin
```

#### LinkedIn Automation: Using the li_at Cookie
For LinkedIn automation, you must provide your LinkedIn session cookie (`li_at`) in the `.env` file. This allows login without using your username or password.

How to get your `li_at` cookie:
1. Log into LinkedIn in your browser.
2. Open DevTools, go to Application > Cookies for `www.linkedin.com` and find/copy the `li_at` value.
3. Place your cookie value in `.env`:
```env
li_at=YOUR_LI_AT_COOKIE_HERE
```
> Session cookies will expire over time. Refresh if you encounter authentication issues.

### 6. Run the Application
You can use uv or direct Python to run the main script:

**Recommended** (one-step):
```bash
uv run -- python -m src.autoapply.main
```

**Manual (activate first):**
```bash
source .venv/bin/activate   # On Linux/macOS
.venv\Scripts\activate      # On Windows
python -m src.autoapply.main
```

This will start the automated LinkedIn job search tool according to your settings.
## Project Structure

```
autoapply/
├── config/
│   └── config.yaml           # Search configuration
├── src/
│   ├── main.py               # Application entry point
│   └── platforms/
│       ├── linkedin.py       # LinkedIn automation logic
│       └── ...               # (other platforms: untested)
├── pyproject.toml            # Dependency/project specification
├── requirements.txt          # Deprecated (use pyproject.toml)
└── .gitignore
```

## Running Tests
```bash
uv pip install -r pyproject.toml[test]  # One-time, if test dependencies not already synced
uv run -- pytest --cov=src tests/
```
Or, using optional dependencies:
```bash
uv sync --extras test
uv run -- pytest --cov=src tests/
```

## Origin & Acknowledgments

This project is an independently maintained and heavily refactored fork of earlier open-source job automation solutions. Major architectural changes, dependency upgrades, Playwright integration, and new features are all original to this repository.

## License

This project is licensed under the [MIT License](LICENSE).

---
If you use this tool, improvements and issues should be reported via your repository. For new features or upstream merges, credit prior authors as required by their licenses.
