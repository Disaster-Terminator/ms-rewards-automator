"""
健康服务
管理系统健康状态
"""

import logging
import time
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class HealthService:
    """健康服务类"""

    def __init__(self):
        """初始化健康服务"""
        self.start_time = time.time()
        self._last_health: dict[str, Any] = {}

    def get_health(self) -> dict[str, Any]:
        """
        获取健康状态

        Returns:
            健康状态数据
        """
        try:
            system_health = self._check_system()
            network_health = self._check_network()
            browser_health = self._check_browser()

            overall = self._calculate_overall(system_health, network_health, browser_health)

            self._last_health = {
                "overall": overall,
                "system": system_health,
                "network": network_health,
                "browser": browser_health,
                "search_stats": {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "success_rate": 0.0,
                },
                "uptime_seconds": time.time() - self.start_time,
                "recommendations": self._generate_recommendations(system_health, network_health, browser_health),
            }

            return self._last_health

        except Exception as e:
            logger.error(f"获取健康状态失败: {e}")
            return {
                "overall": "error",
                "system": {"status": "error", "error": str(e)},
                "network": {"status": "unknown"},
                "browser": {"status": "unknown"},
                "search_stats": {},
                "uptime_seconds": time.time() - self.start_time,
                "recommendations": ["健康检查失败"],
            }

    def _check_system(self) -> dict[str, Any]:
        """检查系统状态"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            status = "healthy"
            issues = []

            if cpu_percent > 90:
                status = "warning"
                issues.append(f"CPU 使用率过高: {cpu_percent:.1f}%")

            if memory.percent > 85:
                status = "warning"
                issues.append(f"内存使用率过高: {memory.percent:.1f}%")

            if disk.percent > 90:
                status = "warning"
                issues.append(f"磁盘空间不足: {disk.percent:.1f}%")

            return {
                "status": status,
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": round(disk.percent, 1),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "issues": issues,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_network(self) -> dict[str, Any]:
        """检查网络状态"""
        try:
            import socket

            test_hosts = [
                ("www.bing.com", 443),
                ("rewards.microsoft.com", 443),
            ]

            successful = 0
            for host, port in test_hosts:
                try:
                    sock = socket.create_connection((host, port), timeout=5)
                    sock.close()
                    successful += 1
                except Exception:
                    pass

            connection_rate = successful / len(test_hosts)

            if connection_rate >= 1.0:
                status = "healthy"
            elif connection_rate >= 0.5:
                status = "warning"
            else:
                status = "error"

            return {
                "status": status,
                "connection_rate": round(connection_rate, 2),
                "successful_connections": successful,
                "total_tests": len(test_hosts),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _check_browser(self) -> dict[str, Any]:
        """检查浏览器状态"""
        try:
            browser_processes = 0
            browser_memory = 0

            browser_names = ['chrome', 'chromium', 'msedge', 'firefox']

            for proc in psutil.process_iter(['name', 'memory_info']):
                try:
                    name = proc.info['name'].lower()
                    if any(b in name for b in browser_names):
                        browser_processes += 1
                        browser_memory += proc.info['memory_info'].rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            status = "healthy"
            issues = []

            if browser_processes > 10:
                status = "warning"
                issues.append(f"浏览器进程过多: {browser_processes}")

            browser_memory_mb = browser_memory / (1024 * 1024)
            if browser_memory_mb > 2000:
                status = "warning"
                issues.append(f"浏览器内存占用过高: {browser_memory_mb:.0f}MB")

            return {
                "status": status,
                "processes": browser_processes,
                "memory_mb": round(browser_memory_mb, 1),
                "issues": issues,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _calculate_overall(self, system: dict, network: dict, browser: dict) -> str:
        """计算总体状态"""
        statuses = [system.get("status", "unknown"), network.get("status", "unknown")]

        if browser.get("status") != "unknown":
            statuses.append(browser.get("status"))

        if "error" in statuses:
            return "error"
        elif "warning" in statuses:
            return "warning"
        else:
            return "healthy"

    def _generate_recommendations(self, system: dict, network: dict, browser: dict) -> list[str]:
        """生成建议"""
        recommendations = []

        if system.get("cpu_percent", 0) > 80:
            recommendations.append("CPU 使用率较高，建议关闭其他应用程序")

        if system.get("memory_percent", 0) > 80:
            recommendations.append("内存使用率较高，建议启用无头模式")

        if system.get("disk_percent", 0) > 85:
            recommendations.append("磁盘空间不足，建议清理日志和截图")

        if network.get("connection_rate", 1) < 0.8:
            recommendations.append("网络连接不稳定，请检查网络设置")

        if browser.get("memory_mb", 0) > 1500:
            recommendations.append("浏览器内存占用过高，建议重启应用")

        return recommendations

    def get_uptime_formatted(self) -> str:
        """获取格式化的运行时间"""
        uptime = time.time() - self.start_time

        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)

        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"
