"""
登录状态检测器模块
提供多重检测方法来确定用户登录状态

与 LoginStateMachine 的区别：
- LoginDetector: 用于检测当前是否已登录（多重检测方法：元素、Cookie、API、内容）
- LoginStateMachine: 用于处理登录流程（状态机驱动）

两者互补使用：
1. LoginDetector 用于快速判断登录状态
2. LoginStateMachine 用于执行登录操作
"""

import json
import logging
import time
from typing import Any

from playwright.async_api import Page

logger = logging.getLogger(__name__)


class LoginStatusCache:
    """登录状态缓存类"""

    def __init__(self, cache_duration: int = 300):
        """
        初始化缓存

        Args:
            cache_duration: 缓存持续时间（秒）
        """
        self.cache_duration = cache_duration
        self.cached_status: bool | None = None
        self.cache_timestamp: float | None = None
        self.cache_reason: str | None = None

    def get_cached_status(self) -> bool | None:
        """获取缓存的登录状态"""
        if (
            self.cached_status is not None
            and self.cache_timestamp is not None
            and time.time() - self.cache_timestamp < self.cache_duration
        ):
            return self.cached_status
        return None

    def set_cached_status(self, status: bool, reason: str = ""):
        """设置缓存状态"""
        self.cached_status = status
        self.cache_timestamp = time.time()
        self.cache_reason = reason

    def clear_cache(self):
        """清除缓存"""
        self.cached_status = None
        self.cache_timestamp = None
        self.cache_reason = None


class LoginDetector:
    """
    登录状态检测器类

    使用多重检测方法判断用户登录状态：
    1. 用户元素检测 - 检查页面上的登录/登出元素
    2. Cookie检测 - 检查认证相关Cookie
    3. API响应检测 - 监听API响应判断登录状态
    4. 页面内容检测 - 分析页面内容关键词

    使用多数投票机制决定最终状态。
    """

    LOGGED_IN_SELECTORS = [
        "button[id*='mectrl']",
        "div[id*='mectrl']",
        "button[aria-label*='Account manager']",
        "div.id_avatar",
        "img[alt*='profile']",
        "button[data-testid='account-menu']",
        "div[data-testid='user-info']",
        "span[data-testid='username']",
        "div.user-name",
        "div#mectrl_main",
        "button#mectrl_headerPicture",
        "div.mectrl_theme",
    ]

    LOGGED_OUT_SELECTORS = [
        "a[href*='login.live.com']",
        "a[href*='login.microsoftonline.com']",
        "button[data-testid='sign-in']",
        "a[href*='microsoft.com/oauth']",
        "header a:has-text('Sign in')",
        "nav a:has-text('Sign in')",
        "header button:has-text('Sign in')",
        "nav button:has-text('Log in')",
    ]

    def __init__(self, config=None):
        """初始化登录检测器"""
        self.config = config
        self.cache = LoginStatusCache()

        self.method_weights = {
            "user_element": 3,
            "cookie": 2,
            "api_response": 2,
            "page_content": 1,
        }

        logger.info("登录状态检测器初始化完成")

    async def detect_login_status(self, page: Page, use_cache: bool = True) -> bool:
        """检测登录状态（主入口方法）"""
        if use_cache:
            cached_status = self.cache.get_cached_status()
            if cached_status is not None:
                logger.debug(f"使用缓存的登录状态: {cached_status} ({self.cache.cache_reason})")
                return cached_status

        logger.info("开始多重登录状态检测...")

        detection_results = {}

        try:
            logger.debug("=" * 50)
            logger.debug("执行用户元素检测...")
            result = await self._detect_by_user_elements(page)
            detection_results["user_element"] = result
            logger.info(f"用户元素检测结果: {result}")
        except Exception as e:
            logger.warning(f"用户元素检测失败: {e}")
            detection_results["user_element"] = None

        try:
            logger.debug("=" * 50)
            logger.debug("执行Cookie检测...")
            result = await self._detect_by_cookies(page)
            detection_results["cookie"] = result
            logger.info(f"Cookie检测结果: {result}")
        except Exception as e:
            logger.warning(f"Cookie检测失败: {e}")
            detection_results["cookie"] = None

        try:
            logger.debug("=" * 50)
            logger.debug("执行API响应检测...")
            result = await self._detect_by_api_response(page)
            detection_results["api_response"] = result
            logger.info(f"API响应检测结果: {result}")
        except Exception as e:
            logger.warning(f"API响应检测失败: {e}")
            detection_results["api_response"] = None

        try:
            logger.debug("=" * 50)
            logger.debug("执行页面内容检测...")
            result = await self._detect_by_page_content(page)
            detection_results["page_content"] = result
            logger.info(f"页面内容检测结果: {result}")
        except Exception as e:
            logger.warning(f"页面内容检测失败: {e}")
            detection_results["page_content"] = None

        logger.debug("=" * 50)

        final_status = self._vote_on_status(detection_results)

        reason = f"多重检测: {detection_results}"
        self.cache.set_cached_status(final_status, reason)

        logger.info("=" * 50)
        logger.info(f"登录状态检测完成: {'已登录' if final_status else '未登录'}")
        logger.info(f"检测结果汇总: {detection_results}")
        logger.info("=" * 50)
        return final_status

    async def _detect_by_user_elements(self, page: Page) -> bool | None:
        """通过用户界面元素检测登录状态"""
        logger.debug(f"[用户元素检测] 当前URL: {page.url}")

        for selector in self.LOGGED_IN_SELECTORS:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    logger.debug(
                        f"[用户元素检测] 选择器 {selector}: 存在={True}, 可见={is_visible}"
                    )
                    if is_visible:
                        logger.info(f"[用户元素检测] ✓ 找到登录元素: {selector}")
                        return True
            except Exception as e:
                logger.debug(f"[用户元素检测] 选择器 {selector} 检查失败: {e}")
                continue

        for selector in self.LOGGED_OUT_SELECTORS:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    logger.debug(
                        f"[用户元素检测] 选择器 {selector}: 存在={True}, 可见={is_visible}"
                    )
                    if is_visible:
                        logger.info(f"[用户元素检测] ✗ 找到登出元素: {selector}")
                        return False
            except Exception as e:
                logger.debug(f"[用户元素检测] 选择器 {selector} 检查失败: {e}")
                continue

        logger.debug("[用户元素检测] 未找到明确的登录/登出元素")
        return None

    async def _detect_by_cookies(self, page: Page) -> bool | None:
        """通过Cookie检测登录状态"""
        try:
            cookies = await page.context.cookies()
            logger.debug(f"[Cookie检测] 总共有 {len(cookies)} 个Cookie")

            auth_cookies = [
                "ESTSAUTH",
                "ESTSAUTHPERSISTENT",
                "SAML11",
                "RPSAuth",
                "MSPOK",
                "MSPRequ",
                "_EDGE_S",
                "_EDGE_V",
            ]

            found_auth_cookies = []
            for cookie in cookies:
                if cookie["name"] in auth_cookies:
                    found_auth_cookies.append(cookie["name"])
                    logger.debug(f"[Cookie检测] ✓ 找到认证Cookie: {cookie['name']}")

            logger.info(
                f"[Cookie检测] 找到 {len(found_auth_cookies)} 个认证Cookie: {found_auth_cookies}"
            )

            if len(found_auth_cookies) >= 2:
                logger.info("[Cookie检测] ✓ 认证Cookie数量充足，判定为已登录")
                return True
            elif len(found_auth_cookies) == 0:
                logger.info("[Cookie检测] ✗ 未找到认证Cookie，判定为未登录")
                return False

            logger.debug("[Cookie检测] 认证Cookie数量不足，无法判定")
            return None

        except Exception as e:
            logger.warning(f"[Cookie检测] 检测出错: {e}")
            return None

    async def _detect_by_api_response(self, page: Page) -> bool | None:
        """通过API响应检测登录状态"""
        try:
            responses = []

            def handle_response(response):
                if any(
                    pattern in response.url for pattern in ["api", "rewards", "account", "profile"]
                ):
                    responses.append(response)

            page.on("response", handle_response)

            try:
                await page.reload(wait_until="networkidle", timeout=10000)
            except Exception:
                pass

            for response in responses:
                try:
                    if response.status == 200:
                        headers = response.headers
                        if "set-cookie" in headers:
                            cookie_header = headers["set-cookie"]
                            if any(
                                auth_name in cookie_header
                                for auth_name in ["MSPOK", "MSPRequ", "auth"]
                            ):
                                return True

                        try:
                            if "application/json" in response.headers.get("content-type", ""):
                                content = await response.text()
                                data = json.loads(content)

                                if any(
                                    field in data
                                    for field in ["user", "account", "profile", "authenticated"]
                                ):
                                    return True
                        except Exception:
                            pass

                    elif response.status == 401:
                        return False

                except Exception as e:
                    logger.debug(f"检查响应失败: {e}")
                    continue

            return None

        except Exception as e:
            logger.debug(f"API响应检测出错: {e}")
            return None
        finally:
            try:
                page.remove_listener("response", handle_response)
            except Exception:
                pass

    async def _detect_by_page_content(self, page: Page) -> bool | None:
        """通过页面内容检测登录状态"""
        try:
            content = await page.content()
            title = await page.title()
            url = page.url

            if any(pattern in url.lower() for pattern in ["login", "signin", "auth"]):
                return False

            logged_in_title_patterns = ["rewards", "dashboard", "account", "profile"]
            logged_out_title_patterns = ["sign in", "login", "authenticate"]

            title_lower = title.lower()
            if any(pattern in title_lower for pattern in logged_in_title_patterns):
                return True
            elif any(pattern in title_lower for pattern in logged_out_title_patterns):
                return False

            content_lower = content.lower()

            logged_in_keywords = [
                "welcome back",
                "your account",
                "sign out",
                "logout",
                "dashboard",
                "profile",
                "settings",
                "your rewards",
            ]

            logged_out_keywords = [
                "sign in to continue",
                "please sign in",
                "login required",
                "create account",
                "forgot password",
            ]

            logged_in_score = sum(1 for keyword in logged_in_keywords if keyword in content_lower)
            logged_out_score = sum(1 for keyword in logged_out_keywords if keyword in content_lower)

            if logged_in_score > logged_out_score and logged_in_score > 0:
                return True
            elif logged_out_score > logged_in_score and logged_out_score > 0:
                return False

            return None

        except Exception as e:
            logger.debug(f"页面内容检测出错: {e}")
            return None

    def _vote_on_status(self, detection_results: dict[str, bool | None]) -> bool:
        """基于多数投票决定登录状态"""
        logged_in_score = 0
        logged_out_score = 0

        for method, result in detection_results.items():
            if result is not None:
                weight = self.method_weights.get(method, 1)
                if result:
                    logged_in_score += weight
                else:
                    logged_out_score += weight

        logger.debug(f"投票结果 - 登录: {logged_in_score}, 登出: {logged_out_score}")
        logger.info(f"[投票] 登录分数={logged_in_score}, 登出分数={logged_out_score}")

        if logged_in_score == logged_out_score:
            cookie_result = detection_results.get("cookie")
            if cookie_result is not None:
                logger.info(f"[投票] 分数平局，使用Cookie检测结果: {cookie_result}")
                return cookie_result
            logger.info("[投票] 分数平局且无Cookie结果，默认为未登录")
            return False

        return logged_in_score > logged_out_score

    def clear_cache(self):
        """清除登录状态缓存"""
        self.cache.clear_cache()
        logger.debug("登录状态缓存已清除")

    async def force_recheck(self, page: Page) -> bool:
        """强制重新检查登录状态（不使用缓存）"""
        self.clear_cache()
        return await self.detect_login_status(page, use_cache=False)

    def get_detection_info(self) -> dict[str, Any]:
        """获取检测信息（用于调试）"""
        return {
            "cache_status": self.cache.cached_status,
            "cache_timestamp": self.cache.cache_timestamp,
            "cache_reason": self.cache.cache_reason,
            "cache_valid": self.cache.get_cached_status() is not None,
        }
