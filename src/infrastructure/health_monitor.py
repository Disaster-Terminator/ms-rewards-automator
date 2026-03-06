"""
健康监控模块
提供系统健康检查、性能监控和问题诊断功能
"""

import asyncio
import json
import logging
import platform
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import psutil

from constants import HEALTH_CHECK_URLS

logger = logging.getLogger(__name__)

# 配置常量
MAX_HISTORY_POINTS = 20  # 保留最近N个数据点（从100减少到20）
CHECK_INTERVAL_DEFAULT = 30


class HealthMonitor:
    """健康监控器类 - 简化版"""

    def __init__(self, config=None):
        """
        初始化健康监控器

        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.enabled = config.get("monitoring.health_check.enabled", True) if config else True
        self.check_interval = (
            config.get("monitoring.health_check.interval", CHECK_INTERVAL_DEFAULT)
            if config
            else CHECK_INTERVAL_DEFAULT
        )

        # 性能指标（使用 deque 限制历史数据量）
        self.metrics = {
            "start_time": time.time(),
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "average_response_time": 0.0,
            "cpu_usage": deque(maxlen=MAX_HISTORY_POINTS),
            "memory_usage": deque(maxlen=MAX_HISTORY_POINTS),
            "browser_crashes": 0,
            "network_errors": 0,
            "browser_memory_mb": 0,
            "browser_page_count": 0,
        }

        self._browser_context = None
        self._browser_instance = None

        # 健康状态
        self.health_status = {
            "overall": "healthy",
            "browser": "unknown",
            "network": "unknown",
            "system": "unknown",
            "last_check": None,
        }

        # 问题与建议
        self.issues = []
        self.recommendations = []

        # 监控任务
        self._monitoring_task = None

        logger.info(f"健康监控器初始化完成 (enabled={self.enabled})")

    def register_browser(self, browser_instance=None, browser_context=None):
        """
        注册浏览器实例用于健康监控

        Args:
            browser_instance: Playwright Browser 实例
            browser_context: BrowserContext 实例
        """
        self._browser_instance = browser_instance
        self._browser_context = browser_context
        logger.debug("已注册浏览器实例到健康监控器")

    async def start_monitoring(self):
        """启动健康监控后台任务"""
        if not self.enabled:
            logger.debug("健康监控已禁用")
            return

        logger.info("启动健康监控...")
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """停止健康监控"""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.info("停止健康监控...")
            self._monitoring_task.cancel()
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                logger.debug("健康监控任务已取消")
            finally:
                self._monitoring_task = None

    async def _monitoring_loop(self):
        """监控循环（简化为固定间隔执行）"""
        try:
            while True:
                try:
                    await self.perform_health_check()
                    await asyncio.sleep(self.check_interval)
                except asyncio.CancelledError:
                    logger.debug("监控循环被取消")
                    raise
                except Exception as e:
                    logger.error(f"健康监控循环错误: {e}")
                    await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.debug("监控循环已停止")
            raise
        finally:
            logger.debug("监控循环资源已清理")

    async def perform_health_check(self) -> dict[str, Any]:
        """
        执行健康检查（简化版，移除复杂的交叉分析）

        Returns:
            健康检查结果字典
        """
        logger.debug("执行健康检查...")

        # 1. 系统资源检查
        system_health = await self._check_system_health()

        # 2. 网络连接检查
        network_health = await self._check_network_health()

        # 3. 浏览器健康检查
        browser_health = await self._check_browser_health()

        # 更新健康状态
        self.health_status.update(
            {
                "system": system_health["status"],
                "network": network_health["status"],
                "browser": browser_health["status"],
                "last_check": datetime.now().isoformat(),
            }
        )

        # 计算总体健康状态（简化：三个子状态中最差的）
        self._calculate_overall_health()

        # 计算成功率
        total = self.metrics["total_searches"]
        self.metrics["success_rate"] = (
            self.metrics["successful_searches"] / total if total > 0 else 0.0
        )

        # 生成建议（简化）
        self._generate_recommendations_simple()

        return {
            "status": self.health_status.copy(),
            "metrics": self._get_metrics_snapshot(),
            "issues": self.issues.copy(),
            "recommendations": self.recommendations.copy(),
        }

    async def _check_system_health(self) -> dict[str, Any]:
        """检查系统健康状态（简化版）"""
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 存储历史数据（deque 自动限制大小）
            self.metrics["cpu_usage"].append(cpu)
            self.metrics["memory_usage"].append(memory_percent)

            # 磁盘检查（跨平台）
            system_disk = "C:\\" if platform.system() == "Windows" else "/"
            try:
                disk = psutil.disk_usage(system_disk)
                disk_percent = (disk.used / disk.total) * 100
            except Exception:
                disk_percent = 0

            # 判断状态
            status = "healthy"
            issues = []

            if cpu > 90:
                status = "warning"
                issues.append(f"CPU使用率过高: {cpu:.1f}%")
            if memory_percent > 85:
                status = "warning"
                issues.append(f"内存使用率过高: {memory_percent:.1f}%")
            if disk_percent > 90:
                status = "warning"
                issues.append(f"磁盘空间不足: {disk_percent:.1f}%")

            return {
                "status": status,
                "cpu_percent": cpu,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "issues": issues,
            }

        except Exception as e:
            logger.error(f"系统健康检查失败: {e}")
            return {"status": "error", "error": str(e), "issues": ["系统健康检查失败"]}

    async def _check_network_health(self) -> dict[str, Any]:
        """检查网络健康状态（简化版）"""
        try:
            import aiohttp

            test_urls = [
                HEALTH_CHECK_URLS["bing"],
                HEALTH_CHECK_URLS["rewards"],
                HEALTH_CHECK_URLS["google"],
            ]

            successful = 0
            response_times = []

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                for url in test_urls:
                    try:
                        start = time.time()
                        async with session.get(url) as resp:
                            response_times.append(time.time() - start)
                            if resp.status == 200:
                                successful += 1
                    except Exception:
                        pass  # 单个URL失败不影响整体

            avg_time = sum(response_times) / len(response_times) if response_times else 0
            connection_rate = successful / len(test_urls)

            # 判断状态
            if connection_rate >= 0.8 and avg_time < 5.0:
                status = "healthy"
            elif connection_rate >= 0.5:
                status = "warning"
            else:
                status = "error"

            issues = []
            if connection_rate < 0.8:
                issues.append(f"网络连接不稳定: {connection_rate * 100:.0f}% 成功率")
            if avg_time > 5.0:
                issues.append(f"网络响应缓慢: {avg_time:.1f}s")

            return {
                "status": status,
                "connection_rate": connection_rate,
                "avg_response_time": avg_time,
                "successful_connections": successful,
                "total_tests": len(test_urls),
                "issues": issues,
            }

        except Exception as e:
            logger.error(f"网络健康检查失败: {e}")
            return {"status": "error", "error": str(e), "issues": ["网络健康检查失败"]}

    async def _check_browser_health(self) -> dict[str, Any]:
        """检查浏览器健康状态（简化版）"""
        try:
            status = "healthy"
            issues = []
            connected = False
            page_count = 0
            memory_mb = 0

            if self._browser_instance:
                try:
                    connected = self._browser_instance.is_connected()

                    if self._browser_context:
                        pages = self._browser_context.pages
                        page_count = len(pages)
                except Exception:
                    connected = False

                # 计算浏览器进程内存（采样）
                for proc in psutil.process_iter(["name", "memory_info"]):
                    try:
                        name = proc.info["name"].lower()
                        if any(b in name for b in ["chrome", "chromium", "msedge", "firefox"]):
                            memory_mb += proc.info["memory_info"].rss / (1024 * 1024)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                memory_mb = round(memory_mb, 1)

                if not connected:
                    status = "error"
                    issues.append("浏览器连接已断开")
                if memory_mb > 2000:
                    status = "warning" if status != "error" else "error"
                    issues.append(f"浏览器内存占用过高: {memory_mb:.0f}MB")
                if page_count > 10:
                    status = "warning" if status == "healthy" else status
                    issues.append(f"页面数量过多: {page_count} 个")
                if self.metrics["browser_crashes"] > 0:
                    status = "warning" if status == "healthy" else status
            else:
                status = "unknown"
                page_count = 0
                memory_mb = 0

            # 更新指标
            self.metrics["browser_page_count"] = page_count
            self.metrics["browser_memory_mb"] = memory_mb

            return {
                "status": status,
                "connected": connected,
                "page_count": page_count,
                "memory_mb": memory_mb,
                "crashes": self.metrics["browser_crashes"],
                "issues": issues,
            }

        except Exception as e:
            logger.error(f"浏览器健康检查失败: {e}")
            return {"status": "error", "error": str(e), "issues": ["浏览器健康检查失败"]}

    def _calculate_overall_health(self) -> None:
        """计算总体健康状态（取最差状态）"""
        statuses = [
            self.health_status["system"],
            self.health_status["network"],
        ]

        if self.health_status["browser"] != "unknown":
            statuses.append(self.health_status["browser"])

        if "error" in statuses:
            self.health_status["overall"] = "error"
        elif "warning" in statuses:
            self.health_status["overall"] = "warning"
        else:
            self.health_status["overall"] = "healthy"

    def _generate_recommendations_simple(self) -> None:
        """生成建议（精简版）"""
        self.recommendations.clear()

        # CPU
        if self.metrics["cpu_usage"]:
            avg_cpu = sum(self.metrics["cpu_usage"]) / len(self.metrics["cpu_usage"])
            if avg_cpu > 80:
                self.recommendations.append("CPU使用率较高，建议关闭其他应用或降低搜索频率")

        # 内存
        if self.metrics["memory_usage"]:
            avg_mem = sum(self.metrics["memory_usage"]) / len(self.metrics["memory_usage"])
            if avg_mem > 80:
                self.recommendations.append("内存使用率较高，建议启用无头模式或重启应用")

        # 成功率
        if self.metrics["total_searches"] > 0:
            success_rate = self.metrics["successful_searches"] / self.metrics["total_searches"]
            if success_rate < 0.8:
                self.recommendations.append("搜索成功率较低，建议检查网络或增加等待时间")

        # 浏览器崩溃
        if self.metrics["browser_crashes"] > 3:
            self.recommendations.append("浏览器崩溃频繁，建议更新浏览器或检查系统资源")

    # 别名，保持向后兼容
    def _generate_recommendations(self) -> None:
        """向后兼容别名"""
        self._generate_recommendations_simple()

    # ============================================
    # 公共 API 方法
    # ============================================

    def record_search_result(self, success: bool, response_time: float = 0.0):
        """记录搜索结果"""
        self.metrics["total_searches"] += 1
        if success:
            self.metrics["successful_searches"] += 1
        else:
            self.metrics["failed_searches"] += 1

        # 更新平均响应时间（running average）
        if response_time > 0:
            total = self.metrics["average_response_time"] * (self.metrics["total_searches"] - 1)
            self.metrics["average_response_time"] = (total + response_time) / self.metrics[
                "total_searches"
            ]

    def record_browser_crash(self):
        """记录浏览器崩溃"""
        self.metrics["browser_crashes"] += 1
        logger.warning(f"记录浏览器崩溃 (总计: {self.metrics['browser_crashes']})")

    def record_network_error(self):
        """记录网络错误"""
        self.metrics["network_errors"] += 1
        logger.warning(f"记录网络错误 (总计: {self.metrics['network_errors']})")

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告（简化）"""
        uptime = time.time() - self.metrics["start_time"]

        cpu_usage = self.metrics["cpu_usage"]
        mem_usage = self.metrics["memory_usage"]

        return {
            "uptime_seconds": uptime,
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "total_searches": self.metrics["total_searches"],
            "success_rate": (
                self.metrics["successful_searches"] / self.metrics["total_searches"]
                if self.metrics["total_searches"] > 0
                else 0
            ),
            "average_response_time": self.metrics["average_response_time"],
            "browser_crashes": self.metrics["browser_crashes"],
            "network_errors": self.metrics["network_errors"],
            "current_cpu": cpu_usage[-1] if cpu_usage else 0,
            "current_memory": mem_usage[-1] if mem_usage else 0,
            "avg_cpu_10min": sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
            "avg_memory_10min": sum(mem_usage) / len(mem_usage) if mem_usage else 0,
        }

    def get_health_summary(self) -> str:
        """获取健康状态摘要字符串"""
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "error": "❌",
            "unknown": "❓",
        }

        overall = self.health_status["overall"]
        emoji = status_emoji.get(overall, "❓")

        summary = [
            f"{emoji} 总体状态: {overall.upper()}",
            f"系统: {status_emoji.get(self.health_status['system'], '❓')} {self.health_status['system']}",
            f"网络: {status_emoji.get(self.health_status['network'], '❓')} {self.health_status['network']}",
            f"浏览器: {status_emoji.get(self.health_status['browser'], '❓')} {self.health_status['browser']}",
        ]

        if self.metrics["total_searches"] > 0:
            success_rate = self.metrics["successful_searches"] / self.metrics["total_searches"]
            summary.append(f"成功率: {success_rate * 100:.1f}%")

        if self.metrics["browser_memory_mb"] > 0:
            summary.append(f"浏览器内存: {self.metrics['browser_memory_mb']:.0f}MB")

        if self.recommendations:
            summary.append(f"建议: {len(self.recommendations)} 条")

        return " | ".join(summary)

    def get_detailed_status(self) -> dict[str, Any]:
        """获取详细健康状态（用于实时监控）"""
        cpu_usage = self.metrics["cpu_usage"]
        mem_usage = self.metrics["memory_usage"]

        return {
            "timestamp": datetime.now().isoformat(),
            "overall": self.health_status["overall"],
            "components": {
                "system": {
                    "status": self.health_status["system"],
                    "cpu_percent": cpu_usage[-1] if cpu_usage else 0,
                    "memory_percent": mem_usage[-1] if mem_usage else 0,
                },
                "network": {"status": self.health_status["network"]},
                "browser": {
                    "status": self.health_status["browser"],
                    "memory_mb": self.metrics["browser_memory_mb"],
                    "page_count": self.metrics["browser_page_count"],
                    "crashes": self.metrics["browser_crashes"],
                },
            },
            "search_stats": {
                "total": self.metrics["total_searches"],
                "successful": self.metrics["successful_searches"],
                "failed": self.metrics["failed_searches"],
                "success_rate": (
                    self.metrics["successful_searches"] / self.metrics["total_searches"]
                    if self.metrics["total_searches"] > 0
                    else 0
                ),
            },
            "uptime_seconds": time.time() - self.metrics["start_time"],
            "recommendations": self.recommendations[:3],
        }

    def diagnose_common_issues(self) -> list[dict[str, Any]]:
        """
        诊断常见问题（简化版，保留用于测试和调试）

        Returns:
            问题诊断结果列表
        """
        diagnoses = []

        # 检查搜索成功率
        if self.metrics["total_searches"] > 10:
            success_rate = self.metrics["successful_searches"] / self.metrics["total_searches"]
            if success_rate < 0.5:
                diagnoses.append(
                    {
                        "issue": "搜索成功率过低",
                        "severity": "high",
                        "description": f"成功率仅为 {success_rate * 100:.1f}%",
                        "solutions": [
                            "检查网络连接",
                            "增加搜索间隔时间",
                            "检查Microsoft Rewards账户状态",
                        ],
                    }
                )

        # 检查浏览器崩溃
        if self.metrics["browser_crashes"] > 5:
            diagnoses.append(
                {
                    "issue": "浏览器崩溃频繁",
                    "severity": "high",
                    "description": f"已发生 {self.metrics['browser_crashes']} 次崩溃",
                    "solutions": [
                        "重启应用程序",
                        "检查系统内存是否充足",
                        "启用无头模式减少资源消耗",
                    ],
                }
            )

        # 检查网络错误
        if self.metrics["network_errors"] > 10:
            diagnoses.append(
                {
                    "issue": "网络错误频繁",
                    "severity": "medium",
                    "description": f"已发生 {self.metrics['network_errors']} 次网络错误",
                    "solutions": [
                        "检查网络连接稳定性",
                        "尝试更换DNS服务器",
                        "检查防火墙设置",
                    ],
                }
            )

        # 检查系统资源
        if self.metrics["cpu_usage"]:
            avg_cpu = sum(self.metrics["cpu_usage"]) / len(self.metrics["cpu_usage"])
            if avg_cpu > 90:
                diagnoses.append(
                    {
                        "issue": "CPU使用率过高",
                        "severity": "medium",
                        "description": f"平均CPU使用率: {avg_cpu:.1f}%",
                        "solutions": [
                            "关闭其他占用CPU的应用程序",
                            "降低搜索频率",
                            "启用无头模式",
                        ],
                    }
                )

        if self.metrics["memory_usage"]:
            avg_memory = sum(self.metrics["memory_usage"]) / len(self.metrics["memory_usage"])
            if avg_memory > 90:
                diagnoses.append(
                    {
                        "issue": "内存使用率过高",
                        "severity": "medium",
                        "description": f"平均内存使用率: {avg_memory:.1f}%",
                        "solutions": [
                            "重启应用程序",
                            "关闭其他占用内存的应用程序",
                            "启用无头模式",
                        ],
                    }
                )

        return diagnoses

    def save_health_report(self, filepath: str = "logs/health_report.json"):
        """
        保存健康报告到文件（简化版）

        Args:
            filepath: 报告文件路径
        """
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "health_status": self.health_status.copy(),
                "performance_metrics": self.get_performance_report(),
                "diagnoses": self.diagnose_common_issues(),
                "recommendations": self.recommendations.copy(),
            }

            # 确保目录存在
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"健康报告已保存到: {filepath}")

        except Exception as e:
            logger.error(f"保存健康报告失败: {e}")

    def _get_metrics_snapshot(self) -> dict[str, Any]:
        """获取指标快照（避免返回deque对象）"""
        return {k: list(v) if isinstance(v, deque) else v for k, v in self.metrics.items()}
