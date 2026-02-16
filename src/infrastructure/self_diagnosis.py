"""
自诊断系统 - 让代码自己发现问题

当操作超时或卡住时，自动收集诊断信息：
- 截图
- 页面状态
- 元素状态
- 控制台日志
- 可能原因分析
"""

import asyncio
import logging
import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class SelfDiagnosisSystem:
    """自诊断系统 - 自动检测和诊断超时问题"""

    def __init__(self, page):
        self.page = page
        self.console_logs = []
        self._max_logs = 100  # 限制日志数量，防止内存泄漏

        # 监听控制台日志
        def handle_console(msg):
            self.console_logs.append(f"[{msg.type}] {msg.text}")
            # 限制日志长度，防止内存泄漏
            if len(self.console_logs) > self._max_logs:
                self.console_logs = self.console_logs[-self._max_logs :]

        page.on("console", handle_console)

    async def monitor_execution(
        self, operation: Callable, timeout: int = 30, operation_name: str = ""
    ) -> Any:
        """
        监控执行，超时自动诊断

        Args:
            operation: 要执行的异步操作
            timeout: 超时时间（秒）
            operation_name: 操作名称，用于日志

        Returns:
            操作结果

        Raises:
            TimeoutError: 操作超时，并附带诊断报告路径
        """
        try:
            result = await asyncio.wait_for(operation(), timeout=timeout)
            return result

        except asyncio.TimeoutError:
            # 卡住了！自动诊断
            logger.warning(f"⚠ Operation timeout: {operation_name}")
            diagnosis = await self.diagnose_timeout(operation_name)

            # 保存诊断报告
            report_path = self.save_diagnosis_report(diagnosis)
            logger.error(f"❌ Diagnosis report saved: {report_path}")

            raise TimeoutError(
                f"Operation '{operation_name}' timeout after {timeout}s. "
                f"See diagnosis report: {report_path}"
            ) from None

    async def diagnose_timeout(self, operation_name: str) -> dict[str, Any]:
        """
        诊断超时原因

        Args:
            operation_name: 超时的操作名称

        Returns:
            诊断信息字典
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info("🔍 Collecting diagnosis information...")

        diagnosis = {
            "timestamp": timestamp,
            "operation": operation_name,
            "screenshot": await self.take_screenshot(timestamp),
            "page_url": self.page.url,
            "page_title": await self.page.title(),
            "console_logs": self.get_recent_console_logs(),
            "element_states": await self.check_key_elements(),
            "possible_causes": [],
        }

        # 分析可能原因
        diagnosis["possible_causes"] = self.analyze_causes(diagnosis)

        logger.info("✓ Diagnosis information collected")

        return diagnosis

    async def take_screenshot(self, timestamp: str) -> str:
        """
        自动截图

        Args:
            timestamp: 时间戳

        Returns:
            截图文件路径
        """
        os.makedirs("logs/diagnostics", exist_ok=True)
        path = f"logs/diagnostics/stuck_{timestamp}.png"

        try:
            await self.page.screenshot(path=path, full_page=True)
            logger.info(f"📸 Screenshot saved: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return "screenshot_failed"

    def get_recent_console_logs(self, limit: int = 20) -> str:
        """
        获取最近的控制台日志

        Args:
            limit: 最多返回多少条日志

        Returns:
            日志文本
        """
        recent_logs = self.console_logs[-limit:] if self.console_logs else []
        return "\n".join(recent_logs) if recent_logs else "No console logs"

    async def check_key_elements(self) -> dict[str, dict[str, Any]]:
        """
        检查关键元素状态

        Returns:
            元素状态字典
        """
        # 登录相关元素选择器
        selectors = {
            "email_input": "#i0116",
            "password_input": "#i0118",
            "next_button": "#idSIButton9",
            "signin_button": "#idSIButton9",
            "totp_input": "#idTxtBx_SAOTCC_OTC",
            "stay_signed_in_yes": "#idSIButton9",
            "login_link": "a[id='id_l']",
            "edge_popup_dismiss": 'button:has-text("不，谢谢")',
        }

        states = {}
        for name, selector in selectors.items():
            try:
                element = await self.page.query_selector(selector)
                if element:
                    states[name] = {
                        "exists": True,
                        "visible": await element.is_visible(),
                        "enabled": await element.is_enabled(),
                    }
                else:
                    states[name] = {"exists": False}
            except Exception as e:
                states[name] = {"exists": False, "error": str(e)}

        return states

    def analyze_causes(self, diagnosis: dict[str, Any]) -> list[str]:
        """
        分析可能的原因

        Args:
            diagnosis: 诊断信息

        Returns:
            可能原因列表
        """
        causes = []
        element_states = diagnosis["element_states"]

        # 检查：没有找到任何关键元素
        if all(not state.get("exists") for state in element_states.values()):
            causes.append("❌ No key elements found - wrong page or selectors changed")

        # 检查：元素存在但不可见
        invisible_elements = [
            name
            for name, state in element_states.items()
            if state.get("exists") and not state.get("visible")
        ]
        if invisible_elements:
            causes.append(f"⚠ Elements exist but not visible: {', '.join(invisible_elements)}")

        # 检查：元素存在但禁用
        disabled_elements = [
            name
            for name, state in element_states.items()
            if state.get("exists") and state.get("visible") and not state.get("enabled")
        ]
        if disabled_elements:
            causes.append(f"⚠ Elements disabled: {', '.join(disabled_elements)}")

        # 检查：控制台错误
        console_logs = diagnosis.get("console_logs", "")
        if "error" in console_logs.lower():
            causes.append("⚠ JavaScript errors detected in console")

        # 检查：错误页面
        url = diagnosis.get("page_url", "")
        if "error" in url.lower() or "denied" in url.lower():
            causes.append(f"❌ Error page detected: {url}")

        if not causes:
            causes.append("⚠ No obvious cause detected - manual investigation needed")

        return causes

    def save_diagnosis_report(self, diagnosis: dict[str, Any]) -> str:
        """
        保存诊断报告为 Markdown

        Args:
            diagnosis: 诊断信息

        Returns:
            报告文件路径
        """
        timestamp = diagnosis["timestamp"]
        report_path = f"logs/diagnostics/diagnosis_{timestamp}.md"

        # 构建报告内容
        report = f"""# 登录卡住诊断报告

**时间：** {diagnosis["timestamp"]}
**操作：** {diagnosis["operation"]}
**页面：** {diagnosis["page_url"]}

## 截图
![Screenshot]({diagnosis["screenshot"]})

## 页面状态
- **URL:** {diagnosis["page_url"]}
- **Title:** {diagnosis["page_title"]}

## 元素状态
"""

        # 添加元素状态
        for name, state in diagnosis["element_states"].items():
            if state.get("exists"):
                visible = "✅ 可见" if state.get("visible") else "❌ 不可见"
                enabled = "✅ 启用" if state.get("enabled") else "❌ 禁用"
                report += f"- **{name}:** 存在, {visible}, {enabled}\n"
            else:
                error = state.get("error", "")
                error_msg = f" ({error})" if error else ""
                report += f"- **{name}:** ❌ 不存在{error_msg}\n"

        # 添加控制台日志
        report += f"\n## 控制台日志\n```\n{diagnosis['console_logs']}\n```\n"

        # 添加可能原因
        report += "\n## 可能原因\n"
        for i, cause in enumerate(diagnosis["possible_causes"], 1):
            report += f"{i}. {cause}\n"

        # 添加建议修复
        report += "\n## 建议修复\n"
        report += "1. 检查截图，确认页面状态\n"
        report += "2. 验证元素选择器是否正确\n"
        report += "3. 检查是否有弹窗或遮罩层\n"
        report += "4. 增加等待时间或重试机制\n"
        report += "5. 检查控制台日志中的错误信息\n"

        # 保存报告
        os.makedirs("logs/diagnostics", exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"📄 Diagnosis report saved: {report_path}")

        return report_path
