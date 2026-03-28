# E2E & Smoke Test Suite

This directory contains comprehensive end-to-end (E2E) and smoke tests for RewardsCore. Tests use **Playwright** for real browser automation and are designed for fast feedback and high reliability.

## Test Structure

```
tests/e2e/
├── conftest.py              # Shared fixtures (browser, context, page)
├── smoke/                   # Quick validation (<30s total)
│   ├── conftest.py         # Profiling + flakiness tracking
│   ├── helpers/
│   │   └── flakiness.py    # Flakiness analysis
│   ├── test_environment.py # Environment validation (02-01)
│   ├── test_bing_health.py # Bing accessibility (02-01)
│   ├── test_search_execution.py  # Core smoke tests (02-02)
│   └── test_performance_gate.py  # Performance assertions (02-02)
├── login/                   # Authentication tests (requires credentials)
├── search/                  # Search functionality tests
├── tasks/                   # Task system tests
├── helpers/                 # Shared utilities
│   ├── environment.py      # CI/local detection
│   ├── screenshot.py       # Failure capture
│   └── decorators.py       # Test decorators
├── data/                    # Test data and scenarios
└── fixtures/               # Mock data and fixtures
```

## Quick Start

### Prerequisites

```bash
# Install dependencies (includes Playwright)
pip install -e ".[dev]"

# Install Chromium browser
playwright install chromium

# Verify environment
python tools/check_environment.py
```

### Running Tests

**Smoke Tests (fast, no credentials)**

```bash
# Full smoke suite (recommended for quick validation)
pytest tests/e2e/smoke/ -v

# Single smoke test file
pytest tests/e2e/smoke/test_search_execution.py -v

# Single test
pytest tests/e2e/smoke/test_search_execution.py::TestSearchExecution::test_basic_search_returns_results -v

# With verbose output and short traceback
pytest tests/e2e/smoke/ -v --tb=short
```

**All E2E Tests (includes login tests - requires credentials)**

```bash
# Full E2E suite
pytest tests/e2e/ -v

# Only tests requiring login
pytest tests/e2e/ -v -m "requires_login"

# Only smoke (no login)
pytest tests/e2e/ -v -m "no_login"
```

**Performance Profiling**

```bash
# Run smoke suite with profiling (always enabled)
pytest tests/e2e/smoke/ -v

# Check profile output
cat logs/e2e/smoke/profile.json
```

**Flakiness Detection**

```bash
# Run smoke suite 5 times to establish baseline
for i in 1 2 3 4 5; do
  pytest tests/e2e/smoke/ -q --tb=no
done

# Check flakiness report (included in profile.json)
cat logs/e2e/smoke/profile.json | grep -A 20 "flakiness_report"

# Or use Python to generate report
python -c "from tests.e2e.smoke.helpers.flakiness import get_flakiness_report; import json; print(json.dumps(get_flakiness_report(window=5), indent=2))"
```

### Headless vs. Headed

- **Local development**: Default is headed (browser visible) for easier debugging
- **CI environment**: Automatically uses headless mode
- **Override**: Set `E2E_HEADLESS=true` or `E2E_HEADLESS=false` environment variable

```bash
# Force headless
E2E_HEADLESS=true pytest tests/e2e/smoke/ -v

# Force headed
E2E_HEADLESS=false pytest tests/e2e/smoke/ -v
```

### Test Markers

- `smoke`: Quick validation tests (<30s total suite)
- `e2e`: Full end-to-end tests
- `slow`: Tests taking >2 minutes
- `no_login`: Tests that run without authentication
- `requires_login`: Tests needing authenticated session

Use `-m` to select markers:

```bash
pytest tests/e2e/ -v -m "smoke and not slow"
```

## Interpreting Results

### Success Indicators

- ✅ All tests green → Environment healthy, ready for E2E development
- ✅ Total time <30s (local) or <45s (CI) → see `profile.json`
- ✅ Flakiness report shows no unstable tests (pass rate ≥95%)

### Common Failures

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| `Browser launch failed` | Playwright browsers not installed | `playwright install chromium` |
| `Timeout navigating to bing.com` | Network/firewall issues | Check internet access, proxy settings |
| `Search box not found` | Bing DOM changed | Update selector (currently `input[name='q']`) |
| `Tests pass individually but fail as suite` | State leakage | Ensure `context` fixture is function-scoped (already configured) |
| `Timeout >30s` | Slow network or CI resource limits | Run headless (`--headless`), check CI performance |

### Flakiness Alert

If you see:

```
FLAKINESS ALERT: The following tests are unstable:
  - test_something: 80.0% pass rate (4/5)
```

Investigate:
1. Check if selectors are too brittle (prefer `get_by_role()` over CSS classes)
2. Increase timeout values
3. Check network stability
4. Review screenshots in `logs/e2e/run_<timestamp>/screenshots/`

If flakiness persists, consider:
- Temporarily skipping the test with `pytest.mark.skip(reason="flaky")`
- Redesigning the test with more robust wait strategies
- Quarantining until fixed (create `pytest.ini` with `addopts = -k "not flaky_test"`)

## Outputs

After running tests, the following artifacts are generated:

```
logs/e2e/
├── smoke/
│   └── profile.json          # Suite performance metrics and flakiness report
├── flakiness.jsonl           # Append-only history of all test outcomes
└── run_<timestamp>/
    ├── screenshots/          # Failure screenshots (if test fails)
    └── dom_snapshots/        # DOM dumps on failure (optional)
```

### Profile JSON Structure

```json
{
  "total_seconds": 25.3,
  "passed": true,
  "threshold": 30,
  "ci": false,
  "session_id": 1711272834,
  "tests": [
    {"name": "test_basic_search_returns_results", "duration": 8.2, "passed": true},
    {"name": "test_multiple_searches_stable", "duration": 16.1, "passed": true}
  ],
  "flakiness_report": {
    "tests/e2e/smoke/test_search_execution.py::TestSearchExecution::test_basic_search_returns_results": {
      "pass_rate": 1.0,
      "total_runs": 5,
      "passed": 5,
      "flaky": false
    }
  }
}
```

## Quality Gates

Before committing code or opening a PR, ensure:

1. **Smoke suite passes**: `pytest tests/e2e/smoke/ -v`
2. **Performance threshold**: Total duration <30s local / <45s CI (checked automatically)
3. **Flakiness baseline**: At least 5 consecutive runs show ≥95% pass rate (≤1 failure)
4. **Static checks**: `ruff check . && ruff format --check .`
5. **Unit tests**: `pytest tests/unit/ -v -m "not real"`

CI will typically run:

```yaml
- name: Run smoke tests
  run: pytest tests/e2e/smoke/ -v
- name: Check performance gate
  run: pytest tests/e2e/smoke/test_performance_gate.py -v
- name: Upload artifacts
  run: |
    cp logs/e2e/smoke/profile.json ${{ runner.temp }}/
    cp logs/e2e/flakiness.jsonl ${{ runner.temp }}/
```

## Login E2E Tests

Tests covering authentication flows: fresh login, session persistence, 2FA, edge cases.

### Prerequisites

- Test account credentials in environment:
  ```bash
  export MS_REWARDS_E2E_EMAIL=user@outlook.com
  export MS_REWARDS_E2E_PASSWORD=secret
  export MS_REWARDS_E2E_TOTP_SECRET=  # Optional: for 2FA accounts
  ```

- Optional: `tests/e2e/fixtures/storage_state.json` for faster tests (generated via `scripts/save_storage_state.py`)

### Running

```bash
# All login tests with parallel execution
python -m pytest -n auto tests/e2e/login/ -v

# Only tests requiring credentials
python -m pytest -n auto tests/e2e/login/ -v -m "requires_login"

# Skip slow tests
python -m pytest -n auto tests/e2e/login/ -v -m "not slow"
```

### Test Categories

| Test File | Coverage |
|-----------|----------|
| `test_login_flow.py` | Fresh login, 2FA, success path |
| `test_session_persistence.py` | Storage state reuse, session survival |
| `test_already_logged_in.py` | Already-authenticated scenarios |
| `test_login_edge_cases.py` | Invalid password, redirects, cleanup |
| `test_multi_account.py` | Parametrized tests across multiple accounts |

### Interpreting Results

- ✅ All green → Login infrastructure healthy, proceed to search tests
- ⚠️ Skipped tests → Expected if credentials not configured
- ❌ 2FA failures → Check TOTP secret matches Microsoft Authenticator
- ❌ Redirect failures → Verify account not locked (health check)

## Search E2E Tests (No-Login Mode)

### Why No-Login First?

- **Reduced risk**: No account lockout from automated searches
- **Parallelizable**: Can run multiple instances simultaneously
- **Fast**: No login overhead (2FA, redirects)
- **Reliable**: Less state, fewer moving parts

### Running No-Login Tests

```bash
# Only no-login tests (with parallel execution)
pytest -n auto tests/e2e/search/ -v -m "no_login"

# With parametrized search terms (runs 10+ times)
pytest -n auto tests/e2e/search/test_search_no_login.py::TestSearchNoLogin::test_parametrized_search_terms -v

# All search tests (includes with-login)
pytest -n auto tests/e2e/search/ -v
```

### Test Coverage

| Test File | Coverage |
|-----------|----------|
| `test_search_no_login.py` | Basic search, autocomplete, tabs (images/videos) |
| `test_consent_handling.py` | Cookie consent acceptance/ignorance |

### Expected Behavior

- ✅ All tests should pass without any credentials configured
- ✅ Bing homepage loads reliably (<5s)
- ✅ Search results appear within 10s
- ✅ Cookie consent handled automatically

### Troubleshooting

- **Results not appearing**: Check Bing accessibility, network connectivity
- **Autocomplete not showing**: May depend on region; test may skip
- **Images/Videos tabs missing**: Region-specific features; skip acceptable

## Configuration

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `E2E_HEADLESS` | Run browser in headless mode | `true` in CI, `false` locally |
| `E2E_SEARCH_COUNT` | Override search count for E2E tests | `2` |
| `CI` | Auto-detected CI environment | N/A |

### pytest.ini Markers

Ensure these markers are defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "smoke: quick validation tests (<30s total suite)",
    "e2e: full end-to-end tests",
    "slow: tests taking >2 minutes",
    "no_login: tests that run without authentication",
    "requires_login: tests needing authenticated session",
]
```

## Troubleshooting

### "Playwright not installed"

```bash
playwright install chromium
# Or with dependencies
playwright install --with-deps chromium
```

### Selectors failing

Bing's DOM may change. Update selectors in test files:

- Search input: `input[name='q']` (stable)
- Results: `.b_algo` (may change to `.b_content` or similar)
- Use `page.get_by_role()` when possible for more resilient selectors

### Tests pass locally but fail in CI

- Check CI resource limits (memory, CPU)
- Add explicit waits for network idle: `await page.wait_for_load_state("networkidle")`
- Increase timeout values in tests
- Disable animations in CI: `await page.add_style_tag(content="* { animation: none !important; transition: none !important; }")`

## Contributing

When adding new smoke tests:

1. Use `pytest.mark.smoke` and `pytest.mark.no_login` (if applicable)
2. Add `track_smoke_duration` fixture to measure execution time
3. Keep tests fast (<10s each)
4. Use robust selectors (avoid hardcoded CSS classes that may change)
5. Update this README if adding new test categories
6. Run flakiness check: 5 consecutive runs should pass

## Phase Progress

- ✅ **02-01**: Environment validation, Bing health tests
- ✅ **02-02**: Search execution, flakiness tracking, performance gates
- ✅ **02-03**: Login E2E tests (Happy path, persistence, edge cases)
- ✅ **02-04**: Search E2E tests (No-login mode)
- ⏳ **02-05**: Search E2E tests with login
- ⏳ **02-06**: Task E2E tests
- ⏳ **02-07**: CI/CD integration
