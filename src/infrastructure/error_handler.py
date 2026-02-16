"""
错误处理器模块
统一错误处理、分类、重试和恢复
"""

import asyncio
import logging
import traceback
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""

    CONFIGURATION = "configuration"  # 配置错误
    AUTHENTICATION = "authentication"  # 认证错误
    NETWORK = "network"  # 网络错误
    PAGE_INTERACTION = "page_interaction"  # 页面交互错误
    BUSINESS_LOGIC = "business_logic"  # 业务逻辑错误
    UNKNOWN = "unknown"  # 未知错误


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"  # 低 - 可以忽略
    MEDIUM = "medium"  # 中 - 需要记录
    HIGH = "high"  # 高 - 需要重试
    CRITICAL = "critical"  # 严重 - 需要停止


class ErrorHandler:
    """错误处理器类"""

    def __init__(self, config):
        """
        初始化错误处理器

        Args:
            config: ConfigManager 实例
        """
        self.config = config
        self.max_retries = config.get("error_handling.max_retries", 3)
        self.retry_delay = config.get("error_handling.retry_delay", 5)
        self.use_exponential_backoff = config.get("error_handling.exponential_backoff", True)
        self._max_history = 100

        self.error_count = 0
        self.error_history = []

        logger.info(f"错误处理器初始化完成 (max_retries={self.max_retries})")

    def classify_error(self, error: Exception) -> tuple[ErrorType, ErrorSeverity]:
        """
        分类错误

        Args:
            error: 异常对象

        Returns:
            (错误类型, 严重程度)
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__

        # 配置错误
        if "config" in error_str or "yaml" in error_str:
            return ErrorType.CONFIGURATION, ErrorSeverity.CRITICAL

        # 认证错误
        if any(keyword in error_str for keyword in ["login", "auth", "session", "cookie"]):
            return ErrorType.AUTHENTICATION, ErrorSeverity.HIGH

        # 网络错误
        if any(keyword in error_str for keyword in ["timeout", "network", "connection", "dns"]):
            return ErrorType.NETWORK, ErrorSeverity.HIGH

        # 页面交互错误
        if any(
            keyword in error_str for keyword in ["selector", "element", "click", "type", "navigate"]
        ):
            return ErrorType.PAGE_INTERACTION, ErrorSeverity.MEDIUM

        # Playwright 特定错误
        if "playwright" in error_type_name.lower():
            if "timeout" in error_str:
                return ErrorType.NETWORK, ErrorSeverity.HIGH
            elif "target" in error_str and "closed" in error_str:
                return ErrorType.PAGE_INTERACTION, ErrorSeverity.HIGH
            else:
                return ErrorType.PAGE_INTERACTION, ErrorSeverity.MEDIUM

        # 业务逻辑错误
        if any(keyword in error_str for keyword in ["points", "search", "task"]):
            return ErrorType.BUSINESS_LOGIC, ErrorSeverity.MEDIUM

        # 未知错误
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM

    async def handle_error(
        self,
        error: Exception,
        context: str = "",
        retry_func: Callable | None = None,
        *args,
        **kwargs,
    ) -> tuple[bool, Any]:
        """
        统一错误处理

        Args:
            error: 异常对象
            context: 错误上下文描述
            retry_func: 重试函数（可选）
            *args, **kwargs: 重试函数的参数

        Returns:
            (是否成功, 结果)
        """
        self.error_count += 1
        error_type, severity = self.classify_error(error)

        # 记录错误
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "type": error_type.value,
            "severity": severity.value,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }

        self.error_history.append(error_record)

        if len(self.error_history) > self._max_history:
            self.error_history = self.error_history[-self._max_history :]

        # 记录日志
        log_message = f"错误 [{error_type.value}] [{severity.value}] {context}: {error}"

        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
            logger.critical("严重错误，无法继续执行")
            return False, None
        elif severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # 如果提供了重试函数且严重程度允许重试
        if retry_func and severity in [ErrorSeverity.HIGH, ErrorSeverity.MEDIUM]:
            return await self.retry_with_backoff(retry_func, context, *args, **kwargs)

        return False, None

    async def retry_with_backoff(
        self, func: Callable, context: str, *args, **kwargs
    ) -> tuple[bool, Any]:
        """
        使用指数退避重试

        Args:
            func: 要重试的函数
            context: 上下文描述
            *args, **kwargs: 函数参数

        Returns:
            (是否成功, 结果)
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"重试 {context} (尝试 {attempt + 1}/{self.max_retries})...")

                # 计算延迟时间
                if self.use_exponential_backoff:
                    delay = self.retry_delay * (2**attempt)  # 指数退避
                else:
                    delay = self.retry_delay

                # 等待
                if attempt > 0:
                    logger.info(f"等待 {delay} 秒后重试...")
                    await asyncio.sleep(delay)

                # 执行函数
                result = await func(*args, **kwargs)

                logger.info(f"✓ 重试成功: {context}")
                return True, result

            except Exception as e:
                logger.warning(f"重试 {attempt + 1} 失败: {e}")

                if attempt == self.max_retries - 1:
                    logger.error(f"❌ 重试次数已用尽: {context}")
                    return False, None

        return False, None

    def check_for_captcha(self, page_content: str) -> bool:
        """
        检查页面是否包含验证码

        Args:
            page_content: 页面内容

        Returns:
            是否包含验证码
        """
        captcha_keywords = [
            "captcha",
            "recaptcha",
            "verify you're human",
            "security check",
            "unusual activity",
            "robot",
            "verification",
        ]

        content_lower = page_content.lower()

        for keyword in captcha_keywords:
            if keyword in content_lower:
                logger.warning(f"⚠️  检测到可能的验证码: {keyword}")
                return True

        return False

    def check_for_account_lock(self, page_content: str) -> bool:
        """
        检查账号是否被锁定

        Args:
            page_content: 页面内容

        Returns:
            是否被锁定
        """
        lock_keywords = [
            "account locked",
            "account suspended",
            "account disabled",
            "temporarily unavailable",
            "access denied",
            "账号已锁定",
            "账号已暂停",
        ]

        content_lower = page_content.lower()

        for keyword in lock_keywords:
            if keyword in content_lower:
                logger.error(f"❌ 检测到账号锁定: {keyword}")
                return True

        return False

    async def handle_page_error(self, page, error: Exception, context: str) -> bool:
        """
        处理页面相关错误

        Args:
            page: Playwright Page 对象
            error: 异常对象
            context: 错误上下文

        Returns:
            是否成功恢复
        """
        try:
            logger.info(f"尝试恢复页面错误: {context}")

            # 获取页面内容
            try:
                content = await page.content()

                # 检查验证码
                if self.check_for_captcha(content):
                    logger.error("检测到验证码，需要人工处理")
                    return False

                # 检查账号锁定
                if self.check_for_account_lock(content):
                    logger.error("检测到账号锁定，停止执行")
                    return False

            except Exception:
                logger.warning("无法获取页面内容")

            # 尝试刷新页面
            logger.info("尝试刷新页面...")
            await page.reload(wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            logger.info("✓ 页面刷新成功")
            return True

        except Exception as e:
            logger.error(f"页面恢复失败: {e}")
            return False

    def get_error_summary(self) -> dict:
        """
        获取错误摘要

        Returns:
            错误统计字典
        """
        summary = {
            "total_errors": self.error_count,
            "error_history": self.error_history[-10:],  # 最近10个错误
            "error_types": {},
            "error_severities": {},
        }

        # 统计错误类型和严重程度
        for error in self.error_history:
            error_type = error["type"]
            severity = error["severity"]

            summary["error_types"][error_type] = summary["error_types"].get(error_type, 0) + 1
            summary["error_severities"][severity] = summary["error_severities"].get(severity, 0) + 1

        return summary

    def should_stop_execution(self) -> bool:
        """
        判断是否应该停止执行

        Returns:
            是否应该停止
        """
        # 如果有严重错误，停止执行
        for error in self.error_history:
            if error["severity"] == ErrorSeverity.CRITICAL.value:
                return True

        # 如果短时间内错误过多，停止执行
        recent_errors = list(self.error_history[-10:])
        if len(recent_errors) >= 5:
            logger.warning("短时间内错误过多，建议停止执行")
            return True

        return False
