"""
预检认证模块的单元测试

测试覆盖所有核心 blocker 场景：
- 文件不存在
- 文件不可读
- Windows 路径
- 无效 JSON
- 缺少 cookies 字段
- 有效文件通过
"""

import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from infrastructure.preflight import PreflightBlocker, PreflightChecker, run_preflight_and_exit


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_state():
    """返回有效的 storage_state 字典"""
    return {
        "cookies": [{"name": "test", "value": "val", "domain": ".bing.com", "path": "/", "expires": 999}],
        "origins": [{"origin": "https://www.bing.com"}],
    }


# ============================================================================
# Core Blocker Tests
# ============================================================================


@pytest.mark.asyncio
async def test_missing_file_blocks():
    """测试：文件不存在时返回 MISSING_FILE blocker"""
    config = MagicMock()
    config.get.return_value = "/nonexistent/storage_state.json"
    checker = PreflightChecker(config)

    with patch("os.path.exists", return_value=False):
        blockers = await checker.validate(require_logged_in=False)

    assert len(blockers) == 1
    blocker = blockers[0]
    assert blocker.code == "MISSING_FILE"
    assert "不存在" in blocker.message
    assert blocker.exit_code == 1


@pytest.mark.asyncio
async def test_unreadable_file_blocks():
    """测试：文件不可读时返回 UNREADABLE_FILE blocker"""
    config = MagicMock()
    config.get.return_value = "/tmp/unreadable.json"
    checker = PreflightChecker(config)

    with patch("os.path.exists", return_value=True), patch("os.access", return_value=False):
        blockers = await checker.validate(require_logged_in=False)

    assert len(blockers) == 1
    blocker = blockers[0]
    assert blocker.code == "UNREADABLE_FILE"
    assert blocker.exit_code == 2


@pytest.mark.asyncio
async def test_windows_path_blocks(valid_state):
    """测试：Windows 挂载路径返回 WINDOWS_PATH blocker"""
    win_path = "/mnt/c/Users/test/storage_state.json"
    config = MagicMock()
    config.get.return_value = win_path
    checker = PreflightChecker(config)

    json_str = json.dumps(valid_state)
    m = mock_open(read_data=json_str)
    with patch("os.path.exists", return_value=True), patch("os.access", return_value=True), patch(
        "builtins.open", m
    ):
        blockers = await checker.validate(require_logged_in=False)

    assert len(blockers) == 1
    blocker = blockers[0]
    assert blocker.code == "WINDOWS_PATH"
    assert "Windows 挂载" in blocker.message or "WSL" in blocker.message
    assert blocker.exit_code == 3


@pytest.mark.asyncio
async def test_invalid_json_blocks(tmp_path):
    """测试：无效 JSON 返回 INVALID_JSON blocker"""
    file_path = tmp_path / "invalid.json"
    file_path.write_text("{ invalid json content }")

    config = MagicMock()
    config.get.return_value = str(file_path)
    checker = PreflightChecker(config)
    blockers = await checker.validate(require_logged_in=False)

    assert len(blockers) == 1
    blocker = blockers[0]
    assert blocker.code == "INVALID_JSON"
    assert blocker.exit_code == 4


@pytest.mark.asyncio
async def test_missing_cookies_blocks(tmp_path):
    """测试：缺少 cookies 字段返回 MISSING_COOKIES blocker"""
    file_path = tmp_path / "no_cookies.json"
    file_path.write_text('{"origins": []}')

    config = MagicMock()
    config.get.return_value = str(file_path)
    checker = PreflightChecker(config)
    blockers = await checker.validate(require_logged_in=False)

    assert len(blockers) == 1
    blocker = blockers[0]
    assert blocker.code == "MISSING_COOKIES"
    assert "cookies" in blocker.message
    assert blocker.exit_code == 5


@pytest.mark.asyncio
async def test_valid_file_passes_preflight(tmp_path, valid_state):
    """测试：有效文件通过预检"""
    file_path = tmp_path / "valid.json"
    file_path.write_text(json.dumps(valid_state))

    config = MagicMock()
    config.get.return_value = str(file_path)
    checker = PreflightChecker(config)
    blockers = await checker.validate(require_logged_in=False)

    assert len(blockers) == 0


@pytest.mark.asyncio
async def test_validation_order_fails_fast(valid_state):
    """测试：检查顺序是 fast-fail 的（文件不存在时不继续后面的检查）"""
    config = MagicMock()
    config.get.return_value = "/nonexistent/file.json"
    checker = PreflightChecker(config)

    # 即使文件路径是 Windows 格式，如果文件不存在也应该立即返回 MISSING_FILE
    win_path = "/mnt/c/nonexistent/file.json"
    config.get.return_value = win_path

    with patch("os.path.exists", return_value=False):
        blockers = await checker.validate(require_logged_in=False)

    # 应该只返回一个 blocker，且是 MISSING_FILE，而不是 WINDOWS_PATH
    assert len(blockers) == 1
    assert blockers[0].code == "MISSING_FILE"


@pytest.mark.asyncio
async def test_formatter_output():
    """测试：format_blocker_message 输出格式正确"""
    config = MagicMock()
    checker = PreflightChecker(config)
    blocker = PreflightBlocker("TEST_CODE", "Test message", "Test resolution", 99)
    formatted = checker.format_blocker_message(blocker)

    assert "[TEST_CODE]" in formatted
    assert "Test message" in formatted
    assert "Resolution: Test resolution" in formatted


# ============================================================================
# run_preflight_and_exit tests
# ============================================================================


@pytest.mark.asyncio
@patch("sys.exit")
async def test_run_preflight_and_exit_success(mock_exit):
    """测试：预检通过时退出码 0"""
    config = MagicMock()
    with patch.object(PreflightChecker, "validate", return_value=[]):
        await run_preflight_and_exit(config)
        mock_exit.assert_called_once_with(0)


@pytest.mark.asyncio
@patch("sys.exit")
async def test_run_preflight_and_exit_with_blocker(mock_exit):
    """测试：有 blocker 时退出码为 blocker.exit_code"""
    config = MagicMock()
    blocker = PreflightBlocker("TEST", "Test error", "Fix it", 42)
    with patch.object(PreflightChecker, "validate", return_value=[blocker]):
        await run_preflight_and_exit(config)
        mock_exit.assert_called_once_with(42)


# ============================================================================
# Smoke test - simplified (manual verification recommended)
# ============================================================================


@pytest.mark.asyncio
async def test_smoke_test_skipped_when_not_required(tmp_path, valid_state):
    """测试：require_logged_in=False 时不执行 smoke test（快速通过）"""
    file_path = tmp_path / "valid.json"
    file_path.write_text(json.dumps(valid_state))

    config = MagicMock()
    config.get.return_value = str(file_path)
    checker = PreflightChecker(config)

    # 验证即使有 require_logged_in=False，也快速完成（不调用 PLAYWRIGHT）
    # 由于 smoke test 只在 require_logged_in=True 执行，这里只验证基本流程
    blockers = await checker.validate(require_logged_in=False)
    assert len(blockers) == 0
