# External Integrations

**Analysis Date:** 2026-03-20

## Overview

This codebase integrates with multiple external services and APIs to accomplish its goals. These integrations span browser automation, HTTP APIs, and notification channels.

## Microsoft Ecosystem (Primary)

### Microsoft Account Authentication

**Purpose:** Authenticate with Microsoft account to access Rewards program

**Integration Points:**
- `src/login/` - Complete login system with state machine
- `src/account/manager.py` - Session management
- `src/browser/simulator.py` - Browser context with session persistence

**Endpoints:**
- `https://login.live.com` - Primary login page
- `https://account.microsoft.com` - Account management
- Various Microsoft identity endpoints (dynamic based on login flow)

**Authentication Methods:**
- Manual login: User manually logs in via visible browser, session saved to `storage_state.json`
- Auto-login: Credentials from config + TOTP 2FA (if configured)
- Session persistence: Playwright `storage_state.json` preserves cookies/localStorage

**Configuration:**
```yaml
login:
  auto_login:
    enabled: false
    email: ""          # From env: MS_REWARDS_EMAIL
    password: ""       # From env: MS_REWARDS_PASSWORD
    totp_secret: ""    # From env: MS_REWARDS_TOTP_SECRET (optional 2FA)
  state_machine_enabled: true
  max_transitions: 20
  timeout_seconds: 300
```

**Key Files:**
- `src/login/login_state_machine.py` - 15+ state handlers for various login scenarios
- `src/login/handlers/` - Individual handlers (email, password, TOTP, recovery, etc.)
- `src/login/human_behavior_simulator.py` - Typing delays, mouse movements

### Microsoft Rewards Dashboard

**Purpose:** Access Bing rewards dashboard to discover tasks and track points

**Integration Points:**
- `src/account/points_detector.py` - Extract points from dashboard DOM
- `src/tasks/task_parser.py` - Parse available tasks from dashboard
- `src/infrastructure/state_monitor.py` - Track points before/after tasks

**Endpoints:**
- `https://rewards.bing.com` - Main rewards dashboard
- Various redirect URLs during login flow

**Data Extracted:**
- Current points balance (daily/available)
- Available tasks ( quizzes, polls, URL rewards)
- Task status (completed, available)
- Search progress

**Selectors (hardcoded, may break if Microsoft changes UI):**
- Points detection: `.points-active`, credential balance elements
- Task cards: `.task-card`, `.b_totalTaskCard`, task name and status

### Bing Search

**Purpose:** Execute searches to earn rewards points

**Integration Points:**
- `src/search/search_engine.py` - Search execution engine
- `src/search/search_term_generator.py` - Generate diverse search terms
- `src/search/query_engine.py` - Aggregate from multiple query sources

**Endpoints:**
- `https://www.bing.com/search?q=<query>` - Search execution URL

**Features:**
- Desktop searches (configurable count, default 20)
- Mobile searches (optional, configurable count)
- Theme management (dark/light) to mimic real user
- Anti-detection: random delays, mouse movements
- Progress tracking via points detection before/after

**Configuration:**
```yaml
search:
  desktop_count: 20
  mobile_count: 0
  wait_interval:
    min: 5
    max: 15
```

## External APIs (Query Sources)

### DuckDuckGo Suggestions API

**Purpose:** Generate search term suggestions dynamically

**Integration:** `src/search/query_sources/duckduckgo_source.py`

**Endpoint:** `https://duckduckgo.com/ac/` (suggestions endpoint)

**Method:** GET with query parameter `q=<seed>`

**Authentication:** None required

**Data Format:** JSON array of suggestion objects with `phrase` field

**Configuration:**
```yaml
query_engine:
  sources:
    duckduckgo:
      enabled: true
      timeout: 15
      max_queries_per_session: 10
```

**Rate Limiting:** None enforced by API, but should add respect for service

**Fallback:** If API fails, source returns empty list and other sources compensate

### Wikipedia API

**Purpose:** Fetch trending topics and random page titles for diverse searches

**Integration:** `src/search/query_sources/wikipedia_source.py`

**Endpoints:**
- `https://en.wikipedia.org/api/rest_v1/page/summary/<topic>` - Get page title from topic
- `https://en.wikipedia.org/w/api.php` - Random page (legacy endpoint)

**Method:** GET requests with `aiohttp`

**Authentication:** None required

**Data Format:** JSON with `title` field

**Features:**
- Uses predefined trending topics list (AI, climate, space, etc.)
- Fetches random pages to fill quotas
- Concurrent request handling via async

**Configuration:**
```yaml
query_engine:
  sources:
    wikipedia:
      enabled: true
      timeout: 15
      max_queries_per_session: 10
```

**Rate Limiting:** No strict limits but should add delays to be respectful

### Bing Suggestions API ( unofficial )

**Purpose:** Get search suggestions from Bing's autocomplete

**Integration:** `src/search/query_sources/bing_suggestions_source.py`

**Endpoint:** `https://www.bing.com/osjson.aspx` (undocumented)

**Method:** GET with query parameters `q=<query>&variant=...`

**Authentication:** None required, but uses common user-agent headers

**Data Format:** JSON array with first element query, second array suggestions

**Configuration:** (inherits timeout from general query_engine settings)

**Note:** Unofficial API, may change or require headers at any time

## Notification Services (Optional)

### Telegram Bot API

**Purpose:** Send execution reports and alerts via Telegram messages

**Integration:** `src/infrastructure/notificator.py`

**API:** `https://api.telegram.org/bot<token>/sendMessage`

**Required Credentials:**
- `notification.telegram.bot_token` - Telegram bot token (from BotFather)
- `notification.telegram.chat_id` - Target chat/user ID

**Data Sent:**
- Daily execution summary
- Points earned
- Success/failure counts
- Error alerts

**Configuration:**
```yaml
notification:
  enabled: false
  telegram:
    enabled: false
    bot_token: ""   # Env: TELEGRAM_BOT_TOKEN
    chat_id: ""     # Env: TELEGRAM_CHAT_ID
```

### Server酱 (ServerChan)

**Purpose:** Send notifications to WeChat via Server酱 service

**Integration:** `src/infrastructure/notificator.py`

**API:** `https://sctapi.ftqq.com/<send_key>.send`

**Required Credentials:**
- `notification.serverchan.key` - Send key from Server酱

**Data Sent:** Same as Telegram (title + description)

**Configuration:**
```yaml
notification:
  enabled: false
  serverchan:
    enabled: false
    key: ""   # Env: SERVERCHAN_KEY
```

## Internal Components (No External Dependencies)

These are self-contained modules within the codebase:

**Logging:** Python standard library `logging`
**Configuration:** `pyyaml` for YAML parsing
**Testing:** `pytest` ecosystem, `unittest.mock`
**Type hints:** Standard Python `typing` module
**AsyncIO:** Standard library `asyncio`
**Time/Scheduling:** `datetime`, `time`, `schedule` library

## Dependency Graph

```
MSRewardsApp (orchestration)
    ├─ BrowserSimulator → Playwright
    │   └─ AntiBanModule → playwright-stealth
    ├─ AccountManager
    │   └─ PointsDetector → BeautifulSoup4 + lxml (DOM parsing)
    ├─ SearchEngine
    │   ├─ SearchTermGenerator
    │   └─ QueryEngine
    │       ├─ LocalFileSource (no external)
    │       ├─ DuckDuckGoSource → aiohttp → DuckDuckGo API
    │       ├─ WikipediaSource → aiohttp → Wikipedia API
    │       └─ BingSuggestionsSource → aiohttp → Bing suggestions
    ├─ TaskManager
    │   ├─ TaskParser → BeautifulSoup4 + lxml
    │   └─ TaskHandlers (URL, Quiz, Poll)
    ├─ StateMonitor → points_detector
    ├─ Notificator (optional)
    │   ├─ Telegram Bot API
    │   └─ Server酱 API
    ├─ HealthMonitor → psutil
    └─ ConfigManager → pyyaml
```

## API Rate Limits & Considerations

**DuckDuckGo Suggestions:** No official rate limits but be respectful - add delays
**Wikipedia API:** Rate limited per IP, use caching and delays
**Bing Suggestions:** Undocumented, may have limits or block automated access
**Telegram/Server酱:** Subject to their respective rate limits (usually generous for notifications)

**Best Practices:**
- Add exponential backoff on API failures
- Respect `Retry-After` headers if present
- Implement circuit breaker pattern (not yet implemented, see CONCERNS.md)
- Cache query results when possible

## Security Considerations

**Credentials Storage:**
- Recommended: Use environment variables (`MS_REWARDS_*`)
- Alternative: `config.yaml` (ensure `.gitignore` includes sensitive configs)
- Session persistence: `storage_state.json` contains cookies/tokens - treat as highly sensitive

**API Keys:**
- Notification tokens should be kept out of version control
- Use `.env` file (not committed) or system environment variables

**Browser Security:**
- `--password-store=basic` flag used to avoid system keychain (see `browser/simulator.py`)
- Anti-detection measures may trigger Microsoft security responses
- Using automation violates Microsoft Rewards ToS - use at own risk

## Failure Modes

**Microsoft Login Flow Changes:**
- Impact: State machine handlers may fail to detect correct page
- Detection: LoginTimeouts, repeated state transitions
- Recovery: Enable `--diagnose` to capture screenshots, update selectors

**DOM Structure Changes:**
- Impact: Points detection, task parsing fail silently
- Detection: Zero points detected, "no tasks found" despite visible tasks
- Recovery: Use diagnostic mode to capture DOM, update selectors in `points_detector.py` and `task_parser.py`

**External API Changes:**
- Impact: Query sources return empty results
- Detection: Fewer search terms generated than expected
- Recovery: Monitor logs for API errors, implement fallback sources

**Rate Limiting/Banning:**
- Impact: API requests blocked, searches may fail
- Detection: HTTP 429/403 responses from APIs
- Recovery: Add delays, use rotating IPs/proxies (not implemented)

---

*Integrations analysis: 2026-03-20*
