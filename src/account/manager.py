"""
账户管理器模块
管理登录状态和会话持久化
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from playwright.async_api import BrowserContext, Page

from constants import BING_URLS, LOGIN_URLS, REWARDS_URLS
from login.edge_popup_handler import EdgePopupHandler
from login.handlers import (
    AuthBlockedHandler,
    EmailInputHandler,
    GetACodeHandler,
    LoggedInHandler,
    OtpCodeEntryHandler,
    PasswordInputHandler,
    PasswordlessHandler,
    RecoveryEmailHandler,
    StaySignedInHandler,
    Totp2FAHandler,
)
from login.login_detector import LoginDetector
from login.login_state_machine import LoginState, LoginStateMachine

logger = logging.getLogger(__name__)


class AccountManager:
    """账户管理器类"""

    def __init__(self, config):
        """
        初始化账户管理器

        Args:
            config: ConfigManager 实例
        """
        self.config = config
        self.storage_state_path = config.get("account.storage_state_path", "storage_state.json")
        self.login_url = config.get("account.login_url", REWARDS_URLS["rewards_home"])

        # 初始化登录检测器（向后兼容）
        self.login_detector = LoginDetector(config)

        # 初始化登录状态机（新功能）
        self.use_state_machine = config.get("login.state_machine_enabled", True)
        if self.use_state_machine:
            self.state_machine = LoginStateMachine(config, logger)
            self._register_state_handlers()
            logger.info("登录状态机已启用")
        else:
            self.state_machine = None
            logger.info("登录状态机已禁用，使用传统登录方式")

        # 初始化 Edge 弹窗处理器
        self.edge_popup_handler = EdgePopupHandler(logger=logger)

        logger.info(f"账户管理器初始化完成: {self.storage_state_path}")

    def _register_state_handlers(self):
        """注册所有状态处理器"""
        if not self.state_machine:
            return

        # 注册处理器
        self.state_machine.register_handler(
            LoginState.EMAIL_INPUT, EmailInputHandler(self.config, logger)
        )
        self.state_machine.register_handler(
            LoginState.PASSWORD_INPUT, PasswordInputHandler(self.config, logger)
        )
        self.state_machine.register_handler(
            LoginState.TOTP_2FA, Totp2FAHandler(self.config, logger)
        )
        self.state_machine.register_handler(
            LoginState.PASSWORDLESS, PasswordlessHandler(self.config, logger)
        )
        self.state_machine.register_handler(
            LoginState.GET_A_CODE, GetACodeHandler(self.config, logger)
        )
        self.state_machine.register_handler(
            LoginState.RECOVERY_EMAIL, RecoveryEmailHandler(self.config, logger)
        )
        self.state_machine.register_handler(
            LoginState.LOGGED_IN, LoggedInHandler(self.config, logger)
        )
        self.state_machine.register_handler(
            LoginState.AUTH_BLOCKED, AuthBlockedHandler(self.config, logger)
        )
        self.state_machine.register_handler(
            LoginState.OTP_CODE_ENTRY, OtpCodeEntryHandler(self.config, logger)
        )
        self.state_machine.register_handler(
            LoginState.STAY_SIGNED_IN, StaySignedInHandler(self.config, logger)
        )

        logger.debug(f"已注册 {len(self.state_machine.handlers)} 个状态处理器")

    async def load_session(self) -> dict | None:
        """
        加载保存的会话状态

        Returns:
            会话状态字典，失败返回 None
        """
        if not os.path.exists(self.storage_state_path):
            logger.info(f"会话文件不存在: {self.storage_state_path}")
            return None

        try:
            with open(self.storage_state_path, encoding="utf-8") as f:
                state = json.load(f)

            # 验证会话状态格式
            if not isinstance(state, dict):
                logger.error("会话状态格式无效")
                return None

            if "cookies" not in state:
                logger.error("会话状态缺少 cookies")
                return None

            cookie_count = len(state.get("cookies", []))
            logger.info(f"✓ 加载会话状态成功: {cookie_count} 个 cookies")

            return state

        except json.JSONDecodeError as e:
            logger.error(f"会话文件 JSON 解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"加载会话状态失败: {e}")
            return None

    async def save_session(self, context: BrowserContext) -> bool:
        """
        保存会话状态到磁盘

        Args:
            context: BrowserContext 实例

        Returns:
            是否成功
        """
        try:
            logger.debug("开始保存会话状态...")

            # 步骤0: 设置全局dialog处理器（在最开始就设置）
            async def handle_dialog(dialog):
                try:
                    logger.debug(f"检测到对话框: {dialog.type} - {dialog.message}")
                    await dialog.accept()
                    logger.debug("✓ 对话框已自动接受")
                except Exception as e:
                    logger.debug(f"处理对话框时出错: {e}")

            # 为context设置dialog监听器
            context.on("page", lambda page: page.on("dialog", handle_dialog))

            # 步骤1: 获取所有页面
            all_pages = context.pages
            logger.debug(f"当前上下文中有 {len(all_pages)} 个页面")

            # 为现有页面设置dialog监听器
            for page in all_pages:
                try:
                    if not page.is_closed():
                        page.on("dialog", handle_dialog)
                except Exception:
                    pass

            # 步骤2: 在所有页面上禁用 beforeunload（包括新打开的页面）
            async def disable_beforeunload(page):
                try:
                    if not page.is_closed():
                        await page.evaluate("""
                            () => {
                                // 移除所有 beforeunload 监听器
                                window.onbeforeunload = null;
                                window.onunload = null;

                                // 阻止新的 beforeunload 监听器
                                const originalAddEventListener = window.addEventListener;
                                window.addEventListener = function(type, listener, options) {
                                    if (type === 'beforeunload' || type === 'unload') {
                                        return;
                                    }
                                    return originalAddEventListener.call(this, type, listener, options);
                                };

                                // 覆盖 confirm 和 alert，防止弹窗
                                window.confirm = () => true;
                                window.alert = () => {};
                            }
                        """)
                        logger.debug(f"✓ 已禁用页面的 beforeunload: {page.url[:50]}")
                except Exception as e:
                    logger.debug(f"禁用 beforeunload 失败: {e}")

            # 并发禁用所有页面的 beforeunload
            await asyncio.gather(
                *[disable_beforeunload(page) for page in all_pages], return_exceptions=True
            )

            # 步骤3: 移除所有事件监听器
            try:
                context.remove_all_listeners("page")
                logger.debug("已移除所有页面创建监听器")
            except Exception as e:
                logger.debug(f"移除监听器时出错: {e}")

            # 步骤4: 等待一小段时间
            await asyncio.sleep(0.3)

            # 步骤5: 关闭所有额外的页面（保留第一个）
            if len(all_pages) > 1:
                logger.debug(f"关闭 {len(all_pages) - 1} 个额外页面...")

                async def close_page_safely(page):
                    try:
                        if not page.is_closed():
                            # 再次确保 beforeunload 被禁用
                            try:
                                await page.evaluate("() => { window.onbeforeunload = null; }")
                            except Exception:
                                pass

                            # 直接关闭（dialog已经在前面设置好了）
                            await page.close()
                            logger.debug("✓ 已关闭额外页面")
                    except Exception as e:
                        logger.debug(f"关闭页面时出错: {e}")

                # 并发关闭所有额外页面
                await asyncio.gather(
                    *[close_page_safely(page) for page in all_pages[1:]], return_exceptions=True
                )

                # 等待关闭完成
                await asyncio.sleep(0.5)

            # 步骤6: 验证只剩下一个页面
            remaining_pages = context.pages
            logger.debug(f"清理后剩余 {len(remaining_pages)} 个页面")

            # 步骤7: 获取会话状态
            logger.debug("开始获取会话状态...")
            state = await context.storage_state()
            logger.debug("✓ 会话状态获取成功")

            # 确保目录存在
            Path(self.storage_state_path).parent.mkdir(parents=True, exist_ok=True)

            # 保存到文件
            with open(self.storage_state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            cookie_count = len(state.get("cookies", []))
            file_size = os.path.getsize(self.storage_state_path)

            logger.info(f"✓ 会话状态已保存: {self.storage_state_path}")
            logger.info(f"  Cookies: {cookie_count}, 文件大小: {file_size} bytes")

            return True

        except Exception as e:
            logger.error(f"保存会话状态失败: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return False

    async def is_logged_in(self, page: Page, navigate: bool = True) -> bool:
        """
        检查是否已登录（使用增强的多重检测）

        Args:
            page: Playwright Page 对象
            navigate: 是否导航到登录页面（默认True，手动登录时应设为False）

        Returns:
            是否已登录
        """
        try:
            logger.info("检查登录状态...")

            # 只在需要时导航到登录页面
            if navigate:
                try:
                    await page.goto(self.login_url, wait_until="domcontentloaded", timeout=30000)
                    # 等待页面加载
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    logger.warning(f"页面导航失败: {e}")
                    # 导航失败，无法检测，返回False（未登录）
                    return False

            # 使用LoginDetector进行多重检测
            is_logged_in = await self.login_detector.detect_login_status(page)

            if is_logged_in:
                logger.info("✓ 用户已登录")
            else:
                logger.info("✗ 用户未登录")

            return is_logged_in

        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            # 如果检查失败，返回False（未登录），更安全
            return False

    async def wait_for_manual_login(self, page: Page, timeout: int = 300) -> bool:
        """
        等待用户手动登录（支持2FA和Stay signed in提示）

        Args:
            page: Playwright Page 对象
            timeout: 超时时间（秒）

        Returns:
            是否登录成功
        """
        logger.info("=" * 60)
        logger.info("请在浏览器中手动登录")
        logger.info("=" * 60)
        logger.info(f"超时时间: {timeout} 秒")
        logger.info("提示: 如果有2FA验证，请完成所有验证步骤")
        logger.info("提示: 程序会自动处理'保持登录'提示")
        logger.info("")

        # 直接导航到 Microsoft 登录页面（使用通用登录页，而不是 rewards 页面）
        # rewards 页面需要登录后才能访问，会返回 HTTP 错误
        manual_login_url = LOGIN_URLS["microsoft_login"]

        try:
            logger.info(f"导航到登录页面: {manual_login_url}")
            await page.goto(manual_login_url, wait_until="domcontentloaded", timeout=30000)
            logger.info("✓ 成功导航到登录页面")
            logger.info("请在浏览器中完成登录操作")
        except Exception as e:
            logger.error(f"导航到登录页面失败: {e}")
            logger.info("请检查网络连接或稍后重试")
            return False

        # 等待用户有时间看到页面
        await asyncio.sleep(2)

        # 等待登录完成
        start_time = asyncio.get_running_loop().time()
        check_interval = 5  # 检查间隔5秒
        last_log_time = 0  # 上次输出日志的时间

        # 2FA相关的选择器
        twofa_selectors = [
            'input[name="otc"]',  # TOTP输入框
            'input[type="tel"]',  # 电话验证码
            'input[aria-label*="code"]',  # 验证码输入
            'div[data-value="PhoneAppOTP"]',  # 身份验证器应用
            'div[data-value="PhoneAppNotification"]',  # 推送通知
        ]

        # "Stay signed in?" 提示的选择器
        stay_signed_in_selectors = [
            'input[id="idSIButton9"]',  # Yes按钮
            'button:has-text("Yes")',
            'input[value="Yes"]',
        ]

        # 登录流程相关的URL关键词
        login_keywords = ["login", "oauth", "authenticate", "signin", "auth"]

        logger.info("⏳ 等待您完成登录...")

        # Edge浏览器弹窗选择器（"不，谢谢"按钮）
        edge_popup_selectors = [
            'button:has-text("不，谢谢")',
            'button:has-text("No, thanks")',
            'button[id*="dismiss"]',
            'button[class*="dismiss"]',
        ]

        while True:
            # 检查超时
            elapsed = asyncio.get_running_loop().time() - start_time
            if elapsed > timeout:
                logger.error(f"等待登录超时（{timeout}秒）")
                return False

            # 每30秒输出一次提示
            if elapsed - last_log_time >= 30:
                logger.info(f"⏳ 仍在等待登录... (已等待 {int(elapsed)} 秒)")
                last_log_time = elapsed

            # 首先尝试关闭 Edge 浏览器弹窗（如果有）
            try:
                for selector in edge_popup_selectors:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        logger.info("检测到 Edge 浏览器弹窗，自动关闭...")
                        await element.click()
                        await asyncio.sleep(1)
                        logger.info("✓ 已关闭弹窗")
                        break
            except Exception as e:
                logger.debug(f"检查 Edge 弹窗时出错: {e}")

            # 获取当前URL
            try:
                current_url = page.url.lower()
            except Exception as e:
                logger.debug(f"获取URL失败: {e}")
                await asyncio.sleep(check_interval)
                continue

            # 如果还在空白页，继续等待
            if current_url == "about:blank" or current_url == "":
                await asyncio.sleep(check_interval)
                continue

            # 检查是否有"Stay signed in?"提示
            # 只在确认是"保持登录"页面时才点击，避免误判
            stay_signed_in_config = self.config.get("login.stay_signed_in", True)
            if stay_signed_in_config:
                try:
                    # 先检查页面是否包含"Stay signed in"文本
                    page_content = await page.content()
                    is_stay_signed_in_page = (
                        "stay signed in" in page_content.lower() or "kmsi" in current_url.lower()
                    )

                    if is_stay_signed_in_page:
                        for selector in stay_signed_in_selectors:
                            try:
                                element = await page.query_selector(selector)
                                if element and await element.is_visible():
                                    logger.info("检测到'保持登录'提示，自动点击'是'...")
                                    await element.click()
                                    await asyncio.sleep(2)  # 等待页面跳转
                                    logger.info("✓ 已点击'保持登录'")
                                    break
                            except Exception as e:
                                logger.debug(f"检查Stay signed in按钮时出错: {e}")
                except Exception as e:
                    logger.debug(f"检查Stay signed in页面时出错: {e}")

            # 检查是否在2FA页面
            is_on_2fa_page = False
            for selector in twofa_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        is_on_2fa_page = True
                        logger.debug("检测到2FA验证页面，等待用户完成验证...")
                        break
                except Exception:
                    pass

            if is_on_2fa_page:
                await asyncio.sleep(check_interval)
                continue

            # 检查是否仍在登录流程中
            # 排除 OAuth 回调页面（这些页面虽然包含 auth，但实际是登录完成的标志）
            is_oauth_callback = (
                "complete-client-signin" in current_url
                or "oauth-silent" in current_url
                or "ppsecure/post.srf" in current_url  # Windows Hello 登录完成后的回调页面
            )
            is_in_login_flow = (
                any(keyword in current_url for keyword in login_keywords) and not is_oauth_callback
            )

            if is_in_login_flow:
                logger.debug(f"仍在登录流程中... ({int(elapsed)}秒)")
                await asyncio.sleep(check_interval)
                continue

            # 如果在 OAuth 回调页面，说明登录已完成，尝试导航到目标页面
            if is_oauth_callback:
                logger.info("检测到 OAuth 回调页面，登录可能已完成")
                logger.info("尝试导航到 Bing 首页验证登录状态...")
                try:
                    await page.goto(BING_URLS["home"], wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(2)
                    current_url = page.url.lower()
                    logger.info(f"已导航到: {current_url}")
                except Exception as e:
                    logger.warning(f"导航失败: {e}")

            # 已经跳转出登录流程，尝试检测登录状态
            # 不限制必须在特定页面，因为通行凭证/扫码登录后可能停留在任意页面
            if not is_in_login_flow:
                logger.debug("已离开登录流程，尝试导航到 Bing 检查登录状态...")

                # 导航到 Bing 以便检测登录状态
                try:
                    await page.goto(BING_URLS["home"], wait_until="domcontentloaded", timeout=15000)
                    logger.debug(f"已导航到 Bing: {page.url}")

                    # 等待页面完全加载
                    await asyncio.sleep(2)

                    # 刷新页面确保登录状态生效
                    logger.debug("刷新页面以确保登录状态生效...")
                    await page.reload(wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(3)  # 等待刷新后页面稳定

                    logger.debug(f"页面刷新完成: {page.url}")
                except Exception as e:
                    logger.debug(f"导航/刷新 Bing 失败: {e}")

                # 直接使用login_detector检测，不要调用is_logged_in（避免页面跳转）
                try:
                    logger.info("开始检测登录状态（详细模式）...")
                    is_logged_in = await self.login_detector.detect_login_status(
                        page, use_cache=False
                    )

                    # 获取检测详情
                    detection_info = self.login_detector.get_detection_info()
                    logger.info(f"检测详情: {detection_info}")

                    if is_logged_in:
                        logger.info("✓ 登录成功！")
                        return True
                    else:
                        logger.warning("登录状态检测失败，继续等待...")
                        logger.warning(f"当前URL: {page.url}")
                except Exception as e:
                    logger.error(f"检测登录状态时出错: {e}")
                    import traceback

                    logger.debug(traceback.format_exc())

            # 等待一段时间再检查
            await asyncio.sleep(check_interval)

    async def auto_login(self, page: Page, credentials: dict[str, str]) -> bool:
        """
        使用登录状态机自动登录

        Args:
            page: Playwright Page 对象
            credentials: 登录凭据字典，包含:
                - email: 邮箱地址
                - password: 密码
                - totp_secret: TOTP密钥（可选）

        Returns:
            是否登录成功
        """
        if not self.use_state_machine or not self.state_machine:
            logger.warning("登录状态机未启用，无法自动登录")
            return False

        try:
            logger.info("开始自动登录流程...")

            # 不要直接导航到 rewards.microsoft.com（会返回 HTTP 400）
            # 也不要点击 Bing 登录按钮（会触发 Edge 弹窗）
            # 直接导航到 Microsoft 登录页面
            logger.info("直接导航到 Microsoft 登录页面...")
            await page.goto(
                LOGIN_URLS["microsoft_login"], wait_until="domcontentloaded", timeout=30000
            )

            # 等待页面完全加载
            await page.wait_for_load_state("networkidle", timeout=10000)
            await page.wait_for_timeout(2000)

            await page.wait_for_timeout(1000)

            # 使用状态机处理登录
            success = await self.state_machine.handle_login(page, credentials)

            if success:
                logger.info("✓ 自动登录成功！")
                # 获取诊断信息
                diag = self.state_machine.get_diagnostic_info()
                logger.info(f"  状态转换次数: {diag['transition_count']}")
                logger.info(f"  最终状态: {diag['current_state']}")
            else:
                logger.error("✗ 自动登录失败")
                # 记录诊断信息
                diag = self.state_machine.get_diagnostic_info()
                logger.error(f"  失败状态: {diag['current_state']}")
                logger.error(f"  状态历史: {len(diag['state_history'])} 次转换")

            return success

        except TimeoutError as e:
            logger.error(f"登录超时: {e}")
            return False
        except RuntimeError as e:
            logger.error(f"登录失败（超过最大转换次数）: {e}")
            return False
        except Exception as e:
            logger.error(f"自动登录异常: {e}", exc_info=True)
            return False

    def get_storage_state_path(self) -> str:
        """
        获取会话状态文件路径

        Returns:
            文件路径
        """
        return self.storage_state_path

    def session_exists(self) -> bool:
        """
        检查会话文件是否存在

        Returns:
            是否存在
        """
        exists = os.path.exists(self.storage_state_path)

        if exists:
            file_size = os.path.getsize(self.storage_state_path)
            logger.debug(f"会话文件存在: {self.storage_state_path} ({file_size} bytes)")
        else:
            logger.debug(f"会话文件不存在: {self.storage_state_path}")

        return exists

    async def refresh_session(self, page: Page, context: BrowserContext) -> bool:
        """
        刷新会话（重新登录并保存）

        Args:
            page: Playwright Page 对象
            context: BrowserContext 实例

        Returns:
            是否成功
        """
        logger.info("开始刷新会话...")

        # 等待手动登录
        if await self.wait_for_manual_login(page):
            # 保存新的会话状态
            return await self.save_session(context)

        return False
