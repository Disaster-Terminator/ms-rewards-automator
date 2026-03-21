# Codebase Structure

**Analysis Date:** 2026-03-20

## Directory Layout

```
RewardsCore-test-cleanup/
├── src/                          # Main source code (86 Python files)
│   ├── cli.py                   # CLI entry point (rscore command)
│   ├── __init__.py
│   ├── py.typed                 # Type hints marker for PEP 561
│   │
│   ├── infrastructure/           # Core orchestration (13 files)
│   │   ├── ms_rewards_app.py    # Main controller (Facade pattern)
│   │   ├── task_coordinator.py  # Task orchestrator (Dependency injection)
│   │   ├── system_initializer.py # Component initialization
│   │   ├── config_manager.py    # Configuration management
│   │   ├── config_validator.py  # Config validation + auto-fix
│   │   ├── state_monitor.py     # Points tracking + reporting
│   │   ├── health_monitor.py    # Performance monitoring
│   │   ├── error_handler.py     # Error handling + retry
│   │   ├── notificator.py       # Notification (Telegram/Server酱)
│   │   ├── scheduler.py         # Task scheduling
│   │   ├── logger.py            # Logging setup
│   │   ├── log_rotation.py     # Log cleanup
│   │   ├── self_diagnosis.py    # Self-diagnostics
│   │   ├── protocols.py         # Protocol definitions (type hints)
│   │   ├── config_types.py      # Type definitions
│   │   └── models.py            # Data models
│   │
│   ├── browser/                  # Browser automation (7 files)
│   │   ├── simulator.py         # Browser lifecycle + contexts
│   │   ├── anti_ban_module.py  # Anti-detection features
│   │   ├── popup_handler.py    # Popup/ad detection
│   │   ├── page_utils.py       # Page utilities
│   │   ├── element_detector.py # Element wait/click utilities
│   │   ├── state_manager.py    # Browser state tracking
│   │   └── scripts/             # Anti-focus scripts
│   │
│   ├── login/                    # Login system (13 files + handlers)
│   │   ├── login_state_machine.py # State machine (15+ states)
│   │   ├── login_detector.py   # Login state detection
│   │   ├── human_behavior_simulator.py # Mouse/keyboard simulation
│   │   ├── state_handler.py     # Base handler class
│   │   ├── edge_popup_handler.py # Edge-specific handling
│   │   └── handlers/            # 10+ state handlers
│   │       ├── email_input_handler.py
│   │       ├── password_input_handler.py
│   │       ├── otp_code_entry_handler.py
│   │       ├── totp_2fa_handler.py
│   │       ├── get_a_code_handler.py
│   │       ├── recovery_email_handler.py
│   │       ├── passwordless_handler.py
│   │       ├── auth_blocked_handler.py
│   │       ├── logged_in_handler.py
│   │       └── stay_signed_in_handler.py
│   │
│   ├── search/                   # Search system (10+ files)
│   │   ├── search_engine.py     # Search execution engine
│   │   ├── search_term_generator.py # Search term generation
│   │   ├── query_engine.py      # Multi-source query aggregation
│   │   ├── bing_api_client.py   # Bing API client
│   │   └── query_sources/        # Query source implementations
│   │       ├── query_source.py      # Base class
│   │       ├── local_file_source.py # Local file
│   │       ├── duckduckgo_source.py # DuckDuckGo API
│   │       ├── wikipedia_source.py  # Wikipedia API
│   │       └── bing_suggestions_source.py # Bing suggestions
│   │
│   ├── account/                  # Account management (2 files)
│   │   ├── manager.py           # Session + login management
│   │   └── points_detector.py   # Points extraction from DOM
│   │
│   ├── tasks/                     # Task system (7 files + handlers)
│   │   ├── task_manager.py      # Task discovery + execution
│   │   ├── task_parser.py       # Task parsing from DOM
│   │   ├── task_base.py         # Task base class
│   │   └── handlers/             # Task implementations
│   │       ├── url_reward_task.py # URL visits
│   │       ├── quiz_task.py     # Quiz completion
│   │       └── poll_task.py     # Poll voting
│   │
│   ├── ui/                        # User interface (3 files)
│   │   ├── real_time_status.py  # Progress display
│   │   ├── tab_manager.py       # Tab management
│   │   ├── cookie_handler.py    # Cookie handling
│   │   └── simple_theme.py      # Theme management
│   │
│   ├── diagnosis/                 # Diagnostics (5 files)
│   │   ├── engine.py            # Diagnostic engine
│   │   ├── inspector.py         # Page inspection
│   │   ├── reporter.py          # Report generation
│   │   ├── rotation.py          # Diagnostic rotation
│   │   └── screenshot.py        # Screenshot capture
│   │
│   └── constants/                # Constants (2 files)
│       └── urls.py              # Bing/MS URL constants
│
├── tests/                        # Test suite (64 test files)
│   ├── conftest.py             # Global pytest config
│   ├── fixtures/               # Test fixtures + mock data
│   ├── unit/                  # Unit tests (primary)
│   ├── integration/           # Integration tests
│   └── manual/                 # Manual test checklists
│
├── tools/                       # Development tools
│   ├── check_environment.py   # Environment validation
│   └── search_terms.txt       # Local search term database
│
├── docs/                        # Documentation
│   ├── guides/                # User guides
│   ├── reports/               # Technical reports
│   └── reference/             # Reference docs
│
├── config.yaml                 # Main config file
├── config.example.yaml        # Config template
├── pyproject.toml             # Project metadata + dependencies
├── requirements.txt           # Python dependencies
├── environment.yml            # Conda environment
├── .pre-commit-config.yaml  # Pre-commit hooks
├── CLAUDE.md                  # Project instructions
├── README.md                  # Project readme
└── main.py                    # Backward-compatible entry
```

## Directory Purposes

**`src/infrastructure/`**
- Purpose: Core orchestration and system-wide concerns
- Contains: MSRewardsApp (facade), TaskCoordinator (dependency injection), config management, monitoring, error handling
- Key files: `ms_rewards_app.py`, `task_coordinator.py`, `system_initializer.py`, `config_manager.py`, `state_monitor.py`

**`src/browser/`**
- Purpose: Browser automation and anti-detection
- Contains: BrowserSimulator, AntiBanModule, popup handling, element interaction
- Key files: `simulator.py`, `anti_ban_module.py`, `popup_handler.py`, `element_detector.py`

**`src/login/`**
- Purpose: Microsoft account authentication
- Contains: LoginStateMachine (state machine pattern), state handlers for 10+ login scenarios
- Key files: `login_state_machine.py`, `login_detector.py`, `human_behavior_simulator.py`, `handlers/*.py`

**`src/search/`**
- Purpose: Search term generation and search execution
- Contains: SearchEngine, SearchTermGenerator, QueryEngine, query sources
- Key files: `search_engine.py`, `search_term_generator.py`, `query_engine.py`, `query_sources/*.py`

**`src/account/`**
- Purpose: Session management and points tracking
- Contains: AccountManager, PointsDetector
- Key files: `manager.py`, `points_detector.py`

**`src/tasks/`**
- Purpose: Task discovery and execution (quizzes, polls, URL rewards)
- Contains: TaskManager, TaskParser, task handlers
- Key files: `task_manager.py`, `task_parser.py`, `task_base.py`, `handlers/*.py`

**`src/ui/`**
- Purpose: User interface and real-time feedback
- Contains: StatusManager, TabManager, CookieHandler
- Key files: `real_time_status.py`, `tab_manager.py`, `cookie_handler.py`

**`src/diagnosis/`**
- Purpose: Page inspection and diagnostic reporting
- Contains: DiagnosticEngine, PageInspector, DiagnosisReporter
- Key files: `engine.py`, `inspector.py`, `reporter.py`

**`src/constants/`**
- Purpose: Centralized URL and constant definitions
- Contains: URL constants for Bing, Microsoft, etc.
- Key files: `urls.py`

**`tests/`**
- Purpose: Test suite with unit and integration tests
- Contains: pytest configuration, fixtures, test files
- Key files: `conftest.py`, `fixtures/`, `unit/`, `integration/`

## Key File Locations

**Entry Points:**
- `src/cli.py`: Primary CLI entry point (rscore command)
- `main.py`: Backward-compatible Python entry point

**Configuration:**
- `config.yaml`: Main configuration file
- `config.example.yaml`: Configuration template
- `src/infrastructure/config_manager.py`: Configuration management
- `src/infrastructure/config_validator.py`: Configuration validation

**Core Logic:**
- `src/infrastructure/ms_rewards_app.py`: Main application controller (503 lines)
- `src/infrastructure/task_coordinator.py`: Task orchestration (449 lines)
- `src/infrastructure/system_initializer.py`: Component initialization (140 lines)

**Testing:**
- `tests/unit/`: Unit tests (recommended for daily development)
- `tests/integration/`: Integration tests
- `tests/fixtures/`: Test fixtures and mock data

## Naming Conventions

**Files:**
- Modules: `snake_case.py` (e.g., `login_state_machine.py`, `search_engine.py`)
- Classes: `PascalCase` (e.g., `MSRewardsApp`, `TaskCoordinator`, `BrowserSimulator`)
- Constants: `UPPER_SNAKE_CASE` in `constants/urls.py` (e.g., `BING_URLS`)
- Test files: `test_*.py` (e.g., `test_login_state_machine.py`)
- Test methods: `test_*` or `Test*` (pytest convention)

**Functions/Methods:**
- Functions: `snake_case` (e.g., `async def handle_login()`, `def initialize_components()`)
- Private methods: `_snake_case` prefix (e.g., `_init_components()`, `_check_headless_requirements()`)
- Async functions: `async def` pattern (e.g., `async def run()`)

**Variables:**
- Variables: `snake_case` (e.g., `account_mgr`, `search_engine`, `initial_points`)
- Class variables: `snake_case` (e.g., `self.browser`, `self.config`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `BING_URL`, `MAX_TRANSITIONS`)

**Types:**
- Type hints: Full names (e.g., `page: Page`, `config: ConfigManager`, `args: argparse.Namespace`)
- Custom types: `PascalCase` (e.g., `LoginState`, `TaskMetadata`, `ExecutionReport`)

**Directories:**
- Directory names: `snake_case` (e.g., `query_sources`, `handlers`, `test_fixtures`)
- Top-level directories: Convention (e.g., `src/`, `tests/`, `docs/`)

## Where to Add New Code

**New Feature (search source):**
- Implementation: `src/search/query_sources/your_source.py`
- Base class: `src/search/query_sources/query_source.py` (extend QuerySource)
- Registration: Add to `src/search/query_engine.py` or use dynamic registration

**New Feature (task handler):**
- Implementation: `src/tasks/handlers/your_task.py`
- Base class: `src/tasks/task_base.py` (extend Task)
- Registration: Add to `src/tasks/task_manager.py` task_registry

**New Feature (login handler):**
- Implementation: `src/login/handlers/your_handler.py`
- Base class: `src/login/state_handler.py` (extend StateHandler)
- Registration: Add to `src/login/login_state_machine.py` handler registry

**New Utility:**
- Infrastructure utilities: `src/infrastructure/`
- Browser utilities: `src/browser/`
- UI utilities: `src/ui/`

**New Component:**
- Core: `src/infrastructure/`
- Browser: `src/browser/`
- Login: `src/login/`
- Search: `src/search/`
- Tasks: `src/tasks/`

**Tests:**
- Unit tests: `tests/unit/test_<module>.py`
- Integration tests: `tests/integration/test_<feature>.py`
- Fixtures: `tests/fixtures/` (conftest.py, mock_*.py)

## Special Directories

**`.planning/codebase/`**
- Purpose: Codebase mapping documents (this directory)
- Generated: Yes (by GSD map-codebase command)
- Committed: Yes (version controlled)

**`logs/`**
- Purpose: Runtime logs and diagnostics
- Generated: Yes (created at runtime)
- Committed: No (.gitignore)

**`screenshots/`**
- Purpose: Diagnostic screenshots
- Generated: Yes (when diagnose=True)
- Committed: No (.gitignore)

**`storage_state.json`**
- Purpose: Playwright session persistence
- Generated: Yes (after login)
- Committed: No (.gitignore - contains sensitive session data)

**`.ruff_cache/`**
- Purpose: Linter cache
- Generated: Yes (by ruff)
- Committed: No (.gitignore)

**`.pytest_cache/`**
- Purpose: Pytest cache
- Generated: Yes (by pytest)
- Committed: No (.gitignore)

**`.hypothesis/`**
- Purpose: Hypothesis property testing database
- Generated: Yes (by hypothesis)
- Committed: No (.gitignore)

---

*Structure analysis: 2026-03-20*