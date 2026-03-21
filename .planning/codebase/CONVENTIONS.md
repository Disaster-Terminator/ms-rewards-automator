# Coding Conventions

**Analysis Date:** 2026-03-20

## Naming Patterns

**Files:**
- snake_case: `config_manager.py`, `login_state_machine.py`
- test_ prefix: `test_config_manager.py`, `test_login_state_machine.py`

**Functions:**
- snake_case: `get_config()`, `execute_searches()`, `is_logged_in()`
- async functions: prefixed with `async def`

**Variables:**
- snake_case: `config_path`, `storage_state_path`, `login_url`
- Private methods: leading underscore `_register_state_handlers()`

**Types:**
- PascalCase classes: `ConfigManager`, `LoginStateMachine`, `AccountManager`
- Enum values: UPPER_CASE with underscore: `LoginState.EMAIL_INPUT`, `LoginState.PASSWORD_INPUT`
- Type aliases: defined with `TypeAlias`

**Constants:**
- UPPER_CASE: `DEFAULT_CONFIG`, `EXECUTION_MODE_PRESETS`, `REWARDS_URLS`

## Code Style

**Formatting:**
- Tool: Ruff (v0.8.0+)
- Line length: 100 characters (enforced in `pyproject.toml`)
- Indentation: 2 spaces (not 4)
- Quote style: Double quotes (enforced by ruff format)
- No magic trailing commas

**Linting:**
- Tool: Ruff (rules: E, W, F, I, B, C4, UP)
- Ignored rules:
  - `E501` (line length - handled by config)
  - `B008` (function call in argument - sometimes needed)
  - `C901` (function complexity - temporarily allowed)

**Key ruff configuration** (from `pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501", "B008", "C901"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**Type Checking:**
- Tool: MyPy (v1.14.0+)
- Python version: 3.10
- Configuration: `warn_return_any = true`, `warn_unused_configs = true`

## Import Organization

**Order (enforced by isort):**
1. Standard library: `import logging`, `import os`, `from typing import Any`
2. Third-party: `import yaml`, `import pytest`, `from playwright.async_api import BrowserContext`
3. First-party (project): `from constants import REWARDS_URLS`, `from browser.page_utils import ...`
4. Relative imports: `from .handlers import ...`

**Path Aliases:**
- No path aliases configured
- Imports use relative paths from `src/` directory
- Pythonpath set to `src` in pytest config

**isort known first-party packages:**
```toml
[tool.ruff.lint.isort]
known-first-party = ["src", "infrastructure", "browser", "login", "search", "account", "tasks", "ui"]
```

## Error Handling

**Patterns:**
- Logging with module-level logger: `logger = logging.getLogger(__name__)`
- Graceful degradation: return default values when config missing
- Exception handling: try/except/finally blocks for resource cleanup
- Error propagation: raise exceptions with context

**Example from `src/infrastructure/config_manager.py`:**
```python
logger = logging.getLogger(__name__)

try:
    with open(config_path, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f)
except Exception:
    logger.warning(f"无法加载配置文件: {config_path}, 使用默认配置")
    user_config = {}
```

**Validation:**
- ConfigValidator class for validation
- Fallback to defaults on invalid config
- Type checking on config values

## Logging

**Framework:** Python standard library `logging`

**Patterns:**
- Module-level logger: `logger = logging.getLogger(__name__)`
- Log levels: DEBUG (detailed), INFO (progress), WARNING (issues), ERROR (failures)
- Context in logs: include relevant data in log messages

**Examples:**
```python
logger.info("账户管理器初始化完成")
logger.warning(f"无法加载配置文件: {config_path}")
logger.error(f"登录失败: {error_message}")
```

## Comments

**When to Comment:**
- Complex logic: explain non-obvious behavior
- Workarounds: document why code deviates from ideal
- Chinese comments: used throughout codebase for context

**JSDoc/TSDoc:**
- Not used (Python docstrings in Chinese instead)
- Module-level docstrings explain purpose

**Example:**
```python
"""
配置管理器模块
负责加载、验证和提供配置参数
"""
```

## Function Design

**Size:** No strict limits (C901 ignored), but prefer focused functions

**Parameters:**
- Type annotated: `def __init__(self, config: ConfigManager)`
- Optional parameters with defaults: `def get(self, key: str, default=None)`
- Multiple parameters on separate lines when needed

**Return Values:**
- Always type annotated
- Return `None` for void functions (explicit)
- Use Optional for nullable returns

**Examples:**
```python
def __init__(self, config: ConfigManager) -> None:
    """初始化账户管理器"""
    ...

def get(self, key: str, default: Any = None) -> Any:
    """获取配置项"""
    ...

async def handle_login(self, context: BrowserContext) -> bool:
    """处理登录流程"""
    ...
```

## Module Design

**Exports:**
- Explicit exports via `__all__` where needed
- Generally uses module-level imports

**Barrel Files:**
- No explicit barrel files
- Package `__init__.py` files exist for organization

**Async/Await:**
- Mandatory for asynchronous operations
- AsyncIO-based patterns throughout
- Never use `@asyncio.coroutine` decorator

**Example:**
```python
async def execute_desktop_searches(
    self, page: Page, count: int, health_monitor=None
) -> bool:
    """执行桌面搜索"""
    for i in range(count):
        search_term = await self.search_term_generator.generate()
        await page.goto(bing_search_url)
        await self.anti_ban_module.random_delay()
    return True
```

## Pre-Commit Hooks

**Configuration:** `.pre-commit-config.yaml`

**Hooks:**
- Ruff linter (auto-fix): `ruff --fix --exit-non-zero-on-fix`
- Ruff formatter: `ruff-format`

**Usage:**
```bash
pre-commit run --all-files
```

---

*Convention analysis: 2026-03-20*