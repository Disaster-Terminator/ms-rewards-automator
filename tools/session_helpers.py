"""
Shared helpers for scripts that need browser session management.
"""

import asyncio
from pathlib import Path


def get_storage_state_path() -> str | None:
    """Get storage_state path from config or default"""
    project_root = Path(__file__).parent.parent
    try:
        import yaml

        config_path = project_root / "config.yaml"
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            return config.get("account", {}).get("storage_state_path", "storage_state.json")
    except Exception:
        pass
    return "storage_state.json"


async def create_session_browser(playwright, headless: bool | None = None) -> tuple:
    """
    Create browser with optional session state.

    Args:
        playwright: Playwright instance
        headless: Override headless mode (None = auto based on session)

    Returns:
        Tuple of (browser, context, page, has_session)
    """
    storage_state = get_storage_state_path()
    project_root = Path(__file__).parent.parent
    storage_state_path = project_root / storage_state if storage_state else None
    has_session = storage_state_path and storage_state_path.exists()

    if headless is None:
        use_headless = has_session
    else:
        use_headless = headless

    browser = await playwright.chromium.launch(headless=use_headless)

    if has_session:
        context = await browser.new_context(storage_state=str(storage_state_path))
    else:
        context = await browser.new_context()

    page = await context.new_page()
    return browser, context, page, has_session


async def wait_for_login(page, context, has_session: bool, timeout: int = 60) -> bool:
    """
    Wait for login if needed.

    Args:
        page: Playwright page
        context: Browser context
        has_session: Whether session state was loaded
        timeout: Timeout in seconds for manual login

    Returns:
        True if logged in, False if timeout
    """
    if has_session:
        await asyncio.sleep(3)
        if "login" in page.url.lower():
            print("  ⚠ 会话已过期，需要重新登录")
            return False
        else:
            print("  ✓ 会话有效，跳过登录等待")
            return True

    print("\n" + "=" * 50)
    print("请在浏览器中完成登录")
    print("登录成功后会自动继续...")
    print("=" * 50)

    for _ in range(timeout):
        await asyncio.sleep(1)
        pages = context.pages
        if pages:
            current_page = pages[-1]
            url = current_page.url
            if "rewards.bing.com" in url and "login" not in url.lower():
                print(f"\n检测到登录成功: {url}")
                return True

    print("超时，请手动确认后按Enter继续...")
    try:
        input()
    except EOFError:
        pass
    return True
