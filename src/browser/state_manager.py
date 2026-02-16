"""
浏览器状态管理器模块
跟踪和管理浏览器的健康状态，处理浏览器生命周期
"""

import asyncio
import logging
import time
from typing import Any

import psutil
from playwright.async_api import Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class BrowserStateManager:
    """浏览器状态管理器类"""

    def __init__(self, config=None):
        """
        初始化浏览器状态管理器

        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.main_page: Page | None = None

        # 状态跟踪
        self.browser_pid: int | None = None
        self.creation_time: float | None = None
        self.last_health_check: float | None = None
        self.health_check_interval = 30  # 30秒检查一次
        self.is_healthy = True
        self.error_count = 0
        self.max_errors = 5

        # 性能监控
        self.memory_usage_history: list[float] = []
        self.cpu_usage_history: list[float] = []
        self.max_history_length = 10

        logger.info("浏览器状态管理器初始化完成")

    def register_browser(self, browser: Browser, context: BrowserContext, main_page: Page):
        """
        注册浏览器实例进行管理

        Args:
            browser: Browser实例
            context: BrowserContext实例
            main_page: 主页面实例
        """
        self.browser = browser
        self.context = context
        self.main_page = main_page
        self.creation_time = time.time()
        self.last_health_check = time.time()
        self.is_healthy = True
        self.error_count = 0

        # 尝试获取浏览器进程ID
        try:
            # 这是一个近似方法，实际PID可能不同
            self.browser_pid = self._find_browser_process()
        except Exception as e:
            logger.debug(f"无法获取浏览器PID: {e}")
            self.browser_pid = None

        logger.info(f"浏览器已注册，PID: {self.browser_pid}")

    def _find_browser_process(self) -> int | None:
        """
        查找浏览器进程ID

        Returns:
            进程ID或None
        """
        try:
            # 查找Chrome/Chromium进程
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    proc_info = proc.info
                    name = proc_info["name"].lower()
                    cmdline = " ".join(proc_info["cmdline"] or []).lower()

                    # 检查是否是浏览器进程
                    if any(
                        browser_name in name for browser_name in ["chrome", "chromium", "msedge"]
                    ):
                        # 检查是否包含playwright相关参数
                        if "remote-debugging-port" in cmdline or "automation" in cmdline:
                            return proc_info["pid"]
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.debug(f"查找浏览器进程失败: {e}")

        return None

    async def check_browser_health(self) -> bool:
        """
        检查浏览器健康状态

        Returns:
            是否健康
        """
        if not self.browser or not self.context or not self.main_page:
            logger.warning("浏览器实例未注册")
            return False

        try:
            current_time = time.time()

            # 检查是否需要进行健康检查
            if (
                self.last_health_check
                and current_time - self.last_health_check < self.health_check_interval
            ):
                return self.is_healthy

            logger.debug("开始浏览器健康检查...")

            # 1. 检查浏览器是否仍然连接
            try:
                contexts = self.browser.contexts
                if not contexts or self.context not in contexts:
                    logger.warning("浏览器上下文已断开")
                    self.is_healthy = False
                    return False
            except Exception as e:
                logger.warning(f"检查浏览器上下文失败: {e}")
                self.is_healthy = False
                return False

            # 2. 检查主页面是否可用
            try:
                if self.main_page.is_closed():
                    logger.warning("主页面已关闭")
                    self.is_healthy = False
                    return False

                # 尝试获取页面标题（轻量级操作）
                await asyncio.wait_for(self.main_page.title(), timeout=5.0)

            except asyncio.TimeoutError:
                logger.warning("页面响应超时")
                self.error_count += 1
            except Exception as e:
                logger.warning(f"检查主页面失败: {e}")
                self.error_count += 1

            # 3. 检查进程状态（如果有PID）
            if self.browser_pid:
                try:
                    proc = psutil.Process(self.browser_pid)
                    if not proc.is_running():
                        logger.warning("浏览器进程已停止")
                        self.is_healthy = False
                        return False

                    # 记录性能数据
                    memory_info = proc.memory_info()
                    cpu_percent = proc.cpu_percent()

                    self.memory_usage_history.append(memory_info.rss / 1024 / 1024)  # MB
                    self.cpu_usage_history.append(cpu_percent)

                    # 保持历史记录长度
                    if len(self.memory_usage_history) > self.max_history_length:
                        self.memory_usage_history.pop(0)
                    if len(self.cpu_usage_history) > self.max_history_length:
                        self.cpu_usage_history.pop(0)

                    # 检查内存使用是否过高（超过1GB）
                    if memory_info.rss > 1024 * 1024 * 1024:
                        logger.warning(f"浏览器内存使用过高: {memory_info.rss / 1024 / 1024:.1f}MB")
                        self.error_count += 1

                except psutil.NoSuchProcess:
                    logger.warning("浏览器进程不存在")
                    self.is_healthy = False
                    return False
                except Exception as e:
                    logger.debug(f"检查进程状态失败: {e}")

            # 4. 检查错误计数
            if self.error_count >= self.max_errors:
                logger.warning(f"错误次数过多: {self.error_count}")
                self.is_healthy = False
                return False

            # 更新检查时间
            self.last_health_check = current_time

            if self.error_count == 0:
                self.is_healthy = True
                logger.debug("✓ 浏览器健康检查通过")
            else:
                logger.debug(f"浏览器健康检查通过，但有 {self.error_count} 个错误")

            return self.is_healthy

        except Exception as e:
            logger.error(f"浏览器健康检查失败: {e}")
            self.is_healthy = False
            return False

    async def cleanup_resources(self):
        """清理浏览器资源"""
        logger.info("开始清理浏览器资源...")

        try:
            # 关闭额外的页面
            if self.context:
                pages = self.context.pages
                logger.debug(f"当前有 {len(pages)} 个页面需要清理")

                for page in pages:
                    if page != self.main_page and not page.is_closed():
                        try:
                            # 禁用 beforeunload 事件，防止"确定要离开？"对话框
                            try:
                                await page.evaluate("""
                                    () => {
                                        window.onbeforeunload = null;
                                        window.addEventListener = function(type, listener, options) {
                                            if (type === 'beforeunload') return;
                                            return EventTarget.prototype.addEventListener.call(this, type, listener, options);
                                        };
                                    }
                                """)
                            except Exception:
                                pass

                            await page.close()
                            logger.debug("关闭额外页面")
                        except Exception as e:
                            logger.debug(f"关闭页面时出错: {e}")

            # 清理上下文
            if self.context and not self.context.pages:
                try:
                    await self.context.close()
                    logger.debug("关闭浏览器上下文")
                except Exception:
                    pass

            # 关闭浏览器
            if self.browser:
                try:
                    await self.browser.close()
                    logger.debug("关闭浏览器")
                except Exception:
                    pass

            # 清理僵尸进程
            await self._cleanup_zombie_processes()

            logger.info("✓ 浏览器资源清理完成")

        except Exception as e:
            logger.error(f"清理浏览器资源失败: {e}")
        finally:
            # 重置状态
            self.browser = None
            self.context = None
            self.main_page = None
            self.browser_pid = None
            self.is_healthy = False

    async def _cleanup_zombie_processes(self):
        """清理僵尸浏览器进程"""
        try:
            zombie_pids = []

            for proc in psutil.process_iter(["pid", "name", "cmdline", "status"]):
                try:
                    proc_info = proc.info
                    name = proc_info["name"].lower()
                    cmdline = " ".join(proc_info["cmdline"] or []).lower()

                    # 查找可能的僵尸浏览器进程
                    if any(
                        browser_name in name for browser_name in ["chrome", "chromium", "msedge"]
                    ):
                        if "remote-debugging-port" in cmdline or "automation" in cmdline:
                            # 检查进程状态
                            if proc_info["status"] == psutil.STATUS_ZOMBIE:
                                zombie_pids.append(proc_info["pid"])
                            elif proc.cpu_percent() == 0 and proc.memory_percent() < 0.1:
                                # 可能是无响应的进程
                                zombie_pids.append(proc_info["pid"])

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # 尝试终止僵尸进程
            for pid in zombie_pids:
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    logger.debug(f"终止僵尸进程: {pid}")

                    # 等待进程终止
                    try:
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        # 强制杀死
                        proc.kill()
                        logger.debug(f"强制杀死进程: {pid}")

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception as e:
                    logger.debug(f"清理进程 {pid} 失败: {e}")

        except Exception as e:
            logger.debug(f"清理僵尸进程失败: {e}")

    def get_performance_stats(self) -> dict[str, Any]:
        """
        获取性能统计信息

        Returns:
            性能统计字典
        """
        stats = {
            "is_healthy": self.is_healthy,
            "error_count": self.error_count,
            "uptime": time.time() - self.creation_time if self.creation_time else 0,
            "browser_pid": self.browser_pid,
        }

        if self.memory_usage_history:
            stats["memory_usage"] = {
                "current": self.memory_usage_history[-1],
                "average": sum(self.memory_usage_history) / len(self.memory_usage_history),
                "max": max(self.memory_usage_history),
            }

        if self.cpu_usage_history:
            stats["cpu_usage"] = {
                "current": self.cpu_usage_history[-1],
                "average": sum(self.cpu_usage_history) / len(self.cpu_usage_history),
                "max": max(self.cpu_usage_history),
            }

        return stats

    async def recover_from_error(self) -> bool:
        """
        从错误中恢复

        Returns:
            是否成功恢复
        """
        logger.info("尝试从浏览器错误中恢复...")

        try:
            # 重置错误计数
            self.error_count = 0

            # 检查主页面是否仍然可用
            if self.main_page and not self.main_page.is_closed():
                try:
                    # 尝试刷新页面
                    await self.main_page.reload(wait_until="domcontentloaded", timeout=10000)
                    logger.info("✓ 页面刷新成功")
                    self.is_healthy = True
                    return True
                except Exception as e:
                    logger.warning(f"页面刷新失败: {e}")

            # 如果页面不可用，尝试创建新页面
            if self.context:
                try:
                    self.main_page = await self.context.new_page()
                    logger.info("✓ 创建新页面成功")
                    self.is_healthy = True
                    return True
                except Exception as e:
                    logger.warning(f"创建新页面失败: {e}")

            logger.warning("浏览器恢复失败")
            return False

        except Exception as e:
            logger.error(f"浏览器恢复过程出错: {e}")
            return False

    def reset_error_count(self):
        """重置错误计数"""
        self.error_count = 0
        logger.debug("错误计数已重置")

    def is_browser_registered(self) -> bool:
        """检查浏览器是否已注册"""
        return self.browser is not None and self.context is not None and self.main_page is not None
