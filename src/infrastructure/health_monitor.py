"""
健康监控模块
提供系统健康检查、性能监控和问题诊断功能
"""

import asyncio
import logging
import psutil
import time
import json
import platform
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class HealthMonitor:
    """健康监控器类"""
    
    def __init__(self, config=None):
        """
        初始化健康监控器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.enabled = config.get("monitoring.health_check.enabled", True) if config else True
        self.check_interval = config.get("monitoring.health_check.interval", 30) if config else 30
        
        # 性能指标
        self.metrics = {
            "start_time": time.time(),
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "average_response_time": 0.0,
            "memory_usage": [],
            "cpu_usage": [],
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
        
        # 问题诊断
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
        """启动健康监控"""
        if not self.enabled:
            logger.debug("健康监控已禁用")
            return
        
        logger.info("启动健康监控...")
        
        # 启动后台监控任务并保存引用
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
        """监控循环"""
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
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """
        执行健康检查
        
        Returns:
            健康检查结果
        """
        logger.debug("执行健康检查...")
        
        # 系统资源检查
        system_health = await self._check_system_health()
        
        # 网络连接检查
        network_health = await self._check_network_health()
        
        # 浏览器健康检查
        browser_health = await self._check_browser_health()
        
        # 更新健康状态
        self.health_status.update({
            "system": system_health["status"],
            "network": network_health["status"],
            "browser": browser_health["status"],
            "last_check": datetime.now().isoformat(),
        })
        
        # 计算总体健康状态
        self._calculate_overall_health()
        
        # 计算成功率
        total_searches = self.metrics["total_searches"]
        if total_searches > 0:
            self.metrics["success_rate"] = self.metrics["successful_searches"] / total_searches
        else:
            self.metrics["success_rate"] = 0.0
        
        # 生成建议
        self._generate_recommendations()
        
        return {
            "status": self.health_status,
            "metrics": self.metrics,
            "issues": self.issues,
            "recommendations": self.recommendations,
        }
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics["cpu_usage"].append(cpu_percent)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.metrics["memory_usage"].append(memory_percent)
            
            # 保持最近100个数据点
            if len(self.metrics["cpu_usage"]) > 100:
                self.metrics["cpu_usage"] = self.metrics["cpu_usage"][-100:]
            if len(self.metrics["memory_usage"]) > 100:
                self.metrics["memory_usage"] = self.metrics["memory_usage"][-100:]
            
            # 磁盘空间 - 跨平台支持
            system_disk = 'C:\\' if platform.system() == 'Windows' else '/'
            try:
                disk = psutil.disk_usage(system_disk)
                disk_percent = (disk.used / disk.total) * 100
            except Exception as disk_error:
                logger.debug(f"无法获取磁盘信息: {disk_error}")
                disk_percent = 0
            
            # 判断系统健康状态
            status = "healthy"
            issues = []
            
            if cpu_percent > 90:
                status = "warning"
                issues.append(f"CPU使用率过高: {cpu_percent:.1f}%")
            
            if memory_percent > 85:
                status = "warning"
                issues.append(f"内存使用率过高: {memory_percent:.1f}%")
            
            if disk_percent > 90:
                status = "warning"
                issues.append(f"磁盘空间不足: {disk_percent:.1f}%")
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "issues": issues,
            }
            
        except Exception as e:
            logger.error(f"系统健康检查失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "issues": ["系统健康检查失败"],
            }
    
    async def _check_network_health(self) -> Dict[str, Any]:
        """检查网络健康状态"""
        try:
            import aiohttp
            
            # 测试关键网站连接
            test_urls = [
                "https://www.bing.com",
                "https://rewards.microsoft.com",
                "https://www.google.com",  # 备用测试
            ]
            
            successful_connections = 0
            response_times = []
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                for url in test_urls:
                    try:
                        start_time = time.time()
                        async with session.get(url) as response:
                            response_time = time.time() - start_time
                            response_times.append(response_time)
                            
                            if response.status == 200:
                                successful_connections += 1
                    except Exception as e:
                        logger.debug(f"网络测试失败 {url}: {e}")
            
            # 计算平均响应时间
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # 判断网络健康状态
            connection_rate = successful_connections / len(test_urls)
            
            if connection_rate >= 0.8 and avg_response_time < 5.0:
                status = "healthy"
            elif connection_rate >= 0.5:
                status = "warning"
            else:
                status = "error"
            
            issues = []
            if connection_rate < 0.8:
                issues.append(f"网络连接不稳定: {connection_rate*100:.0f}% 成功率")
            if avg_response_time > 5.0:
                issues.append(f"网络响应缓慢: {avg_response_time:.1f}s")
            
            return {
                "status": status,
                "connection_rate": connection_rate,
                "avg_response_time": avg_response_time,
                "successful_connections": successful_connections,
                "total_tests": len(test_urls),
                "issues": issues,
            }
            
        except Exception as e:
            logger.error(f"网络健康检查失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "issues": ["网络健康检查失败"],
            }
    
    async def _check_browser_health(self) -> Dict[str, Any]:
        """检查浏览器健康状态"""
        try:
            issues = []
            status = "healthy"
            
            browser_connected = False
            page_count = 0
            browser_memory_mb = 0
            
            if self._browser_instance:
                try:
                    browser_connected = self._browser_instance.is_connected()
                    
                    if self._browser_context:
                        pages = self._browser_context.pages
                        page_count = len(pages)
                        
                        for page in pages:
                            try:
                                if not page.is_closed():
                                    pass
                            except Exception:
                                pass
                except Exception as e:
                    logger.debug(f"浏览器状态检查异常: {e}")
                    browser_connected = False
                
                self.metrics["browser_page_count"] = page_count
                
                for proc in psutil.process_iter(['name', 'memory_info']):
                    try:
                        name = proc.info['name'].lower()
                        if any(browser in name for browser in ['chrome', 'chromium', 'msedge', 'firefox']):
                            browser_memory_mb += proc.info['memory_info'].rss / (1024 * 1024)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                self.metrics["browser_memory_mb"] = round(browser_memory_mb, 1)
                
                if not browser_connected:
                    status = "error"
                    issues.append("浏览器连接已断开")
                
                if browser_memory_mb > 2000:
                    status = "warning" if status != "error" else "error"
                    issues.append(f"浏览器内存占用过高: {browser_memory_mb:.0f}MB")
                
                if page_count > 10:
                    status = "warning" if status == "healthy" else status
                    issues.append(f"页面数量过多: {page_count} 个")
                
                if self.metrics["browser_crashes"] > 0:
                    status = "warning" if status == "healthy" else status
            else:
                self.metrics["browser_page_count"] = 0
                self.metrics["browser_memory_mb"] = 0
                status = "unknown"
            
            return {
                "status": status,
                "connected": browser_connected,
                "page_count": page_count,
                "memory_mb": browser_memory_mb,
                "crashes": self.metrics["browser_crashes"],
                "issues": issues,
            }
            
        except Exception as e:
            logger.error(f"浏览器健康检查失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "issues": ["浏览器健康检查失败"],
            }
    
    def _calculate_overall_health(self):
        """计算总体健康状态"""
        statuses = [
            self.health_status["system"],
            self.health_status["network"],
        ]
        
        browser_status = self.health_status["browser"]
        if browser_status != "unknown":
            statuses.append(browser_status)
        
        if "error" in statuses:
            self.health_status["overall"] = "error"
        elif "warning" in statuses:
            self.health_status["overall"] = "warning"
        else:
            self.health_status["overall"] = "healthy"
    
    def _generate_recommendations(self):
        """生成优化建议"""
        self.recommendations.clear()
        
        # CPU使用率建议
        if self.metrics["cpu_usage"]:
            avg_cpu = sum(self.metrics["cpu_usage"][-10:]) / len(self.metrics["cpu_usage"][-10:])
            if avg_cpu > 80:
                self.recommendations.append("CPU使用率较高，建议关闭其他应用程序或降低搜索频率")
        
        # 内存使用率建议
        if self.metrics["memory_usage"]:
            avg_memory = sum(self.metrics["memory_usage"][-10:]) / len(self.metrics["memory_usage"][-10:])
            if avg_memory > 80:
                self.recommendations.append("内存使用率较高，建议启用无头模式或重启应用")
        
        # 成功率建议
        if self.metrics["total_searches"] > 0:
            success_rate = self.metrics["successful_searches"] / self.metrics["total_searches"]
            if success_rate < 0.8:
                self.recommendations.append("搜索成功率较低，建议检查网络连接或增加等待时间")
        
        # 浏览器崩溃建议
        if self.metrics["browser_crashes"] > 3:
            self.recommendations.append("浏览器崩溃频繁，建议更新浏览器或检查系统资源")
    
    def record_search_result(self, success: bool, response_time: float = 0.0):
        """
        记录搜索结果
        
        Args:
            success: 是否成功
            response_time: 响应时间
        """
        self.metrics["total_searches"] += 1
        
        if success:
            self.metrics["successful_searches"] += 1
        else:
            self.metrics["failed_searches"] += 1
        
        # 更新平均响应时间
        if response_time > 0:
            total_time = self.metrics["average_response_time"] * (self.metrics["total_searches"] - 1)
            self.metrics["average_response_time"] = (total_time + response_time) / self.metrics["total_searches"]
    
    def record_browser_crash(self):
        """记录浏览器崩溃"""
        self.metrics["browser_crashes"] += 1
        logger.warning(f"记录浏览器崩溃 (总计: {self.metrics['browser_crashes']})")
    
    def record_network_error(self):
        """记录网络错误"""
        self.metrics["network_errors"] += 1
        logger.warning(f"记录网络错误 (总计: {self.metrics['network_errors']})")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        获取性能报告
        
        Returns:
            性能报告数据
        """
        uptime = time.time() - self.metrics["start_time"]
        
        return {
            "uptime_seconds": uptime,
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "total_searches": self.metrics["total_searches"],
            "success_rate": (
                self.metrics["successful_searches"] / self.metrics["total_searches"]
                if self.metrics["total_searches"] > 0 else 0
            ),
            "average_response_time": self.metrics["average_response_time"],
            "browser_crashes": self.metrics["browser_crashes"],
            "network_errors": self.metrics["network_errors"],
            "current_cpu": self.metrics["cpu_usage"][-1] if self.metrics["cpu_usage"] else 0,
            "current_memory": self.metrics["memory_usage"][-1] if self.metrics["memory_usage"] else 0,
            "avg_cpu_10min": (
                sum(self.metrics["cpu_usage"][-20:]) / len(self.metrics["cpu_usage"][-20:])
                if len(self.metrics["cpu_usage"]) >= 20 else 0
            ),
            "avg_memory_10min": (
                sum(self.metrics["memory_usage"][-20:]) / len(self.metrics["memory_usage"][-20:])
                if len(self.metrics["memory_usage"]) >= 20 else 0
            ),
        }
    
    def diagnose_common_issues(self) -> List[Dict[str, Any]]:
        """
        诊断常见问题
        
        Returns:
            问题诊断结果列表
        """
        diagnoses = []
        
        # 检查搜索成功率
        if self.metrics["total_searches"] > 10:
            success_rate = self.metrics["successful_searches"] / self.metrics["total_searches"]
            if success_rate < 0.5:
                diagnoses.append({
                    "issue": "搜索成功率过低",
                    "severity": "high",
                    "description": f"成功率仅为 {success_rate*100:.1f}%",
                    "solutions": [
                        "检查网络连接",
                        "增加搜索间隔时间",
                        "检查Microsoft Rewards账户状态",
                        "更新浏览器版本",
                    ]
                })
        
        # 检查浏览器崩溃
        if self.metrics["browser_crashes"] > 5:
            diagnoses.append({
                "issue": "浏览器崩溃频繁",
                "severity": "high",
                "description": f"已发生 {self.metrics['browser_crashes']} 次崩溃",
                "solutions": [
                    "重启应用程序",
                    "检查系统内存是否充足",
                    "更新Playwright和浏览器",
                    "启用无头模式减少资源消耗",
                ]
            })
        
        # 检查网络错误
        if self.metrics["network_errors"] > 10:
            diagnoses.append({
                "issue": "网络错误频繁",
                "severity": "medium",
                "description": f"已发生 {self.metrics['network_errors']} 次网络错误",
                "solutions": [
                    "检查网络连接稳定性",
                    "尝试更换DNS服务器",
                    "检查防火墙设置",
                    "增加网络超时时间",
                ]
            })
        
        # 检查系统资源
        if self.metrics["cpu_usage"]:
            avg_cpu = sum(self.metrics["cpu_usage"][-10:]) / len(self.metrics["cpu_usage"][-10:])
            if avg_cpu > 90:
                diagnoses.append({
                    "issue": "CPU使用率过高",
                    "severity": "medium",
                    "description": f"平均CPU使用率: {avg_cpu:.1f}%",
                    "solutions": [
                        "关闭其他占用CPU的应用程序",
                        "降低搜索频率",
                        "启用无头模式",
                        "检查后台进程",
                    ]
                })
        
        if self.metrics["memory_usage"]:
            avg_memory = sum(self.metrics["memory_usage"][-10:]) / len(self.metrics["memory_usage"][-10:])
            if avg_memory > 90:
                diagnoses.append({
                    "issue": "内存使用率过高",
                    "severity": "medium",
                    "description": f"平均内存使用率: {avg_memory:.1f}%",
                    "solutions": [
                        "重启应用程序",
                        "关闭其他占用内存的应用程序",
                        "启用无头模式",
                        "检查内存泄漏",
                    ]
                })
        
        return diagnoses
    
    def save_health_report(self, filepath: str = "logs/health_report.json"):
        """
        保存健康报告到文件
        
        Args:
            filepath: 报告文件路径
        """
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "health_status": self.health_status,
                "performance_metrics": self.get_performance_report(),
                "diagnoses": self.diagnose_common_issues(),
                "recommendations": self.recommendations,
            }
            
            # 确保目录存在
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"健康报告已保存到: {filepath}")
            
        except Exception as e:
            logger.error(f"保存健康报告失败: {e}")
    
    def get_health_summary(self) -> str:
        """
        获取健康状态摘要
        
        Returns:
            健康状态摘要字符串
        """
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "error": "❌",
            "unknown": "❓",
        }
        
        overall_status = self.health_status["overall"]
        emoji = status_emoji.get(overall_status, "❓")
        
        summary = [
            f"{emoji} 总体状态: {overall_status.upper()}",
            f"系统: {status_emoji.get(self.health_status['system'], '❓')} {self.health_status['system']}",
            f"网络: {status_emoji.get(self.health_status['network'], '❓')} {self.health_status['network']}",
            f"浏览器: {status_emoji.get(self.health_status['browser'], '❓')} {self.health_status['browser']}",
        ]
        
        if self.metrics["total_searches"] > 0:
            success_rate = self.metrics["successful_searches"] / self.metrics["total_searches"]
            summary.append(f"成功率: {success_rate*100:.1f}%")
        
        if self.metrics["browser_memory_mb"] > 0:
            summary.append(f"浏览器内存: {self.metrics['browser_memory_mb']:.0f}MB")
        
        if self.recommendations:
            summary.append(f"建议: {len(self.recommendations)} 条")
        
        return " | ".join(summary)
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """
        获取详细健康状态（用于实时监控）
        
        Returns:
            详细状态字典
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "overall": self.health_status["overall"],
            "components": {
                "system": {
                    "status": self.health_status["system"],
                    "cpu_percent": self.metrics["cpu_usage"][-1] if self.metrics["cpu_usage"] else 0,
                    "memory_percent": self.metrics["memory_usage"][-1] if self.metrics["memory_usage"] else 0,
                },
                "network": {
                    "status": self.health_status["network"],
                },
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
                    if self.metrics["total_searches"] > 0 else 0
                ),
            },
            "uptime_seconds": time.time() - self.metrics["start_time"],
            "recommendations": self.recommendations[:3],
        }
