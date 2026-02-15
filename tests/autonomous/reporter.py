"""
测试报告生成器
生成结构化的测试报告，包含截图、诊断结果和建议
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

from .page_inspector import DetectedIssue, IssueSeverity
from .diagnostic_engine import DiagnosisResult

logger = logging.getLogger(__name__)


@dataclass
class TestStep:
    """测试步骤"""
    name: str
    status: str  # "passed", "failed", "skipped"
    duration_ms: int
    message: Optional[str] = None
    screenshot: Optional[str] = None
    issues: List[DetectedIssue] = field(default_factory=list)


@dataclass 
class TestResult:
    """测试结果"""
    name: str
    status: str  # "passed", "failed", "error"
    start_time: str
    end_time: str
    duration_ms: int
    steps: List[TestStep] = field(default_factory=list)
    issues: List[DetectedIssue] = field(default_factory=list)
    diagnoses: List[DiagnosisResult] = field(default_factory=list)
    points_tracking: Dict[str, Any] = field(default_factory=dict)


class TestReporter:
    """测试报告生成器"""
    
    def __init__(self, output_dir: str = "logs/test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_results: List[TestResult] = []
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")
        
        self.screenshots: List[Dict[str, Any]] = []
        self.summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "points_gained": 0
        }
        
        logger.info(f"测试报告生成器初始化: {self.output_dir}")
    
    def start_test(self, name: str) -> str:
        """开始测试"""
        return datetime.now().isoformat()
    
    def end_test(
        self,
        name: str,
        status: str,
        start_time: str,
        steps: List[TestStep],
        issues: List[DetectedIssue] = None,
        diagnoses: List[DiagnosisResult] = None,
        points_tracking: Dict[str, Any] = None
    ):
        """结束测试"""
        end_time = datetime.now()
        start_dt = datetime.fromisoformat(start_time)
        duration_ms = int((end_time - start_dt).total_seconds() * 1000)
        
        result = TestResult(
            name=name,
            status=status,
            start_time=start_time,
            end_time=end_time.isoformat(),
            duration_ms=duration_ms,
            steps=steps,
            issues=issues or [],
            diagnoses=diagnoses or [],
            points_tracking=points_tracking or {}
        )
        
        self.test_results.append(result)
        self._update_summary(status)
        
        if points_tracking and points_tracking.get("gained"):
            self.summary["points_gained"] = points_tracking["gained"]
    
    def _update_summary(self, status: str):
        """更新摘要"""
        self.summary["total_tests"] += 1
        if status in self.summary:
            self.summary[status] += 1
    
    def add_screenshot(self, screenshot_info: Dict[str, Any]):
        """添加截图信息"""
        self.screenshots.append(screenshot_info)
    
    def generate_report(self) -> str:
        """生成报告"""
        report_path = self.output_dir / f"test_report_{self.session_id}.json"
        
        report = {
            "meta": {
                "session_id": self.session_id,
                "generated_at": datetime.now().isoformat(),
                "report_version": "1.0"
            },
            "summary": self.summary,
            "tests": [self._test_result_to_dict(t) for t in self.test_results],
            "screenshots": self.screenshots,
            "recommendations": self._generate_recommendations()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试报告已生成: {report_path}")
        return str(report_path)
    
    def _test_result_to_dict(self, result: TestResult) -> Dict[str, Any]:
        """转换测试结果为字典"""
        result_dict = {
            "name": result.name,
            "status": result.status,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "duration_ms": result.duration_ms,
            "duration_formatted": self._format_duration(result.duration_ms),
            "steps": [
                {
                    "name": s.name,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "message": s.message,
                    "screenshot": s.screenshot,
                    "issues_count": len(s.issues)
                }
                for s in result.steps
            ],
            "issues": [
                {
                    "type": i.issue_type.value,
                    "severity": i.severity.value,
                    "title": i.title,
                    "description": i.description,
                    "url": i.url,
                    "evidence": i.evidence,
                    "suggestions": i.suggestions
                }
                for i in result.issues
            ],
            "diagnoses": [
                {
                    "category": d.category.value,
                    "root_cause": d.root_cause,
                    "confidence": d.confidence,
                    "description": d.description,
                    "solutions_count": len(d.solutions)
                }
                for d in result.diagnoses
            ]
        }
        
        if result.points_tracking:
            result_dict["points_tracking"] = {
                "initial": result.points_tracking.get("initial"),
                "final": result.points_tracking.get("final"),
                "gained": result.points_tracking.get("gained", 0),
                "history": result.points_tracking.get("history", [])
            }
        
        return result_dict
    
    def _format_duration(self, duration_ms: int) -> str:
        """格式化持续时间"""
        seconds = duration_ms / 1000
        if seconds < 60:
            return f"{seconds:.2f}s"
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """生成建议"""
        recommendations = []
        
        failed_tests = [t for t in self.test_results if t.status == "failed"]
        if failed_tests:
            recommendations.append({
                "priority": "high",
                "category": "test_failures",
                "message": f"有 {len(failed_tests)} 个测试失败",
                "details": [t.name for t in failed_tests],
                "action": "检查失败测试的详细日志和截图"
            })
        
        critical_issues = []
        for result in self.test_results:
            for issue in result.issues:
                if issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.ERROR]:
                    critical_issues.append(issue)
        
        if critical_issues:
            recommendations.append({
                "priority": "critical",
                "category": "critical_issues",
                "message": f"发现 {len(critical_issues)} 个严重问题",
                "details": list(set(i.title for i in critical_issues)),
                "action": "立即处理严重问题"
            })
        
        all_diagnoses = []
        for result in self.test_results:
            all_diagnoses.extend(result.diagnoses)
        
        auto_fixable = []
        for diagnosis in all_diagnoses:
            for solution in diagnosis.solutions:
                if solution.get("auto_fixable") and solution.get("applicable"):
                    auto_fixable.append({
                        "diagnosis": diagnosis.root_cause,
                        "solution": solution["description"]
                    })
        
        if auto_fixable:
            recommendations.append({
                "priority": "medium",
                "category": "auto_fixable",
                "message": f"有 {len(auto_fixable)} 个问题可自动修复",
                "details": auto_fixable[:5],
                "action": "考虑应用自动修复方案"
            })
        
        return recommendations
    
    def generate_html_report(self) -> str:
        """生成HTML报告"""
        html_path = self.output_dir / f"test_report_{self.session_id}.html"
        
        html_content = self._build_html()
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML报告已生成: {html_path}")
        return str(html_path)
    
    def _build_html(self) -> str:
        """构建HTML内容"""
        summary = self.summary
        results = self.test_results
        
        status_colors = {
            "passed": "#28a745",
            "failed": "#dc3545",
            "error": "#fd7e14",
            "skipped": "#6c757d"
        }
        
        severity_colors = {
            "critical": "#dc3545",
            "error": "#fd7e14",
            "warning": "#ffc107",
            "info": "#17a2b8"
        }
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - {self.session_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .summary-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .summary-card .number {{ font-size: 32px; font-weight: bold; margin-bottom: 5px; }}
        .summary-card .label {{ font-size: 14px; color: #666; }}
        .test-section {{ background: white; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }}
        .test-header {{ padding: 15px 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
        .test-header h3 {{ font-size: 16px; }}
        .test-status {{ padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; }}
        .test-content {{ padding: 20px; }}
        .step {{ padding: 10px; margin-bottom: 10px; background: #f8f9fa; border-radius: 5px; display: flex; justify-content: space-between; }}
        .step-name {{ font-weight: 500; }}
        .step-status {{ font-size: 12px; padding: 2px 10px; border-radius: 10px; }}
        .issue {{ padding: 15px; margin-bottom: 10px; border-radius: 5px; border-left: 4px solid; }}
        .issue-critical {{ background: #fff5f5; border-color: #dc3545; }}
        .issue-error {{ background: #fff8f0; border-color: #fd7e14; }}
        .issue-warning {{ background: #fffdf0; border-color: #ffc107; }}
        .issue-info {{ background: #f0faff; border-color: #17a2b8; }}
        .diagnosis {{ padding: 15px; background: #f8f9fa; border-radius: 5px; margin-bottom: 10px; }}
        .diagnosis-header {{ font-weight: bold; margin-bottom: 10px; }}
        .solution {{ padding: 10px; background: white; border-radius: 5px; margin-top: 10px; }}
        .recommendations {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .recommendation {{ padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
        .recommendation-high {{ background: #fff5f5; border-left: 4px solid #dc3545; }}
        .recommendation-medium {{ background: #fffdf0; border-left: 4px solid #ffc107; }}
        .recommendation-critical {{ background: #ffe6e6; border-left: 4px solid #721c24; }}
        .screenshot {{ max-width: 100%; border-radius: 5px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .no-issues {{ color: #28a745; padding: 20px; text-align: center; }}
        .points-tracking {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .points-tracking h3 {{ margin-bottom: 15px; }}
        .points-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; text-align: center; }}
        .points-item .value {{ font-size: 28px; font-weight: bold; }}
        .points-item .label {{ font-size: 12px; opacity: 0.9; }}
        .points-positive {{ color: #90EE90; }}
        .points-negative {{ color: #FFB6C1; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 自主测试报告</h1>
            <div class="meta">
                会话ID: {self.session_id} | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="number">{summary['total_tests']}</div>
                <div class="label">总测试数</div>
            </div>
            <div class="summary-card">
                <div class="number" style="color: #28a745;">{summary['passed']}</div>
                <div class="label">通过</div>
            </div>
            <div class="summary-card">
                <div class="number" style="color: #dc3545;">{summary['failed']}</div>
                <div class="label">失败</div>
            </div>
            <div class="summary-card">
                <div class="number" style="color: #fd7e14;">{summary['errors']}</div>
                <div class="label">错误</div>
            </div>
        </div>
"""
        
        for result in results:
            status_color = status_colors.get(result.status, "#6c757d")
            
            html += f"""
        <div class="test-section">
            <div class="test-header">
                <h3>{result.name}</h3>
                <span class="test-status" style="background: {status_color};">{result.status.upper()}</span>
            </div>
            <div class="test-content">
                <p><strong>持续时间:</strong> {self._format_duration(result.duration_ms)}</p>
"""
            
            if result.points_tracking and result.points_tracking.get("initial") is not None:
                pts = result.points_tracking
                gained = pts.get("gained", 0)
                gained_class = "points-positive" if gained >= 0 else "points-negative"
                gained_sign = "+" if gained >= 0 else ""
                html += f"""
                <div class="points-tracking">
                    <h3>📊 积分追踪</h3>
                    <div class="points-grid">
                        <div class="points-item">
                            <div class="value">{pts.get('initial', 'N/A')}</div>
                            <div class="label">初始积分</div>
                        </div>
                        <div class="points-item">
                            <div class="value">{pts.get('final', 'N/A')}</div>
                            <div class="label">最终积分</div>
                        </div>
                        <div class="points-item">
                            <div class="value {gained_class}">{gained_sign}{gained}</div>
                            <div class="label">积分变化</div>
                        </div>
                    </div>
                </div>
"""
            
            if result.steps:
                html += "<h4 style='margin: 15px 0 10px;'>测试步骤</h4>"
                for step in result.steps:
                    step_color = status_colors.get(step.status, "#6c757d")
                    html += f"""
                <div class="step">
                    <span class="step-name">{step.name}</span>
                    <span class="step-status" style="background: {step_color}; color: white;">{step.status}</span>
                </div>
"""
            
            if result.issues:
                html += "<h4 style='margin: 15px 0 10px;'>发现问题</h4>"
                for issue in result.issues:
                    severity_class = f"issue-{issue.severity.value}"
                    html += f"""
                <div class="issue {severity_class}">
                    <strong>[{issue.severity.value.upper()}] {issue.title}</strong>
                    <p>{issue.description}</p>
                    {"<p><small>建议: " + ", ".join(issue.suggestions[:2]) + "</small></p>" if issue.suggestions else ""}
                </div>
"""
            
            if result.diagnoses:
                html += "<h4 style='margin: 15px 0 10px;'>诊断结果</h4>"
                for diag in result.diagnoses:
                    html += f"""
                <div class="diagnosis">
                    <div class="diagnosis-header">🔍 {diag.root_cause}</div>
                    <p>{diag.description}</p>
                    <p><small>置信度: {diag.confidence*100:.0f}%</small></p>
                </div>
"""
            
            if not result.issues and not result.diagnoses:
                html += '<div class="no-issues">✅ 无问题发现</div>'
            
            html += """
            </div>
        </div>
"""
        
        recommendations = self._generate_recommendations()
        if recommendations:
            html += """
        <div class="recommendations">
            <h3 style="margin-bottom: 20px;">📋 建议操作</h3>
"""
            for rec in recommendations:
                priority_class = f"recommendation-{rec['priority']}"
                html += f"""
            <div class="recommendation {priority_class}">
                <strong>{rec['message']}</strong>
                <p style="margin-top: 5px; color: #666;">{rec['action']}</p>
            </div>
"""
            html += """
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        return html
    
    def print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 70)
        print("测试报告摘要")
        print("=" * 70)
        print(f"会话ID: {self.session_id}")
        print(f"总测试数: {self.summary['total_tests']}")
        print(f"  ✅ 通过: {self.summary['passed']}")
        print(f"  ❌ 失败: {self.summary['failed']}")
        print(f"  ⚠️  错误: {self.summary['errors']}")
        print(f"  ⏭️  跳过: {self.summary['skipped']}")
        
        if self.summary.get('points_gained', 0) != 0:
            points = self.summary['points_gained']
            sign = "+" if points >= 0 else ""
            print(f"\n📊 积分变化: {sign}{points}")
        
        total_issues = sum(len(t.issues) for t in self.test_results)
        critical_issues = sum(
            1 for t in self.test_results 
            for i in t.issues 
            if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.ERROR]
        )
        
        print(f"\n发现问题: {total_issues} 个")
        print(f"  🔴 严重: {critical_issues} 个")
        
        print("=" * 70)
    
    def generate_text_report(self) -> str:
        """生成纯文本报告"""
        lines = []
        lines.append("=" * 70)
        lines.append("MS Rewards Automator - 自主测试报告")
        lines.append("=" * 70)
        lines.append(f"会话ID: {self.session_id}")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        lines.append("-" * 70)
        lines.append("测试摘要")
        lines.append("-" * 70)
        lines.append(f"总测试数: {self.summary['total_tests']}")
        lines.append(f"  通过: {self.summary['passed']}")
        lines.append(f"  失败: {self.summary['failed']}")
        lines.append(f"  错误: {self.summary['errors']}")
        lines.append(f"  跳过: {self.summary['skipped']}")
        
        if self.summary.get('points_gained', 0) != 0:
            points = self.summary['points_gained']
            sign = "+" if points >= 0 else ""
            lines.append(f"\n积分变化: {sign}{points}")
        lines.append("")
        
        for result in self.test_results:
            lines.append("-" * 70)
            lines.append(f"测试: {result.name}")
            lines.append(f"状态: {result.status.upper()}")
            lines.append(f"持续时间: {self._format_duration(result.duration_ms)}")
            lines.append("")
            
            if result.points_tracking and result.points_tracking.get("initial") is not None:
                pts = result.points_tracking
                gained = pts.get("gained", 0)
                sign = "+" if gained >= 0 else ""
                lines.append(f"[积分追踪]")
                lines.append(f"  初始积分: {pts.get('initial', 'N/A')}")
                lines.append(f"  最终积分: {pts.get('final', 'N/A')}")
                lines.append(f"  积分变化: {sign}{gained}")
                lines.append("")
            
            if result.steps:
                lines.append("[测试步骤]")
                for step in result.steps:
                    status_icon = "[OK]" if step.status == "passed" else "[FAIL]"
                    lines.append(f"  {status_icon} {step.name} ({self._format_duration(step.duration_ms)})")
                lines.append("")
            
            if result.issues:
                lines.append("[发现问题]")
                for issue in result.issues:
                    sev = issue.severity.value.upper()
                    lines.append(f"  [{sev}] {issue.title}")
                    lines.append(f"      {issue.description}")
                    if issue.evidence:
                        lines.append(f"      证据: {issue.evidence}")
                    if issue.suggestions:
                        lines.append(f"      建议: {', '.join(issue.suggestions[:2])}")
                lines.append("")
            
            if result.diagnoses:
                lines.append("[诊断结果]")
                for diag in result.diagnoses:
                    lines.append(f"  根因: {diag.root_cause}")
                    lines.append(f"      {diag.description}")
                    lines.append(f"      置信度: {diag.confidence*100:.0f}%")
                lines.append("")
        
        recommendations = self._generate_recommendations()
        if recommendations:
            lines.append("-" * 70)
            lines.append("建议操作")
            lines.append("-" * 70)
            for rec in recommendations:
                lines.append(f"[{rec['priority'].upper()}] {rec['message']}")
                lines.append(f"    {rec['action']}")
            lines.append("")
        
        lines.append("=" * 70)
        lines.append("报告结束")
        lines.append("=" * 70)
        
        return "\n".join(lines)
