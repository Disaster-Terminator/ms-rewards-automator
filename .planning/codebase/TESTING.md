# Testing Patterns

**Analysis Date:** 2026-03-20

## Test Framework

**Runner:**
- pytest (v8.0.0+)
- Config: `pyproject.toml` [tool.pytest.ini_options]
- Async support: pytest-asyncio (v0.24.0+)

**Assertion Library:**
- pytest built-in assertions
- unittest.mock for mocking

**Additional Tools:**
- pytest-cov (v6.0.0+) for coverage
- pytest-xdist (v3.5.0+) for parallel testing
- pytest-timeout (v2.3.0+) for test timeouts
- pytest-benchmark (v5.0.0+) for performance tests
- hypothesis (v6.125.0+) for property-based testing

**Run Commands:**
```bash
# Quick unit tests (recommended for daily development)
pytest tests/unit/ -v --tb=short -m "not real and not slow"

# Full unit tests (includes slow tests)
pytest tests/unit/ -v --tb=short -m "not real"

# Real browser tests (requires credentials)
pytest tests/unit/ -v -m "real"

# Integration tests
pytest tests/integration/ -v --tb=short

# Property-based tests
pytest tests/ -v -m "property"

# Performance benchmarks
pytest tests/ -v -m "performance"

# With coverage
pytest tests/unit/ -v --cov=src --cov-report=html --cov-report=term

# Parallel testing (4 workers)
pytest tests/unit/ -v -n 4

# Last failed tests
pytest --last-failed

# Failed first (retry failures)
pytest --failed-first
```

## Test File Organization

**Location:**
- Co-located with source in `tests/` directory
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Fixtures: `tests/fixtures/`
- Manual tests: `tests/manual/`

**Naming:**
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Fixtures: `conftest.py`, `mock_*.py`

**Structure:**
```
tests/
├── conftest.py                # Global pytest configuration
├── fixtures/
│   ├── conftest.py            # Fixture definitions
│   ├── mock_accounts.py      # Mock account data
│   └── mock_dashboards.py    # Mock dashboard data
├── unit/                      # Unit tests (recommended)
│   ├── test_config_manager.py
│   ├── test_login_state_machine.py
│   ├── test_task_manager.py
│   └── ...
└── integration/               # Integration tests
    └── test_query_engine_integration.py
```

## Test Structure

**Suite Organization:**
```python
class TestConfigManager:
    """ConfigManager 单元测试类"""

    def test_load_valid_config(self):
        """测试加载有效配置文件"""
        ...

    def test_missing_config_uses_defaults(self):
        """测试缺失配置项使用默认值"""
        ...
```

**Patterns:**
- Clear test names: `test_<feature>_<expected_behavior>`
- Descriptive docstrings in Chinese
- AAA pattern: Arrange, Act, Assert
- Independent tests (no shared state)

**Setup/Teardown:**
- pytest fixtures with appropriate scopes
- tmp_path for file operations
- Auto-cleanup via pytest

## Mocking

**Framework:** unittest.mock (built-in)

**Patterns:**
```python
from unittest.mock import MagicMock, AsyncMock, Mock

# Mock synchronous methods
def test_something():
    mock_config = MagicMock()
    mock_config.get.side_effect = lambda key, default=None: {...}

# Mock async methods
async def test_async_method():
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock(return_value=mock_response)
    mock_page.wait_for_selector = AsyncMock()

# Mock specific attributes
def test_with_mock_logger():
    logger = Mock()
    manager = AccountManager(config, logger=logger)
    logger.info.assert_called_once()
```

**Common Mock Objects (from `tests/conftest.py`):**
- `temp_workspace`: tmp_path fixture for file operations
- `mock_logger`: session-scoped mock logger
- `mock_config`: module-scoped mock ConfigManager
- `mock_browser_context`: module-scoped mock Playwright BrowserContext

**What to Mock:**
- External services (Playwright, HTTP clients)
- File I/O operations
- Time-dependent functionality
- Configuration loading

**What NOT to Mock:**
- Business logic in unit tests
- Internal method interactions (test the real thing)
- Simple data transformations

## Fixtures and Factories

**Test Data:**
- Located in `tests/fixtures/`
- Mock data in `mock_accounts.py`, `mock_dashboards.py`

**Example Fixture Pattern:**
```python
# tests/fixtures/mock_accounts.py
@pytest.fixture
def mock_valid_account():
    return {
        "email": "test@example.com",
        "password": "test_password",
        "totp_secret": "JBSWY3DPEHPK3PXP"
    }

@pytest.fixture
def mock_session_state():
    return {
        "cookies": [{"name": "auth", "value": "token123"}],
        "origins": [{"origin": "https://rewards.bing.com", "localStorage": {}}]
    }
```

**Location:**
- Global fixtures: `tests/conftest.py`
- Module fixtures: `tests/fixtures/conftest.py`
- Local fixtures: test file-scoped

## Coverage

**Requirements:** Not explicitly enforced, but tracked

**View Coverage:**
```bash
# Generate HTML coverage report
pytest tests/unit/ --cov=src --cov-report=html

# Terminal report
pytest tests/unit/ --cov=src --cov-report=term

# Show missing lines
pytest tests/unit/ --cov=src --cov-report=term-missing
```

**Configuration** (from `pyproject.toml`):
```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*", "*/site-packages/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
show_missing = true
skip_covered = true
```

## Test Markers

**Available Markers:**
```python
@pytest.mark.unit           # Unit tests (fast, isolated)
@pytest.mark.integration    # Integration tests (medium speed)
@pytest.mark.e2e           # End-to-end tests (slow)
@pytest.mark.slow          # Slow tests (skip with -m "not slow")
@pytest.mark.real          # Real browser tests (skip with -m "not real")
@pytest.mark.property      # Hypothesis property-based tests
@pytest.mark.performance   # Performance benchmarks
@pytest.mark.reliability   # Reliability and error recovery
@pytest.mark.security      # Security and anti-detection
```

**Default Filter:**
- Set in `pyproject.toml`: `addopts = "-v --tb=short --strict-markers -m 'not real'"`
- Skips real browser tests by default

**Usage:**
```bash
# Run only unit tests
pytest tests/unit/ -v -m "unit"

# Run unit + integration
pytest tests/ -v -m "unit or integration"

# Run all except slow
pytest tests/ -v -m "not slow"
```

## Test Types

**Unit Tests:**
- Scope: Individual components in isolation
- Location: `tests/unit/`
- Examples: `test_config_manager.py`, `test_login_state_machine.py`
- Characteristics: Fast, no external dependencies, mocked collaborators

**Integration Tests:**
- Scope: Multiple components working together
- Location: `tests/integration/`
- Examples: `test_query_engine_integration.py`
- Characteristics: Medium speed, real components, tested end-to-end

**E2E Tests:**
- Scope: Full workflow tests
- Location: Not extensively used
- Framework: pytest-playwright
- Characteristics: Slow, requires real browser, full environment

**Property-Based Tests:**
- Framework: Hypothesis (v6.125.0+)
- Configuration: Hypothesis profiles (default, ci, dev)
- Usage: Random input generation with assertions

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_async_login():
    """Test async login flow"""
    result = await account_manager.login(page)
    assert result is True
    page.goto.assert_called_once()
```

**Error Testing:**
```python
def test_config_invalid_yaml():
    """Test handling of invalid YAML config"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content: [")
        config_path = f.name

    try:
        manager = ConfigManager(config_path)
        # Should fallback to defaults
        assert manager.get("search.desktop_count") == 20
    finally:
        os.unlink(config_path)
```

**Fixture with Parameters:**
```python
@pytest.fixture(params=[10, 20, 30])
def search_count(request):
    """Parameterized fixture for different search counts"""
    return request.param
```

**Temporary Files:**
```python
def test_with_temp_config():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"search": {"desktop_count": 25}}, f)
        config_path = f.name
    try:
        manager = ConfigManager(config_path)
        assert manager.get("search.desktop_count") == 25
    finally:
        os.unlink(config_path)
```

## Hypothesis Configuration

**Profiles:**
```python
# tests/conftest.py
settings.register_profile(
    "default",
    max_examples=100,
    deadline=5000,  # 5 seconds
    print_blob=True,
)

settings.register_profile(
    "ci",
    max_examples=200,
    deadline=10000,  # 10 seconds
    print_blob=True,
)

settings.register_profile(
    "dev",
    max_examples=50,
    deadline=None,  # No deadline
    verbosity=Verbosity.verbose,
)
```

**Usage:**
```bash
HYPOTHESIS_PROFILE=ci pytest tests/ -v -m "property"
```

---

*Testing analysis: 2026-03-20*