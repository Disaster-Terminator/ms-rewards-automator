# Architecture

**Analysis Date:** 2026-03-20

## Pattern Overview

**Overall:** Facade Pattern with Dependency Injection

**Key Characteristics:**
- **Facade Pattern**: `MSRewardsApp` orchestrates all subsystems through a unified interface, hiding complexity from callers
- **Dependency Injection**: `TaskCoordinator` receives all dependencies through constructor, improving testability and maintainability
- **State Machine Pattern**: `LoginStateMachine` manages complex login flow with 15+ states and handlers
- **Strategy Pattern**: `QueryEngine` supports multiple query sources (local file, DuckDuckGo, Wikipedia, Bing)
- **Composite Pattern**: `TaskManager` executes different task types through unified `Task` interface
- **Observer Pattern**: `StatusManager` provides real-time progress updates to UI layer

## Layers

**Infrastructure Layer:**
- Purpose: Core application orchestration and system-wide concerns
- Location: `src/infrastructure/`
- Contains: `MSRewardsApp`, `TaskCoordinator`, `SystemInitializer`, `ConfigManager`, `StateMonitor`, `HealthMonitor`, `ErrorHandler`, `Notificator`, `Scheduler`, `LogRotation`, `SelfDiagnosis`
- Depends on: Browser, Account, Search, Tasks, UI layers
- Used by: CLI layer

**Browser Layer:**
- Purpose: Browser lifecycle management, anti-detection, element interaction
- Location: `src/browser/`
- Contains: `BrowserSimulator`, `AntiBanModule`, `PopupHandler`, `PageUtils`, `ElementDetector`, `StateManager`, `AntiFocusScripts`
- Depends on: Infrastructure layer
- Used by: Infrastructure (via TaskCoordinator)

**Login Layer:**
- Purpose: Microsoft account authentication with state machine
- Location: `src/login/`
- Contains: `LoginStateMachine`, `LoginDetector`, `HumanBehaviorSimulator`, `StateHandler`, 10+ handler files in `handlers/`
- Depends on: Browser layer
- Used by: Infrastructure (via TaskCoordinator)

**Search Layer:**
- Purpose: Search term generation and search execution
- Location: `src/search/`
- Contains: `SearchEngine`, `SearchTermGenerator`, `QueryEngine`, `BingAPIClient`, query sources in `query_sources/`
- Depends on: Browser layer, Infrastructure
- Used by: Infrastructure (via TaskCoordinator)

**Account Layer:**
- Purpose: Session management, login state, points detection
- Location: `src/account/`
- Contains: `AccountManager`, `PointsDetector`
- Depends on: Browser layer
- Used by: Infrastructure (via TaskCoordinator)

**Tasks Layer:**
- Purpose: Task discovery, parsing, and execution (quizzes, polls, URL rewards)
- Location: `src/tasks/`
- Contains: `TaskManager`, `TaskParser`, `TaskBase`, task handlers in `handlers/`
- Depends on: Browser layer, Account layer
- Used by: Infrastructure (via TaskCoordinator)

**UI Layer:**
- Purpose: Real-time status display, tab management, cookie handling
- Location: `src/ui/`
- Contains: `StatusManager`, `TabManager`, `CookieHandler`, `SimpleThemeManager`
- Depends on: Infrastructure layer
- Used by: All layers (for progress updates)

**Diagnosis Layer:**
- Purpose: Page inspection, issue detection, diagnostic reporting
- Location: `src/diagnosis/`
- Contains: `Engine`, `Inspector`, `Reporter`, `Rotation`, `Screenshot`
- Depends on: Browser layer
- Used by: Infrastructure (MSRewardsApp when diagnose=True)

**Constants Layer:**
- Purpose: Centralized URL and constant definitions
- Location: `src/constants/`
- Contains: `urls.py`
- Used by: All layers

**CLI Layer:**
- Purpose: Command-line interface entry point
- Location: `src/cli.py`
- Contains: Argument parsing, signal handling, scheduler integration
- Used by: None (entry point)

## Data Flow

**Main Execution Flow:**

```
cli.py (entry point)
    ↓
async_main() [cli.py:143]
    ↓
ConfigManager + ConfigValidator (load config)
    ↓
Signal setup (SIGINT/SIGTERM)
    ↓
Scheduler (if enabled) → TaskScheduler.run_scheduled_task()
    ↓ OR
MSRewardsApp(config, args, diagnose=diagnose_enabled)
    ↓
MSRewardsApp.run() [8-step flow]
    ├─ [1/8] _init_components()
    │   └─ SystemInitializer.initialize_components()
    │       ├─ Create BrowserSimulator
    │       ├─ Create SearchEngine, SearchTermGenerator
    │       ├─ Create AccountManager, PointsDetector
    │       ├─ Create StateMonitor, HealthMonitor
    │       ├─ Create ErrorHandler, Notificator
    │       └─ Instantiate TaskCoordinator with all dependencies
    │
    ├─ [2/8] _create_browser()
    │   └─ BrowserSimulator.create_desktop_browser()
    │       └─ create_context() with storage_state
    │
    ├─ [3/8] _handle_login()
    │   └─ TaskCoordinator.handle_login(page, context)
    │       ├─ AccountManager.session_exists()?
    │       ├─ AccountManager.is_logged_in() or
    │       └─ TaskCoordinator._do_login()
    │           ├─ Auto login (if configured) or
    │           └─ Manual login (wait_for_manual_login)
    │               └─ LoginStateMachine (with 10+ handlers)
    │
    ├─ [4/8] _check_initial_points()
    │   └─ StateMonitor.check_points_before_task()
    │       └─ PointsDetector.get_current_points()
    │
    ├─ [5/8] _execute_searches() [desktop]
    │   └─ TaskCoordinator.execute_desktop_search()
    │       └─ SearchEngine.execute_desktop_searches()
    │           ├─ SearchTermGenerator.generate() [or QueryEngine]
    │           ├─ page.goto(BING_URL + query)
    │           ├─ AntiBanModule.random_delay()
    │           └─ PointsDetector.get_current_points()
    │
    ├─ [6/8] _execute_searches() [mobile]
    │   └─ TaskCoordinator.execute_mobile_search()
    │       ├─ Create mobile context (iPhone simulation)
    │       ├─ Verify mobile login state
    │       └─ SearchEngine.execute_mobile_searches()
    │
    ├─ [7/8] _execute_daily_tasks()
    │   └─ TaskCoordinator.execute_daily_tasks()
    │       ├─ TaskManager.discover_tasks()
    │       ├─ TaskParser.discover_tasks() [DOM parsing]
    │       └─ TaskManager.execute_tasks()
    │           └─ Task handlers (URLRewardTask/QuizTask/PollTask)
    │
    └─ [8/8] _generate_report()
        ├─ StateMonitor.save_daily_report()
        ├─ Notificator.send_daily_report()
        └─ LogRotation.cleanup_all()
```

**State Management:**
- Configuration: `ConfigManager` (YAML + environment variables + CLI args priority)
- Session: `storage_state.json` (Playwright session persistence)
- Execution State: `StateMonitor` tracks points, searches, tasks, alerts
- Health: `HealthMonitor` tracks performance metrics
- Real-time UI: `StatusManager` provides progress via classmethods

## Key Abstractions

**Facade Pattern:**
- Purpose: Unified interface to complex subsystems
- Examples: `src/infrastructure/ms_rewards_app.py`, `src/infrastructure/task_coordinator.py`
- Pattern: MSRewardsApp delegates to TaskCoordinator, which coordinates subsystems

**State Machine Pattern:**
- Purpose: Manage complex login flow with multiple states and handlers
- Examples: `src/login/login_state_machine.py`
- Pattern: 15+ states (EMAIL_INPUT, PASSWORD_INPUT, TOTP_2FA, etc.) with handler registry

**Strategy Pattern:**
- Purpose: Support multiple search term sources
- Examples: `src/search/query_engine.py`, `src/search/query_sources/`
- Pattern: QuerySource base class with implementations (LocalFile, DuckDuckGo, Wikipedia, BingSuggestions)

**Dependency Injection:**
- Purpose: Decouple TaskCoordinator from concrete implementations
- Examples: `src/infrastructure/task_coordinator.py` constructor
- Pattern: Receives all dependencies (AccountManager, SearchEngine, etc.) through constructor

**Composite Pattern:**
- Purpose: Execute different task types through unified interface
- Examples: `src/tasks/task_manager.py`, `src/tasks/task_base.py`, `src/tasks/handlers/`
- Pattern: Task base class with concrete implementations (UrlRewardTask, QuizTask, PollTask)

## Entry Points

**Primary Entry Point:**
- Location: `src/cli.py`
- Triggers: `rscore` command (installed via pyproject.toml entry_points)
- Responsibilities: Parse arguments, setup logging, load config, create MSRewardsApp, run main loop
- Called by: Shell (user runs `rscore`)

**Secondary Entry Point:**
- Location: `main.py`
- Triggers: `python main.py`
- Responsibilities: Backward compatibility wrapper that imports and calls `cli.main()`
- Called by: Python interpreter

**Application Controller:**
- Location: `src/infrastructure/ms_rewards_app.py` (class MSRewardsApp)
- Triggers: Instantiated by cli.py, run() method called
- Responsibilities: 8-step execution flow, component lifecycle, error handling, cleanup

**Task Coordination:**
- Location: `src/infrastructure/task_coordinator.py` (class TaskCoordinator)
- Triggers: Called by MSRewardsApp methods
- Responsibilities: Orchestrate login, searches, tasks with injected dependencies

## Error Handling

**Strategy:** Graceful degradation with fallback mechanisms

**Patterns:**
- Try-catch blocks in async methods with specific exception handling
- Fallback mechanisms (e.g., diagnosis mode disabled on import failure)
- Page crash detection and automatic recreation (`_is_page_crashed()`, `_recreate_page()`)
- Health monitor tracks error rates and alerts

**Examples:**
- MSRewardsApp._cleanup() - ensures resources released even on error
- TaskCoordinator.execute_mobile_search() - handles context switching failures
- Notificator - gracefully handles notification failures
- ConfigValidator - auto-fixes common configuration issues

## Cross-Cutting Concerns

**Logging:**
- Framework: Python standard `logging` module
- Setup: `infrastructure/logger.py` (setup_logging function)
- Location: `logs/automator.log` with rotation (10MB × 5 files)
- Levels: DEBUG, INFO, WARNING, ERROR

**Validation:**
- Config validation: `infrastructure/config_validator.py` - validates config.yaml, auto-fixes issues
- Parameter validation: argparse in cli.py
- State validation: LoginStateMachine (max transitions protection)

**Authentication:**
- Approach: Playwright session persistence via `storage_state.json`
- Manual: User login with session saved
- Auto: Config-based credentials with TOTP support

---

*Architecture analysis: 2026-03-20*