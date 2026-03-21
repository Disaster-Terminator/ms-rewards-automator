# Codebase Concerns

**Analysis Date:** 2026-03-20

## Tech Debt

**Search Engine Complexity:**
- Issue: `src/search/search_engine.py` (732 lines) contains complex search logic with multiple modes (desktop, mobile), theme management, and extensive anti-ban features. This makes it difficult to maintain and test.
- Files: `src/search/search_engine.py`
- Impact: High risk of regression bugs when modifying search logic. Long function chains make debugging difficult.
- Fix approach: Consider breaking into smaller modules (SearchStrategy classes) or extracting theme/throttle management.

**Task Parser Selectors:**
- Issue: `src/tasks/task_parser.py` (656 lines) relies on hardcoded CSS selectors for Microsoft Rewards dashboard. DOM structure changes can break task detection.
- Files: `src/tasks/task_parser.py`, `src/account/points_detector.py`
- Impact: Task discovery and point detection may fail silently when Microsoft updates their dashboard.
- Fix approach: Implement selector validation/monitoring, add fallback selectors, create diagnostic mode to detect selector failures.

**Health Monitor Performance:**
- Issue: `src/infrastructure/health_monitor.py` (632 lines) uses frequent psutil calls and deque operations that can impact performance.
- Files: `src/infrastructure/health_monitor.py`
- Impact: Monitoring overhead can slow down execution, especially in headless mode.
- Fix approach: Reduce monitoring frequency, batch metrics collection, add sampling for expensive operations.

**Silent Exception Handling:**
- Issue: Over 100 instances of `except Exception: pass` across codebase, masking errors without proper logging.
- Files: `src/login/state_handler.py`, `src/login/login_detector.py`, `src/browser/state_manager.py`, `src/browser/element_detector.py`, and many others
- Impact: Errors are silently swallowed, making debugging difficult. Login failures, element detection failures, and network errors may go unnoticed.
- Fix approach: Replace `pass` with proper error logging, specific exception handling, and fallback strategies.

**Empty Return Values:**
- Issue: Multiple functions return empty lists `[]` without explanation or fallback behavior.
- Files: `src/search/bing_api_client.py`, `src/search/query_engine.py`, `src/login/handlers/logged_in_handler.py`, `src/browser/element_detector.py`
- Impact: Calling code cannot distinguish between "no results" and "error occurred".
- Fix approach: Return tuples (success, data) or raise exceptions with specific error types.

## Known Bugs

**TOTP Handler Edge Case:**
- Issue: If TOTP secret is malformed or empty, handler logs error but continues with empty secret, leading to invalid codes.
- Files: `src/login/handlers/totp_2fa_handler.py` (lines 105-122)
- Trigger: Malformed `totp_secret` in credentials config
- Workaround: Validate secret format before proceeding

**Login State Machine Infinite Loop:**
- Issue: Under certain network conditions, state machine may cycle between states without making progress but also without hitting max_transitions limit due to timing.
- Files: `src/login/login_state_machine.py` (line 99+)
- Trigger: Slow network causing timeout resets between state transitions
- Workaround: Max transitions limit provides some protection but edge cases exist

**Task Parser URL Filter Bypass:**
- Issue: Some internal Microsoft URLs not in skip_hrefs list, potentially causing navigation to unexpected pages.
- Files: `src/tasks/task_parser.py` (lines 14-32)
- Trigger: Dashboard links with relative paths or new URL patterns
- Workaround: Update skip list when new patterns discovered

## Security Considerations

**Credential Handling:**
- Risk: TOTP secrets and passwords are passed as plain strings through multiple handler classes without encryption.
- Files: `src/login/handlers/totp_2fa_handler.py`, `src/login/handlers/password_input_handler.py`, `src/account/manager.py`
- Current mitigation: Credentials typically read from environment variables
- Recommendations: Consider using a secure credential store (e.g., system keychain), implement credential masking in logs

**Storage State Exposure:**
- Risk: `storage_state.json` contains session tokens and cookies that grant account access.
- Files: `src/account/manager.py` (session persistence)
- Current mitigation: Recommended to add to `.gitignore` (verified present)
- Recommendations: Encrypt storage state file, add expiration checking

**Browser Launch Arguments:**
- Risk: Using `--password-store=basic` flag may leak password autofill data.
- Files: `src/browser/simulator.py` (line 104)
- Current mitigation: Using "basic" store avoids system keychain
- Recommendations: Document security implications, consider completely disabling autofill

**No Input Sanitization:**
- Risk: Search terms are not sanitized before being sent to Bing.
- Files: `src/search/search_engine.py`, `src/search/search_term_generator.py`
- Current mitigation: Query engine may filter some content
- Recommendations: Add input validation and sanitization for search terms

## Performance Bottlenecks

**Sequential Search Execution:**
- Problem: Desktop and mobile searches execute sequentially even when configured for parallelism.
- Files: `src/infrastructure/task_coordinator.py`, `src/search/search_engine.py`
- Cause: No parallel task execution framework implemented
- Improvement path: Implement asyncio.gather() for independent search operations

**Frequent DOM Reparsing:**
- Problem: Points detector and task parser repeatedly parse full DOM for each operation.
- Files: `src/account/points_detector.py`, `src/tasks/task_parser.py`
- Cause: No caching of parsed elements
- Improvement path: Add element caching within page context

**Heavy Monitoring Overhead:**
- Problem: Health monitor checks browser process every few seconds with psutil.
- Files: `src/infrastructure/health_monitor.py`
- Cause: Continuous polling for memory/CPU metrics
- Improvement path: Reduce check frequency, use event-based metrics where possible

**Large Query Cache:**
- Problem: Search term generator caches potentially unlimited queries in memory.
- Files: `src/search/search_term_generator.py`, `src/search/query_engine.py`
- Cause: No size limit on _query_cache
- Improvement path: Add LRU cache with size limit

## Fragile Areas

**Microsoft Rewards Dashboard Selectors:**
- Why fragile: Selectors are hardcoded and rely on specific DOM structure that changes frequently
- Files: `src/tasks/task_parser.py` (lines 38-100+), `src/account/points_detector.py` (lines 21-53)
- Safe modification: Use diagnostic mode to validate selectors before production changes
- Test coverage: Limited - no real browser tests in default CI

**Login State Detection:**
- Why fragile: Relies on URL patterns and element presence that can change with Microsoft login flow updates
- Files: `src/login/login_detector.py` (lines 350-370)
- Safe modification: Add fallback detection strategies, test with multiple account types
- Test coverage: Basic unit tests exist but limited real login scenarios

**External API Query Sources:**
- Why fragile: DuckDuckGo, Wikipedia, Bing Suggestions sources depend on external APIs that may change or rate-limit
- Files: `src/search/query_sources/duckduckgo_source.py`, `src/search/query_sources/wikipedia_source.py`, `src/search/query_sources/bing_suggestions_source.py`
- Safe modification: Add rate limiting, implement circuit breaker pattern, provide offline fallback
- Test coverage: Online sources tested in isolated tests only

**Theme Manager State:**
- Why fragile: Theme preferences stored in JSON and read on each run, could become inconsistent
- Files: `src/browser/theme_manager.py` (if exists), `src/infrastructure/state_monitor.py`
- Safe modification: Add state validation and migration on load
- Test coverage: Limited

## Scaling Limits

**Browser Context Reuse:**
- Current capacity: Single browser context per execution, mobile/desktop switching requires context recreation
- Limit: Memory leak risk with long-running sessions, context switching overhead
- Scaling path: Implement context pooling for production use

**Configuration Memory:**
- Current capacity: Full config held in memory throughout execution
- Limit: Minimal impact for single-instance, but multiple concurrent runs would duplicate config
- Scaling path: Consider singleton pattern for config

**Log File Growth:**
- Current capacity: 10MB × 5 files rotation, 30-day retention
- Limit: Disk space for high-frequency executions
- Scaling path: Implement log archival to object storage or reduce retention

**State Machine History:**
- Current capacity: Unbounded deque for state transitions in LoginStateMachine
- Limit: Memory growth in long-running sessions with many transitions
- Scaling path: Add maxlen to deques or implement periodic cleanup

## Dependencies at Risk

**playwright-stealth:**
- Risk: Third-party package with limited maintenance, may not keep up with Playwright updates
- Impact: Anti-detection features may fail with Playwright updates, causing account bans
- Migration plan: Monitor for updates, consider implementing custom stealth features or using alternatives

**beautifulsoup4 + lxml:**
- Risk: DOM parsing libraries, changes to HTML structure could cause parsing failures
- Impact: Task parsing and point detection could break
- Migration plan: Keep versions updated, add parser validation in diagnostics

**aiohttp:**
- Risk: HTTP client used for external API queries
- Impact: Query sources (DuckDuckGo, Wikipedia) may fail with API changes
- Migration plan: Add retry logic, circuit breaker, fallback sources

**pyyaml:**
- Risk: Configuration parsing
- Impact: Config loading failures if YAML format changes
- Migration plan: Minimal risk, maintain config validation

## Missing Critical Features

**No End-to-End Test Automation:**
- Problem: Only 1 integration test file exists despite CLAUDE.md mentioning comprehensive tests
- Blocks: Validating full user workflows, regression testing

**No Real Browser Test Suite:**
- Problem: Tests marked `real` are skipped by default
- Blocks: Detecting login flow changes, selector changes in production

**No Load Testing:**
- Problem: No performance/load testing infrastructure
- Blocks: Validating behavior under stress or with multiple accounts

**No Security Test Suite:**
- Problem: No dedicated security testing
- Blocks: Validating credential handling, session security

**No Circuit Breaker for External APIs:**
- Problem: Query sources can fail repeatedly without stopping
- Blocks: System continues to hammer failing APIs, causing delays

## Test Coverage Gaps

**Login Handlers Not Fully Tested:**
- What's not tested: 10+ login handlers (email_input, password, TOTP, passwordless, etc.)
- Files: `src/login/handlers/*.py`
- Risk: Handler failures only discovered in production
- Priority: High

**Task Handlers Not Tested:**
- What's not tested: URL reward tasks, quiz tasks, poll tasks execution logic
- Files: `src/tasks/handlers/*.py`
- Risk: Task completion may fail silently, incorrect point calculation
- Priority: High

**Points Detector Not Tested:**
- What's not tested: DOM parsing logic for extracting points from dashboard
- Files: `src/account/points_detector.py`
- Risk: Points tracking failures, incorrect reward calculations
- Priority: High

**Search Engine Not Tested:**
- What's not tested: Search execution with different configurations
- Files: `src/search/search_engine.py`
- Risk: Search failures not caught before production
- Priority: Medium

**Browser Simulator Not Tested:**
- What's not tested: Browser launch, context creation, anti-ban features
- Files: `src/browser/simulator.py`, `src/browser/anti_ban_module.py`
- Risk: Browser failures only discovered in production
- Priority: Medium

---

*Concerns audit: 2026-03-20*