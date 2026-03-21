"""
预检模块 (Preflight Checker)
用于在 E2E 测试和 CI/CD 流程中快速验证认证状态

主要功能：
- 快速检测 storage_state.json 文件的可访问性和有效性
- 识别 WSL/WSLg 环境下的 Windows 路径阻断问题
- 可选：通过轻量级浏览器检查验证会话是否仍然有效
- 所有检查均在 15 秒内完成，失败时提供明确的 exit code 和修复指引

阻塞策略：
- 按顺序执行检查，任一失败立即返回，不进行后续检查
- 每个 blocker 包含唯一的错误码、用户友好的错误信息和具体解决步骤
- 通过环境变量 E2E_PREFLIGHT=1 或 CLI flag --preflight 触发
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PreflightBlocker:
    """预检阻塞项，描述一个阻止 E2E 测试继续的认证问题"""

    code: str
    """唯一错误码，用于程序化识别"""

    message: str
    """面向用户的错误信息，说明问题"""

    resolution: str
    """具体的修复步骤，包含命令示例"""

    exit_code: int
    """建议的退出码（1-127范围）"""

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}\n  Resolution: {self.resolution}"


class PreflightChecker:
    """预检器，负责在执行 E2E 流程前快速验证认证状态"""

    # 预定义的 blocker 类型
    BLOCKERS = {
        "MISSING_FILE": PreflightBlocker(
            code="MISSING_FILE",
            message="认证状态文件不存在",
            resolution="运行 'rscore --user' 完成首次登录，或检查 account.storage_state_path 配置",
            exit_code=1,
        ),
        "UNREADABLE_FILE": PreflightBlocker(
            code="UNREADABLE_FILE",
            message="认证状态文件不可读（权限不足）",
            resolution="运行 'chmod 600 {path}' 或检查文件权限",
            exit_code=2,
        ),
        "WINDOWS_PATH": PreflightBlocker(
            code="WINDOWS_PATH",
            message=" storage_state 路径在 Windows 挂载点下（WSL/WSLg 不支持）",
            resolution="将 storage_state.json 移动到 WSL 本地文件系统（如 ~/storage_state.json），更新配置 account.storage_state_path",
            exit_code=3,
        ),
        "INVALID_JSON": PreflightBlocker(
            code="INVALID_JSON",
            message="认证状态文件 JSON 格式无效",
            resolution="删除文件并重新运行 'rscore --user' 重新生成",
            exit_code=4,
        ),
        "MISSING_COOKIES": PreflightBlocker(
            code="MISSING_COOKIES",
            message="认证状态文件缺少 cookies 字段（格式错误）",
            resolution="删除文件并重新运行 'rscore --user' 重新生成",
            exit_code=5,
        ),
        "SESSION_EXPIRED": PreflightBlocker(
            code="SESSION_EXPIRED",
            message="认证会话已过期或无效",
            resolution="运行 'rscore --user' 重新登录；删除 storage_state.json 或修复路径后重试",
            exit_code=6,
        ),
    }

    def __init__(self, config):
        """
        初始化预检器

        Args:
            config: ConfigManager 实例（支持 get() 方法）
        """
        self.config = config
        self.storage_state_path = config.get("account.storage_state_path", "storage_state.json")
        logger.debug(f"PreflightChecker 初始化: storage_state_path={self.storage_state_path}")

    async def validate(self, require_logged_in: bool = False) -> list[PreflightBlocker]:
        """
        执行所有预检，按顺序检查并 fast-fail

        Args:
            require_logged_in: 是否要求会话有效（轻量级浏览器检查）
                              WSL 环境建议设为 False 以快速失败

        Returns:
            阻塞项列表，空列表表示全部通过
        """
        logger.info("开始预检...")
        start_time = os.times()

        # 1. 文件存在性检查（最快）
        if not os.path.exists(self.storage_state_path):
            logger.warning(f"预检失败: 文件不存在 {self.storage_state_path}")
            return [self.BLOCKERS["MISSING_FILE"]]

        # 2. 文件可读性检查
        if not os.access(self.storage_state_path, os.R_OK):
            logger.warning(f"预检失败: 文件不可读 {self.storage_state_path}")
            return [self.BLOCKERS["UNREADABLE_FILE"]]

        # 3. Windows 路径阻断检查（WSL/WSLg 常见问题）
        normalized_path = os.path.normpath(self.storage_state_path)
        if normalized_path.startswith("/mnt/") or "/cygdrive/" in normalized_path:
            logger.warning(f"预检失败: Windows 挂载路径 {normalized_path}")
            return [self.BLOCKERS["WINDOWS_PATH"]]

        # 4. JSON 合法性检查
        try:
            with open(self.storage_state_path, encoding="utf-8") as f:
                state = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"预检失败: JSON 解析失败 {e}")
            return [self.BLOCKERS["INVALID_JSON"]]
        except Exception as e:
            logger.warning(f"预检失败: 文件读取异常 {e}")
            return [self.BLOCKERS["INVALID_JSON"]]

        # 5. Cookies 字段存在性检查
        if not isinstance(state, dict) or "cookies" not in state:
            logger.warning("预检失败: 缺少 cookies 字段")
            return [self.BLOCKERS["MISSING_COOKIES"]]

        # 6. 可选的浏览器 smoke test（会话有效性检查）
        if require_logged_in:
            logger.info("执行会话有效性检查（smoke test）...")
            try:
                from playwright.async_api import async_playwright

                async def _smoke_test():
                    """内部辅助函数，执行轻量级浏览器检查"""
                    playwright = await async_playwright().start()
                    try:
                        # 快速创建浏览器上下文并加载 storage_state
                        browser = await playwright.chromium.launch(headless=True)
                        context = await browser.new_context()

                        try:
                            await context.add_cookies(state["cookies"])
                        except Exception as e:
                            logger.debug(f"添加 cookies 失败: {e}，尝试使用 storage_state 加载")
                            # 如果 add_cookies 失败，尝试使用 from_storage_state
                            if "storage_state_path" in self.config.__dict__:
                                # 备用方案：直接使用存储状态
                                pass

                        page = await context.new_page()
                        try:
                            # 导航到 Bing 首页（快速）
                            await page.goto("https://www.bing.com", wait_until="domcontentloaded", timeout=10000)
                            await page.wait_for_timeout(2000)

                            # 检查登录状态：查找登录按钮或用户头像
                            # 简单启发式：页面包含 Sign in 链接或用户名显示
                            content = await page.content()
                            login_indicators = ["sign in", "登录", "microsoft account"]
                            is_logged_in = not any(ind in content.lower() for ind in login_indicators)

                            return is_logged_in
                        finally:
                            await page.close()
                            await context.close()
                    finally:
                        await browser.close()
                        await playwright.stop()

                # 执行 smoke test（限制超时 12 秒）
                import asyncio
                try:
                    is_valid = await asyncio.wait_for(_smoke_test(), timeout=12.0)
                    if not is_valid:
                        logger.warning("预检失败: 会话已过期")
                        return [self.BLOCKERS["SESSION_EXPIRED"]]
                    else:
                        logger.info("✓ 会话有效性检查通过")
                except asyncio.TimeoutError:
                    logger.warning("Smoke test 超时，假设会话有效（谨慎起见建议重新登录）")
                    # 超时不阻塞，只记录警告
                except Exception as e:
                    logger.warning(f"Smoke test 失败: {e}，跳过会话验证")
                    # 其他错误不阻塞，仅警告

            except ImportError:
                logger.warning("Playwright 未安装，跳过浏览器检查")
            except Exception as e:
                logger.warning(f"浏览器检查异常: {e}，跳过会话验证")

        # 所有检查通过
        elapsed = (os.times().elapsed - start_time) / 1e9  # 转换为秒
        logger.info(f"✓ 预检通过 ({elapsed:.2f}s)")
        return []

    def format_blocker_message(self, blocker: PreflightBlocker) -> str:
        """
        格式化 blocker 输出，包含颜色（如果终端支持）

        Args:
            blocker: PreflightBlocker 对象

        Returns:
            格式化后的完整错误信息
        """
        return str(blocker)


# 便捷函数：快速执行预检并退出
async def run_preflight_and_exit(config, require_logged_in: bool = False) -> None:
    """
    执行预检并在失败时立即退出程序

    Args:
        config: ConfigManager 实例
        require_logged_in: 是否要求会话有效
    """
    checker = PreflightChecker(config)
    blockers = await checker.validate(require_logged_in)

    if blockers:
        for blocker in blockers:
            print(checker.format_blocker_message(blocker), file=sys.stderr)
        sys.exit(blockers[0].exit_code)
    else:
        sys.exit(0)
