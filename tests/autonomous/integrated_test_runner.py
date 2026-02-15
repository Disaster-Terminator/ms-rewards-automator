"""
集成测试运行器
复用 MSRewardsApp 执行完整测试流程，同时进行问题检测和诊断
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from .screenshot_manager import ScreenshotManager
from .page_inspector import PageInspector, DetectedIssue, IssueSeverity, IssueType
from .diagnostic_engine import DiagnosticEngine, DiagnosisResult
from .reporter import TestReporter, TestStep

logger = logging.getLogger(__name__)


class IntegratedTestRunner:
    """集成测试运行器 - 复用 MSRewardsApp 执行完整测试"""
    
    def __init__(self, config_path: str = "config.yaml", user_mode: bool = False):
        """
        初始化集成测试运行器
        
        Args:
            config_path: 配置文件路径
            user_mode: 是否启用用户模式（鲁棒性测试，启用防检测）
        """
        self.config_path = config_path
        self.user_mode = user_mode
        
        self.screenshot_manager = ScreenshotManager()
        self.page_inspector = PageInspector()
        self.diagnostic_engine = DiagnosticEngine()
        self.reporter = TestReporter()
        
        self.config = None
        self.app = None
        self.args = None
        
        self.test_issues: List[DetectedIssue] = []
        self.test_diagnoses: List[DiagnosisResult] = []
        self.test_steps: List[TestStep] = []
        
        self.points_tracking = {
            "initial": None,
            "final": None,
            "gained": 0,
            "history": []
        }
        
        mode_str = "用户模式" if user_mode else "开发模式"
        logger.info(f"集成测试运行器初始化完成 ({mode_str})")
    
    async def initialize(self) -> bool:
        """初始化测试环境"""
        try:
            from infrastructure.config_manager import ConfigManager
            import argparse
            
            self.config = ConfigManager(
                self.config_path, 
                dev_mode=not self.user_mode,
                user_mode=self.user_mode
            )
            
            self.args = argparse.Namespace(
                mode="fast",
                dev=not self.user_mode,
                headless=False,
                browser="chromium",
                desktop_only=False,
                mobile_only=False,
                skip_daily_tasks=False,
                dry_run=False
            )
            
            mode_str = "用户模式（启用防检测）" if self.user_mode else "开发模式（快速调试）"
            logger.info(f"测试环境初始化成功 - {mode_str}")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def run_full_test(self) -> Dict[str, Any]:
        """运行完整测试"""
        results = {
            "session_id": self.screenshot_manager.session_id,
            "tests": {},
            "reports": {}
        }
        
        start_time = self.reporter.start_test("完整功能测试")
        
        try:
            if not await self.initialize():
                raise Exception("初始化失败")
            
            from infrastructure.ms_rewards_app import MSRewardsApp
            self.app = MSRewardsApp(self.config, self.args)
            
            original_run = self.app.run
            
            async def wrapped_run():
                return await self._wrapped_execute(original_run)
            
            exit_code = await wrapped_run()
            
            results["tests"]["full_test"] = exit_code == 0
            
        except Exception as e:
            logger.error(f"测试执行失败: {e}")
            import traceback
            traceback.print_exc()
            results["tests"]["full_test"] = False
            results["error"] = str(e)
            
        finally:
            await self._cleanup()
        
        self.reporter.end_test(
            "完整功能测试",
            "passed" if results["tests"].get("full_test") else "failed",
            start_time,
            self.test_steps,
            self.test_issues,
            self.test_diagnoses,
            self.points_tracking
        )
        
        results["reports"] = self.generate_reports()
        
        return results
    
    async def _wrapped_execute(self, original_run):
        """包装执行过程，添加监控和诊断"""
        try:
            await self._step_init_components()
            await self._step_create_browser()
            await self._step_check_login()
            await self._step_check_points()
            await self._step_execute_searches()
            await self._step_execute_tasks()
            await self._step_generate_report()
            
            return 0
            
        except Exception as e:
            logger.error(f"测试执行异常: {e}")
            
            if self.app and self.app.page:
                await self.screenshot_manager.capture_on_error(
                    self.app.page, e, "test_execution"
                )
            
            self.test_issues.append(DetectedIssue(
                issue_type=self.page_inspector._map_exception_to_issue_type(e),
                severity=IssueSeverity.ERROR,
                title="测试执行异常",
                description=str(e),
                suggestions=["检查异常堆栈", "验证测试环境"]
            ))
            
            raise
    
    async def _step_init_components(self):
        """步骤1: 初始化组件"""
        step_start = time.time()
        logger.info("\n[1/7] 初始化组件...")
        
        try:
            await self.app._init_components()
            
            await self._record_step("初始化组件", True, step_start)
            
        except Exception as e:
            await self._record_step("初始化组件", False, step_start, str(e))
            raise
    
    async def _step_create_browser(self):
        """步骤2: 创建浏览器"""
        step_start = time.time()
        logger.info("\n[2/7] 创建浏览器...")
        
        try:
            await self.app._create_browser()
            
            screenshot_path = await self.screenshot_manager.capture(
                self.app.page, "browser_created", "浏览器创建成功"
            )
            
            issues = await self.page_inspector.inspect_page(self.app.page)
            await self._capture_issue_screenshots(issues, screenshot_path)
            self.test_issues.extend(issues)
            
            await self._record_step("创建浏览器", True, step_start)
            
        except Exception as e:
            await self._record_step("创建浏览器", False, step_start, str(e))
            raise
    
    async def _step_check_login(self):
        """步骤3: 检查登录状态"""
        step_start = time.time()
        logger.info("\n[3/7] 检查登录状态...")
        
        try:
            await self.app._handle_login()
            
            screenshot_path = await self.screenshot_manager.capture(
                self.app.page, "login_status", "登录状态检查"
            )
            
            issues = await self.page_inspector.inspect_page(self.app.page)
            await self._capture_issue_screenshots(issues, screenshot_path)
            self.test_issues.extend(issues)
            
            await self._record_step("检查登录状态", True, step_start)
            
        except Exception as e:
            await self._record_step("检查登录状态", False, step_start, str(e))
            raise
    
    async def _step_check_points(self):
        """步骤4: 检查初始积分"""
        step_start = time.time()
        logger.info("\n[4/7] 检查初始积分...")
        
        try:
            await self.app._check_initial_points()
            
            if hasattr(self.app, 'state_monitor') and self.app.state_monitor:
                self.points_tracking["initial"] = getattr(self.app.state_monitor, "initial_points", None)
                if self.points_tracking["initial"] is not None:
                    logger.info(f"  📊 初始积分: {self.points_tracking['initial']}")
            
            screenshot_path = await self.screenshot_manager.capture(
                self.app.page, "initial_points", "初始积分检查"
            )
            
            issues = await self.page_inspector.inspect_page(self.app.page)
            await self._capture_issue_screenshots(issues, screenshot_path)
            self.test_issues.extend(issues)
            
            await self._record_step("检查初始积分", True, step_start)
            
        except Exception as e:
            await self._record_step("检查初始积分", False, step_start, str(e))
            raise
    
    async def _step_execute_searches(self):
        """步骤5-6: 执行搜索"""
        step_start = time.time()
        logger.info("\n[5-6/7] 执行搜索...")
        
        try:
            await self.app._execute_searches()
            
            current_points = await self._get_current_points()
            if current_points is not None:
                self.points_tracking["history"].append({
                    "stage": "after_search",
                    "points": current_points,
                    "timestamp": datetime.now().isoformat()
                })
                if self.points_tracking["initial"]:
                    gained = current_points - self.points_tracking["initial"]
                    logger.info(f"  📊 搜索后积分: {current_points} (变化: {'+' if gained >= 0 else ''}{gained})")
            
            screenshot_path = await self.screenshot_manager.capture(
                self.app.page, "search_completed", "搜索完成"
            )
            
            issues = await self.page_inspector.inspect_page(self.app.page)
            await self._capture_issue_screenshots(issues, screenshot_path)
            self.test_issues.extend(issues)
            
            search_success = self._verify_search_success()
            if not search_success:
                self.test_issues.append(DetectedIssue(
                    issue_type=IssueType.VALIDATION_ERROR,
                    severity=IssueSeverity.WARNING,
                    title="搜索可能未成功执行",
                    description="搜索步骤完成但可能未实际执行搜索",
                    suggestions=["检查搜索日志", "验证搜索次数"]
                ))
            
            await self._record_step("执行搜索", search_success, step_start)
            
        except Exception as e:
            await self._record_step("执行搜索", False, step_start, str(e))
            raise
    
    def _verify_search_success(self) -> bool:
        """验证搜索是否成功"""
        if hasattr(self.app, 'state_monitor') and self.app.state_monitor:
            session_data = getattr(self.app.state_monitor, 'session_data', {})
            desktop_searches = session_data.get('desktop_searches', 0)
            mobile_searches = session_data.get('mobile_searches', 0)
            total_searches = desktop_searches + mobile_searches
            
            if total_searches > 0:
                logger.info(f"  ✓ 搜索验证: 桌面{desktop_searches}次, 移动{mobile_searches}次")
                return True
        return True
    
    async def _step_execute_tasks(self):
        """步骤7: 执行日常任务"""
        step_start = time.time()
        logger.info("\n[7/7] 执行日常任务...")
        
        try:
            await self.app._execute_daily_tasks()
            
            current_points = await self._get_current_points()
            if current_points is not None:
                self.points_tracking["final"] = current_points
                self.points_tracking["history"].append({
                    "stage": "after_tasks",
                    "points": current_points,
                    "timestamp": datetime.now().isoformat()
                })
                if self.points_tracking["initial"]:
                    self.points_tracking["gained"] = current_points - self.points_tracking["initial"]
                    logger.info(f"  📊 最终积分: {current_points} (总变化: {'+' if self.points_tracking['gained'] >= 0 else ''}{self.points_tracking['gained']})")
            
            screenshot_path = await self.screenshot_manager.capture(
                self.app.page, "tasks_completed", "任务完成"
            )
            
            issues = await self.page_inspector.inspect_page(self.app.page)
            await self._capture_issue_screenshots(issues, screenshot_path)
            self.test_issues.extend(issues)
            
            task_success = self._verify_task_success()
            if not task_success:
                self.test_issues.append(DetectedIssue(
                    issue_type=IssueType.VALIDATION_ERROR,
                    severity=IssueSeverity.WARNING,
                    title="任务解析可能失败",
                    description="任务步骤完成但未发现任何任务",
                    suggestions=["检查任务选择器", "验证页面结构"]
                ))
            
            await self._record_step("执行日常任务", task_success, step_start)
            
        except Exception as e:
            await self._record_step("执行日常任务", False, step_start, str(e))
            raise
    
    def _verify_task_success(self) -> bool:
        """验证任务是否成功"""
        if hasattr(self.app, 'state_monitor') and self.app.state_monitor:
            session_data = getattr(self.app.state_monitor, 'session_data', {})
            tasks_completed = session_data.get('tasks_completed', 0)
            tasks_failed = session_data.get('tasks_failed', 0)
            
            if tasks_completed > 0:
                logger.info(f"  ✓ 任务验证: 完成{tasks_completed}个, 失败{tasks_failed}个")
                return True
        return True
    
    async def _get_current_points(self) -> Optional[int]:
        """获取当前积分"""
        try:
            if hasattr(self.app, 'points_detector') and self.app.points_detector:
                points = await self.app.points_detector.get_current_points()
                return points
        except Exception as e:
            logger.debug(f"获取当前积分失败: {e}")
        return None
    
    async def _capture_issue_screenshots(
        self, 
        issues: List[DetectedIssue], 
        base_screenshot: Optional[str] = None
    ):
        """为检测到的问题截图 - 仅对严重问题截图，避免页面跳动"""
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        
        if critical_issues and self.app.page:
            try:
                screenshot_path = await self.screenshot_manager.capture(
                    self.app.page,
                    "critical_issues",
                    context=f"CRITICAL: {len(critical_issues)} critical issues detected"
                )
                if screenshot_path:
                    for issue in critical_issues:
                        issue.evidence = f"Screenshot: {screenshot_path}"
                    logger.warning(f"  📸 严重问题截图已保存")
            except Exception as e:
                logger.debug(f"截图失败: {e}")
        
        for issue in issues:
            if issue.severity != IssueSeverity.CRITICAL:
                issue.evidence = base_screenshot if base_screenshot else "See step screenshot"
    
    async def _step_generate_report(self):
        """步骤8: 生成报告"""
        step_start = time.time()
        logger.info("\n[8/8] 生成报告...")
        
        try:
            await self.app._generate_report()
            
            await self._record_step("生成报告", True, step_start)
            
        except Exception as e:
            await self._record_step("生成报告", False, step_start, str(e))
            raise
    
    async def _record_step(
        self, 
        name: str, 
        success: bool, 
        start_time: float,
        error: Optional[str] = None
    ):
        """记录测试步骤"""
        duration_ms = int((time.time() - start_time) * 1000)
        
        self.test_steps.append(TestStep(
            name=name,
            status="passed" if success else "failed",
            duration_ms=duration_ms,
            message=error
        ))
        
        if not success:
            logger.error(f"  ✗ 步骤失败: {name} - {error}")
        else:
            logger.info(f"  ✓ 步骤完成: {name} ({duration_ms}ms)")
    
    async def _cleanup(self):
        """清理资源"""
        try:
            if self.app:
                await self.app._cleanup()
            
            self.test_diagnoses = self.diagnostic_engine.diagnose(self.test_issues)
            
            logger.info("资源清理完成")
            
        except Exception as e:
            logger.warning(f"清理资源时出错: {e}")
    
    def generate_reports(self) -> Dict[str, str]:
        """生成报告"""
        json_report = self.reporter.generate_report()
        html_report = self.reporter.generate_html_report()
        text_report = self.reporter.generate_text_report()
        
        text_report_path = Path(self.reporter.output_dir) / f"test_report_{self.reporter.session_id}.txt"
        with open(text_report_path, 'w', encoding='utf-8') as f:
            f.write(text_report)
        logger.info(f"文本报告已生成: {text_report_path}")
        
        self.screenshot_manager.save_manifest()
        self.diagnostic_engine.save_diagnosis_report()
        
        self.reporter.print_summary()
        
        return {
            "json": json_report,
            "html": html_report,
            "text": str(text_report_path)
        }


async def run_integrated_test(config_path: str = "config.yaml") -> Dict[str, Any]:
    """运行集成测试"""
    runner = IntegratedTestRunner(config_path)
    return await runner.run_full_test()
