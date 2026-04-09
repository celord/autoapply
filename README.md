# AutoApply

An automated job search and application tool that streamlines the job hunting process across multiple platforms. AutoApply uses browser automation to search for jobs, extract listings, and submit applications on LinkedIn, Indeed, and Glassdoor.

## Features

- **Multi-Platform Support** — Automated job search across LinkedIn, Indeed, and Glassdoor
- **Browser Automation** — Playwright-powered for reliable, modern browser automation
- **Configurable Search** — YAML-based configuration for job titles, locations, and platform-specific settings
- **Secure Cookie Login** — Logs into LinkedIn using your session cookie (li_at) for robust, headless authentication
- **Structured Logging** — Detailed logging with Loguru for monitoring and debugging
- **Test Coverage** — Comprehensive test suite with pytest for all platform integrations
- **Modular Architecture** — Plugin-style platform system with a common base class

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Browser Automation | Playwright |
| HTML Parsing | BeautifulSoup4 |
| Testing | pytest, pytest-cov |
| Logging | Loguru |
| Configuration | PyYAML, python-dotenv |

## Supported Platforms

| Platform | Search | Extract | Apply |
|----------|--------|---------|-------|
| LinkedIn | Yes | Yes | Yes |
| Indeed | Yes | Yes | Yes |
| Glassdoor | Yes | Yes | Yes |

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/mhmalvi/autoapply.git
cd autoapply
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Settings

Edit `config/config.yaml` with your job search preferences:

```yaml
search:
  job_title: "Software Engineer"
  location: "Remote"
  platforms:
    - linkedin
    - indeed
    - glassdoor
```

#### LinkedIn Automation: Using the li_at Cookie

For LinkedIn automation, you must provide your LinkedIn session cookie (`li_at`) in the `.env` file. Automation will log in using this cookie via Playwright.

**How to get your `li_at` cookie:**
1. Log in to LinkedIn in your browser.
2. Open DevTools, find Application/Storage > Cookies for `www.linkedin.com`, and copy your `li_at` value.
3. Place your cookie value in `.env` like this:

```env
li_at=YOUR_LI_AT_COOKIE_HERE
```

> You do NOT need to provide LinkedIn email or password for automation.
> If the session expires, refresh your cookie.

If you need credentials for other platforms, add them to your `.env` as appropriate.

### 5. Run the Application

```bash
python -m src.autoapply.main
```

## Project Structure

```
autoapply/
├── config/
│   └── config.yaml           # Search and platform configuration
├── src/
│   ├── main.py               # Application entry point
│   ├── platforms/
│   │   ├── base.py           # Abstract base class for platforms
│   │   ├── linkedin.py       # LinkedIn automation
│   │   ├── indeed.py         # Indeed automation
│   │   └── glassdoor.py      # Glassdoor automation
│   └── utils/
│       ├── config_loader.py  # YAML configuration parser
│       └── logger.py         # Logging setup
├── tests/
│   ├── conftest.py           # Test fixtures
│   ├── test_linkedin.py
│   ├── test_indeed.py
│   ├── test_glassdoor.py
│   └── test_config.py
├── requirements.txt
└── .gitignore
```

## Running Tests

```bash
pytest --cov=src tests/
```

## License

This project is open source and available under the [MIT License](LICENSE).
