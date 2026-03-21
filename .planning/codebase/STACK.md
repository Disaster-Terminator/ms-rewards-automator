# Technology Stack

**Analysis Date:** 2026-03-20

## Languages & Runtime

**Primary Language:**
- Python 3.10+ (with modern features: pattern matching, structural pattern matching)

**Runtime:**
- CPython (standard Python interpreter)
- AsyncIO-based concurrency throughout

## Frameworks & Core Libraries

**Browser Automation:**
- `playwright` (v1.49+) - Browser automation framework
- `playwright-stealth` - Anti-detection plugin for Playwright

**Configuration & Validation:**
- `pydantic` (v2.9+) - Data validation and settings management (not heavily used but in dependencies)
- `pyyaml` - YAML configuration parsing

**HTTP & Networking:**
- `aiohttp` - Async HTTP client (for external API queries: DuckDuckGo, Wikipedia)
- `httpx` - Modern HTTP client (alternative, currently not used but in dependencies)

**Testing:**
- `pytest` (v8.0.0+) - Test framework
- `pytest-asyncio` (v0.24.0+) - Async test support
- `pytest-cov` (v6.0.0+) - Coverage reporting
- `pytest-xdist` (v3.5.0+) - Parallel test execution
- `pytest-timeout` (v2.3.0+) - Test timeouts
- `pytest-benchmark` (v5.0.0+) - Performance benchmarks
- `hypothesis` (v6.125.0+) - Property-based testing

**Code Quality:**
- `ruff` (v0.8.0+) - Fast Python linter and formatter (replaces flake8, black, isort)
- `mypy` (v1.14.0+) - Static type checker
- `pre-commit` - Git hook framework

**Utilities:**
- `beautifulsoup4` + `lxml` - HTML/XML parsing (DOM analysis for points detection and task parsing)
- `python-dotenv` - Environment variable loading from .env files

**CLI & Argument Parsing:**
- `argparse` (standard library) - Command-line argument parsing

**Logging & Monitoring:**
- `psutil` - System resource monitoring (browser process memory/CPU)

**Time & Scheduling:**
- `schedule` - Job scheduling (for scheduler mode)
- `APScheduler` - Advanced scheduling (in dependencies, currently not used)

**Data:**
- `orjson` - Fast JSON parsing (optional, in dependencies)

## Configuration Management

**Main Config File:** `config.yaml` (user-editable, copied from `config.example.yaml`)

**Configuration Priority (highest to lowest):**
1. CLI arguments (e.g., `--dev`, `--headless`, `--user`)
2. Environment variables (e.g., `MS_REWARDS_EMAIL`, `MS_REWARDS_PASSWORD`, `MS_REWARDS_TOTP_SECRET`)
3. YAML configuration file (`config.yaml`)
4. Default values in `ConfigManager`

**Key Configuration Sections:**
```yaml
search:          # Search counts, wait intervals
browser:         # Headless mode, browser type
login:           # Auto-login credentials, state machine settings
scheduler:       # Scheduled execution mode
anti_detection:  # Stealth settings, human behavior level
task_system:     # Task execution enable/disable, debug mode
query_engine:    # Multi-source query aggregation settings
notification:    # Telegram, Server酱 notification settings
```

## Project Setup & Packaging

**Build System:**
- `pyproject.toml` (PEP 518/517/621) - Modern Python project configuration
- `setuptools` + `setuptools_scm` - Packaging (version from git tags)

**Entry Points:**
```toml
[project.scripts]
rscore = "src.cli:main"
```

**Dependencies Management:**
- `requirements.txt` - Pinned dependencies (generated from pyproject.toml)
- `environment.yml` - Conda environment specification (optional)

**Type Hints:**
- `py.typed` marker in `src/` indicates PEP 561 compliance
- Full type annotations throughout codebase (enforced by mypy)

## Development Tools

**Code Formatting & Linting:**
- `ruff` - Combined linter/formatter (replaces multiple tools)
  - Uses rules: E (pycodestyle errors), W (pycodestyle warnings), F (Pyflakes), I (isort), B (flake8-bugbear), C4 (flake8-comprehensions), UP (pyupgrade)
  - Ignored: E501 (line length - custom 100), B008 (mutable args), C901 (complexity)
  - Line length: 100 characters (not 79)
  - Quote style: double quotes
  - Indentation: 2 spaces

**Type Checking:**
- `mypy` - Static type verification
  - Python version: 3.10
  - Strict mode: warnings on any/unused configs

**Pre-commit Hooks:**
- `.pre-commit-config.yaml` configures automatic checks before commits
  - Ruff linter with auto-fix
  - Ruff formatter

## Deployment & Execution

**Command-Line Interface:**
```bash
rscore [OPTIONS]
```

**Common Commands:**
```bash
# Install (development)
pip install -e ".[dev]"

# Install (production)
pip install -e .

# Install Playwright browser
playwright install chromium

# Run
rscore                    # Production (20 searches, scheduler)
rscore --dev              # Development (2 searches, faster)
rscore --user             # User testing (3 searches, manual login)
rscore --headless         # Headless mode
```

## External Services Dependencies

**Microsoft Services (via Browser Automation):**
- `login.live.com` - Microsoft account authentication
- `rewards.bing.com` - Rewards dashboard and task management
- `bing.com` - Search engine for earning points
- `account.microsoft.com` - Account settings and profile

**External APIs (for Query Sources):**
- `DuckDuckGo API` - Search suggestions (no authentication required)
- `Wikipedia API` - Trending topics and random pages (no authentication required)
- `Bing Suggestions API` - Search term suggestions (simulated, no official API key)

**Optional Notification Services:**
- `Telegram Bot API` - Telegram notifications (requires bot token + chat ID)
- `Server酱` (sct.ftqq.com) - WeChat notifications (requires send key)

## Data Storage

**Runtime Files:**
- `storage_state.json` - Playwright session state (cookies, localStorage) - **sensitive**
- `logs/automator.log` - Main execution log (rotating: 10MB × 5)
- `logs/daily_reports/` - JSON reports per execution
- `logs/theme_state.json` - Bing theme preferences
- `logs/diagnosis/` - Diagnostic data when `--diagnose` enabled
- `logs/state_monitor_state.json` - Persistent execution state

**Configuration Files:**
- `config.yaml` - User configuration (may contain credentials, should be in .gitignore if sensitive)
- `config.example.yaml` - Template for new users

**Generated Files (not committed):**
- `__pycache__/`, `*.pyc` - Python bytecode
- `.pytest_cache/` - Pytest cache
- `.hypothesis/` - Hypothesis test database
- `coverage.xml`, `htmlcov/` - Coverage reports
- `.ruff_cache/` - Ruff cache
- `screenshots/` - Diagnostic screenshots
- `.env` - Environment variables (if used)

## Version Control

- **VCS:** Git
- **Branch Strategy:**
  - `main` - Stable releases
  - `feature/*` - New feature development
  - `refactor/*` - Code refactoring
  - `fix/*` - Bug fixes
  - `test/*` - Test-related changes
- **Commit Convention:** Conventional Commits (feat, fix, refactor, test, docs, chore)
- **Pre-commit Hooks:** Enforced (ruff check, ruff format)

---

*Stack analysis: 2026-03-20*
