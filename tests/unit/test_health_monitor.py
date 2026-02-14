"""
HealthMonitor 单元测试
测试健康监控系统的各项功能
"""

import sys
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.health_monitor import HealthMonitor


class TestHealthMonitor:
    """HealthMonitor 测试类"""
    
    @pytest.fixture
    def config(self):
        """创建模拟配置"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            "monitoring.health_check.enabled": True,
            "monitoring.health_check.interval": 30,
        }.get(key, default)
        return config
    
    @pytest.fixture
    def monitor(self, config):
        """创建 HealthMonitor 实例"""
        return HealthMonitor(config)
    
    def test_init(self, monitor):
        """测试初始化"""
        assert monitor is not None
        assert monitor.enabled is True
        assert monitor.check_interval == 30
        assert "start_time" in monitor.metrics
        assert monitor.health_status["overall"] == "healthy"
    
    def test_init_disabled(self):
        """测试禁用状态初始化"""
        config = Mock()
        config.get.return_value = False
        monitor = HealthMonitor(config)
        assert monitor.enabled is False
    
    @pytest.mark.asyncio
    async def test_start_monitoring_disabled(self, config):
        """测试启动监控 - 禁用状态"""
        config.get.return_value = False
        monitor = HealthMonitor(config)
        
        # 不应该启动监控循环
        await monitor.start_monitoring()
        # 测试通过不抛出异常即可
    
    @pytest.mark.asyncio
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    async def test_check_system_health_normal(self, mock_disk, mock_memory, mock_cpu, monitor):
        """测试系统健康检查 - 正常状态"""
        # 模拟正常的系统指标
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0)
        mock_disk.return_value = Mock(used=50*1024**3, total=100*1024**3)
        
        result = await monitor._check_system_health()
        
        assert result["status"] == "healthy"
        assert result["cpu_percent"] == 50.0
        assert result["memory_percent"] == 60.0
        assert len(result["issues"]) == 0
    
    @pytest.mark.asyncio
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    async def test_check_system_health_warning(self, mock_disk, mock_memory, mock_cpu, monitor):
        """测试系统健康检查 - 警告状态"""
        # 模拟高负载系统指标
        mock_cpu.return_value = 95.0
        mock_memory.return_value = Mock(percent=90.0)
        mock_disk.return_value = Mock(used=95*1024**3, total=100*1024**3)
        
        result = await monitor._check_system_health()
        
        assert result["status"] == "warning"
        assert len(result["issues"]) > 0
        assert any("CPU使用率过高" in issue for issue in result["issues"])
        assert any("内存使用率过高" in issue for issue in result["issues"])
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_check_network_health_success(self, mock_session_class, monitor):
        """测试网络健康检查 - 成功"""
        # 模拟成功的网络请求
        mock_response = Mock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_class.return_value = mock_session
        
        result = await monitor._check_network_health()
        
        assert result["status"] == "healthy"
        assert result["connection_rate"] >= 0.8
        assert len(result["issues"]) == 0
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_check_network_health_failure(self, mock_session_class, monitor):
        """测试网络健康检查 - 失败"""
        # 模拟网络请求失败
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Network error")
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_class.return_value = mock_session
        
        result = await monitor._check_network_health()
        
        assert result["status"] == "error"
        assert result["connection_rate"] == 0.0
        assert len(result["issues"]) > 0
    
    def test_record_search_result_success(self, monitor):
        """测试记录搜索结果 - 成功"""
        monitor.record_search_result(True, 2.5)
        
        assert monitor.metrics["total_searches"] == 1
        assert monitor.metrics["successful_searches"] == 1
        assert monitor.metrics["failed_searches"] == 0
        assert monitor.metrics["average_response_time"] == 2.5
    
    def test_record_search_result_failure(self, monitor):
        """测试记录搜索结果 - 失败"""
        monitor.record_search_result(False)
        
        assert monitor.metrics["total_searches"] == 1
        assert monitor.metrics["successful_searches"] == 0
        assert monitor.metrics["failed_searches"] == 1
    
    def test_record_multiple_search_results(self, monitor):
        """测试记录多个搜索结果"""
        monitor.record_search_result(True, 2.0)
        monitor.record_search_result(True, 3.0)
        monitor.record_search_result(False)
        
        assert monitor.metrics["total_searches"] == 3
        assert monitor.metrics["successful_searches"] == 2
        assert monitor.metrics["failed_searches"] == 1
        assert monitor.metrics["average_response_time"] == 2.5  # (2.0 + 3.0) / 2
    
    def test_record_browser_crash(self, monitor):
        """测试记录浏览器崩溃"""
        monitor.record_browser_crash()
        monitor.record_browser_crash()
        
        assert monitor.metrics["browser_crashes"] == 2
    
    def test_record_network_error(self, monitor):
        """测试记录网络错误"""
        monitor.record_network_error()
        monitor.record_network_error()
        monitor.record_network_error()
        
        assert monitor.metrics["network_errors"] == 3
    
    def test_get_performance_report(self, monitor):
        """测试获取性能报告"""
        # 添加一些测试数据
        monitor.record_search_result(True, 2.0)
        monitor.record_search_result(False)
        monitor.metrics["cpu_usage"] = [50.0, 60.0, 55.0]
        monitor.metrics["memory_usage"] = [70.0, 75.0, 72.0]
        
        report = monitor.get_performance_report()
        
        assert "uptime_seconds" in report
        assert "uptime_formatted" in report
        assert report["total_searches"] == 2
        assert report["success_rate"] == 0.5
        assert report["current_cpu"] == 55.0
        assert report["current_memory"] == 72.0
    
    def test_diagnose_common_issues_low_success_rate(self, monitor):
        """测试问题诊断 - 低成功率"""
        # 模拟低成功率
        for _ in range(15):
            monitor.record_search_result(False)
        for _ in range(5):
            monitor.record_search_result(True)
        
        diagnoses = monitor.diagnose_common_issues()
        
        assert len(diagnoses) > 0
        assert any("搜索成功率过低" in d["issue"] for d in diagnoses)
        assert any(d["severity"] == "high" for d in diagnoses)
    
    def test_diagnose_common_issues_frequent_crashes(self, monitor):
        """测试问题诊断 - 频繁崩溃"""
        # 模拟频繁崩溃
        for _ in range(6):
            monitor.record_browser_crash()
        
        diagnoses = monitor.diagnose_common_issues()
        
        assert len(diagnoses) > 0
        assert any("浏览器崩溃频繁" in d["issue"] for d in diagnoses)
    
    def test_diagnose_common_issues_high_cpu(self, monitor):
        """测试问题诊断 - 高CPU使用率"""
        # 模拟高CPU使用率
        monitor.metrics["cpu_usage"] = [95.0] * 10
        
        diagnoses = monitor.diagnose_common_issues()
        
        assert len(diagnoses) > 0
        assert any("CPU使用率过高" in d["issue"] for d in diagnoses)
    
    def test_calculate_overall_health(self, monitor):
        """测试总体健康状态计算"""
        # 测试健康状态
        monitor.health_status["system"] = "healthy"
        monitor.health_status["network"] = "healthy"
        monitor._calculate_overall_health()
        assert monitor.health_status["overall"] == "healthy"
        
        # 测试警告状态
        monitor.health_status["system"] = "warning"
        monitor.health_status["network"] = "healthy"
        monitor._calculate_overall_health()
        assert monitor.health_status["overall"] == "warning"
        
        # 测试错误状态
        monitor.health_status["system"] = "error"
        monitor.health_status["network"] = "healthy"
        monitor._calculate_overall_health()
        assert monitor.health_status["overall"] == "error"
    
    def test_generate_recommendations(self, monitor):
        """测试生成建议"""
        # 模拟高CPU和内存使用率
        monitor.metrics["cpu_usage"] = [85.0] * 10
        monitor.metrics["memory_usage"] = [85.0] * 10
        
        # 模拟低成功率
        monitor.record_search_result(False)
        monitor.record_search_result(False)
        monitor.record_search_result(True)
        
        monitor._generate_recommendations()
        
        assert len(monitor.recommendations) > 0
        assert any("CPU使用率较高" in rec for rec in monitor.recommendations)
        assert any("内存使用率较高" in rec for rec in monitor.recommendations)
    
    @patch('builtins.open', create=True)
    @patch('pathlib.Path.mkdir')
    @patch('json.dump')
    def test_save_health_report(self, mock_json_dump, mock_mkdir, mock_open, monitor):
        """测试保存健康报告"""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        monitor.save_health_report("test_report.json")
        
        mock_mkdir.assert_called_once()
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()
    
    def test_get_health_summary(self, monitor):
        """测试获取健康状态摘要"""
        monitor.health_status["overall"] = "warning"
        monitor.health_status["system"] = "healthy"
        monitor.health_status["network"] = "warning"
        monitor.recommendations = ["建议1", "建议2"]
        
        # 添加搜索数据
        monitor.record_search_result(True)
        monitor.record_search_result(True)
        monitor.record_search_result(False)
        
        summary = monitor.get_health_summary()
        
        assert "WARNING" in summary
        assert "healthy" in summary
        assert "warning" in summary
        assert "66.7%" in summary  # 成功率
        assert "2 条" in summary  # 建议数量


@pytest.mark.asyncio
async def test_health_monitor_integration():
    """集成测试 - 完整的健康监控流程"""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        "monitoring.health_check.enabled": True,
        "monitoring.health_check.interval": 1,  # 短间隔用于测试
    }.get(key, default)
    
    monitor = HealthMonitor(config)
    
    # 记录一些测试数据
    monitor.record_search_result(True, 1.5)
    monitor.record_search_result(True, 2.0)
    monitor.record_search_result(False)
    
    # 执行健康检查
    with patch('psutil.cpu_percent', return_value=50.0), \
         patch('psutil.virtual_memory', return_value=Mock(percent=60.0)), \
         patch('psutil.disk_usage', return_value=Mock(used=50*1024**3, total=100*1024**3)), \
         patch('aiohttp.ClientSession') as mock_session_class:
        
        # 模拟网络检查
        mock_response = Mock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_class.return_value = mock_session
        
        result = await monitor.perform_health_check()
        
        assert result["status"]["overall"] == "healthy"
        assert result["metrics"]["total_searches"] == 3
        assert result["metrics"]["success_rate"] == 2/3


if __name__ == "__main__":
    pytest.main([__file__])