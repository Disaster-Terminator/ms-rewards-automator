# 任务文档：自主测试框架集成与验收流程重构

## 元数据

| 项目 | 值 |
|------|-----|
| 分支名 | `refactor/autonomous-test-integration` |
| 任务类型 | refactor |
| 优先级 | 高 |
| 预估工作量 | 中等 |
| 创建时间 | 2026-02-20 |

---

## 一、背景与目标

### 问题分析

当前测试框架存在以下问题：

| 问题 | 影响 | 严重程度 |
|------|------|----------|
| `--autonomous-test` 是独立参数 | Agent 不执行，需要单独运行 | 高 |
| `--dev`/`--user` 无诊断能力 | Agent 只能看日志，难以发现问题 | 高 |
| 诊断报告冗长 | Agent 不愿意阅读 | 中 |
| 测试流程不清晰 | Agent 不知道该执行什么 | 中 |

### 目标

1. **废弃无效参数**：移除 `--autonomous-test`、`--quick-test`
2. **集成诊断能力**：让 `--dev`/`--user` 自动具备诊断能力
3. **简化验收流程**：设计清晰的 4 阶段验收流程
4. **平衡效率与质量**：诊断是轻量级的，不拖慢开发

---

## 二、设计方案

### 2.1 核心原则

```
┌─────────────────────────────────────────────────────────────────┐
│  原则1：轻量级集成 - 诊断是可选的，不影响正常执行                │
│  原则2：智能采样 - 关键节点检查，不是每一步都检查                │
│  原则3：报告简洁 - 一页摘要，中文输出                            │
│  原则4：向后兼容 - 现有功能不受影响                             │
│  原则5：代码隔离 - 诊断代码移出 tests/，避免 pytest 误执行       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 关键决策

| 问题 | 决策 | 理由 |
|------|------|------|
| 诊断代码位置 | 移至 `src/diagnosis/` | 避免 pytest 执行自主框架，严重耽误时间 |
| 未登录处理 | 文件登录 → 用户登录 → 退出 | 没登录测了没意义 |
| 验收流程 | `--dev` + `--user` 都必须 | `--user` 验证拟人化行为 |
| 报告语言 | 中文 | 与备忘录一致 |
| 问题处理 | CRITICAL 中断，其他继续 | 严重问题不应继续执行 |
| 配置项 | 暂不需要 | 项目处于开发阶段 |
| 报告文件名 | 带时间戳 | 保留历史，方便对比 |
| 截图目录 | 统一到 `logs/diagnosis/` | 当前 `screenshots/`、`logs/diagnostics/`、`logs/screenshots/` 三处混乱 |

### 2.3 日志目录重构

**当前问题**：截图和诊断文件分散在 3 个位置

```
现状：
├── screenshots/                    # 根目录，1个文件
├── logs/
│   ├── diagnostics/               # HTML + PNG 混合
│   ├── screenshots/               # 按日期，命名混乱
│   └── test_reports/              # 测试报告
```

**目标结构**：

```
logs/
├── diagnosis/
│   ├── 20260220_153000/           # 按时间戳组织
│   │   ├── summary.txt            # 中文诊断摘要
│   │   ├── report.json            # 详细 JSON（可选）
│   │   └── screenshots/           # 截图
│   │       ├── login_check.png
│   │       ├── search_result.png
│   │       └── task_status.png
│   └── ...
├── test_reports/                  # 测试报告（保持不变）
├── daily_report.json              # 日常报告
├── health_report.json             # 健康报告
└── diagnosis_report.json          # 最新诊断（覆盖）
```

**清理任务**：

| 操作 | 说明 |
|------|------|
| 删除 `screenshots/` | 根目录截图，已废弃 |
| 清空 `logs/diagnostics/` | 旧诊断文件，不再使用 |
| 清空 `logs/screenshots/` | 旧截图，不再使用 |

**轮转机制**：

```python
# src/diagnosis/rotation.py
MAX_DIAGNOSIS_FOLDERS = 10  # 最多保留 10 次诊断记录

def cleanup_old_diagnoses(logs_dir: Path):
    """清理旧的诊断目录，保留最近的 N 个"""
    diagnosis_dir = logs_dir / "diagnosis"
    if not diagnosis_dir.exists():
        return
    
    folders = sorted(diagnosis_dir.iterdir(), reverse=True)
    for old_folder in folders[MAX_DIAGNOSIS_FOLDERS:]:
        shutil.rmtree(old_folder)
```

### 2.4 `@pytest.mark.real` 测试分析

**当前只有一个 real 测试**：

| 文件 | 测试内容 | 与诊断框架关系 |
|------|----------|----------------|
| `test_beforeunload_fix.py` | 测试 beforeunload 对话框修复 | **不重复**，保留 |

**结论**：`real` 测试是专门的功能测试，与诊断框架功能不同，保留不动。

### 2.3 架构变更

```
改造前：
main.py --dev → MSRewardsApp.run() → 日志输出
main.py --autonomous-test → AutonomousTestRunner → 诊断报告

改造后：
main.py --dev → MSRewardsApp.run(诊断模式) → 日志 + 诊断摘要
```

### 2.4 代码迁移

**从 `tests/autonomous/` 迁移到 `src/diagnosis/`**：

| 原位置 | 新位置 | 说明 |
|--------|--------|------|
| `tests/autonomous/diagnostic_engine.py` | `src/diagnosis/engine.py` | 核心诊断引擎 |
| `tests/autonomous/page_inspector.py` | `src/diagnosis/inspector.py` | 页面检查器 |
| `tests/autonomous/screenshot_manager.py` | `src/diagnosis/screenshot.py` | 截图管理 |
| - | `src/diagnosis/reporter.py` | 新增：报告生成器 |
| - | `src/diagnosis/__init__.py` | 新增：模块入口 |

**保留在 `tests/autonomous/`**：

| 文件 | 说明 |
|------|------|
| `autonomous_test_runner.py` | 完整测试运行器（独立使用） |
| `integrated_test_runner.py` | 集成测试运行器 |
| `smart_scenarios.py` | 测试场景定义 |
| `reporter.py` | 测试报告（与诊断报告不同） |

**pytest 配置更新**：

```ini
# pytest.ini 添加排除规则
[pytest]
testpaths = tests/unit tests/integration
# 不再扫描 tests/autonomous
```

### 2.3 参数变更

| 参数 | 改造前 | 改造后 |
|------|--------|--------|
| `--autonomous-test` | 独立运行测试框架 | **移除** |
| `--quick-test` | 缩短检查间隔 | **移除** |
| `--test-type` | 指定测试类型 | **移除** |
| `--diagnose` | 不存在 | **新增**，可选启用诊断 |
| `--dev` | 快速开发模式 | 快速开发模式 + 默认启用诊断 |
| `--user` | 用户模式 | 用户模式 + 默认启用诊断 |

### 2.4 诊断检查点

只在关键节点进行检查，不影响执行效率：

| 检查点 | 检查内容 | 耗时 |
|--------|----------|------|
| 登录后 | 登录状态、Cookie 有效性 | ~1s |
| 搜索后 | 搜索结果页、积分变化 | ~1s |
| 任务后 | 任务完成状态、页面错误 | ~1s |
| 结束时 | 汇总诊断、生成报告 | ~2s |

**总诊断开销**：约 5-10 秒，相对于完整运行时间可忽略。

### 2.5 诊断报告格式

生成简洁的摘要报告，而非冗长的 JSON：

```
═══════════════════════════════════════════════════════════════
                    诊断摘要 (2026-02-20 15:30:00)
═══════════════════════════════════════════════════════════════

执行概况：
  • 桌面搜索：30/30 ✓
  • 移动搜索：20/20 ✓
  • 每日任务：5/6 ✓

发现问题：
  ⚠️ [选择器] 积分选择器可能过时 (置信度: 0.8)
     → 建议：检查 points_detector.py 中的选择器
  
  ℹ️ [网络] 响应时间较慢 (置信度: 0.6)
     → 建议：检查网络连接

诊断报告已保存：logs/diagnosis_summary.txt

═══════════════════════════════════════════════════════════════
```

---

## 三、代码修改清单

### 3.1 main.py 修改

**移除的参数**（约 20 行）：

```python
# 移除以下参数定义
--autonomous-test
--quick-test
--test-type
```

**新增的参数**：

```python
parser.add_argument(
    "--diagnose",
    action="store_true",
    default=None,  # None 表示由 dev/user 模式决定
    help="启用诊断模式（--dev/--user 默认启用）",
)
```

**修改的逻辑**：

```python
# 移除 run_autonomous_test 分支
if args.autonomous_test:
    return await run_autonomous_test(args)  # 删除此分支

# 在 MSRewardsApp 调用时传递诊断配置
diagnose_enabled = args.diagnose or (args.dev or args.user)
app = MSRewardsApp(config, args, diagnose=diagnose_enabled)
```

### 3.2 DiagnosticEngine 新增方法

在 `tests/autonomous/diagnostic_engine.py` 中新增：

```python
class DiagnosticEngine:
    # ... 现有代码 ...
    
    def quick_check(self, page, check_type: str) -> QuickDiagnosis:
        """
        快速诊断检查
        
        Args:
            page: Playwright 页面对象
            check_type: 检查类型 (login/search/task/summary)
        
        Returns:
            QuickDiagnosis: 简化的诊断结果
        """
        pass
    
    def generate_summary_report(self) -> str:
        """
        生成简洁的摘要报告
        
        Returns:
            格式化的摘要文本
        """
        pass
```

### 3.3 MSRewardsApp 修改

在 `src/infrastructure/ms_rewards_app.py` 中：

```python
class MSRewardsApp:
    def __init__(self, config, args, diagnose: bool = False):
        # ... 现有初始化 ...
        self.diagnose = diagnose
        if diagnose:
            from tests.autonomous.diagnostic_engine import DiagnosticEngine
            self.diagnostic_engine = DiagnosticEngine()
    
    async def run(self):
        """主运行方法"""
        try:
            # ... 现有逻辑 ...
            
            # 关键节点诊断
            if self.diagnose:
                await self._diagnose_checkpoint("login")
            
            # 搜索逻辑
            if self.diagnose:
                await self._diagnose_checkpoint("search")
            
            # 任务逻辑
            if self.diagnose:
                await self._diagnose_checkpoint("task")
            
        finally:
            # 生成诊断摘要
            if self.diagnose:
                self._print_diagnosis_summary()
```

### 3.4 新增文件

**`tests/autonomous/quick_diagnosis.py`**：

轻量级诊断模块，提供：

- `QuickDiagnosis` 数据类
- `quick_check_page()` 函数
- `format_summary()` 函数

---

## 四、验收流程重构

### 4.1 新的 4 阶段验收流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 1：代码质量（必须）                       │
├─────────────────────────────────────────────────────────────────┤
│  ruff check .              → Lint 检查                          │
│  ruff format . --check     → 格式检查                           │
│  耗时：~10s                                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 2：自动化测试（必须）                     │
├─────────────────────────────────────────────────────────────────┤
│  pytest tests/ -v -m "not slow and not real"                    │
│  注意：这是 Mock 测试，只能排查浅层问题                           │
│  耗时：~30s                                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 3：实战测试（必须）                       │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: python main.py --dev                                  │
│          → 快速验证核心逻辑 + 诊断                              │
│          → 阅读诊断摘要，确认无严重问题                          │
│                                                                 │
│  Step 2: python main.py --user                                 │
│          → 验证拟人化行为 + 防检测逻辑                           │
│          → 阅读诊断摘要，确认无严重问题                          │
│                                                                 │
│  耗时：~5-10min                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 4：交付确认                               │
├─────────────────────────────────────────────────────────────────┤
│  向用户展示改动摘要                                              │
│  等待用户确认"本地审查通过"                                      │
└─────────────────────────────────────────────────────────────────┘
```

**为什么 `--user` 必须执行**：

| `--dev` 无法发现的问题 | `--user` 能发现 |
|------------------------|-----------------|
| 拟人化鼠标移动 bug | ✅ |
| 拟人化打字模拟 bug | ✅ |
| 防检测模块问题 | ✅ |
| 长时间运行稳定性 | ✅ |
| 拟人化等待时间问题 | ✅ |

### 4.2 DoD 模板更新

```markdown
## DoD (Definition of Done)

### 第一阶段：代码质量 ✓
- [ ] `ruff check .` 通过
- [ ] `ruff format . --check` 通过

### 第二阶段：自动化测试 ✓
- [ ] `pytest tests/ -v -m "not slow and not real"` 通过
- [ ] ⚠️ 注意：自动化测试是 Mock，只能排查浅层问题

### 第三阶段：实战测试 + 诊断 ✓
- [ ] `python main.py --dev` 无报错
- [ ] 阅读诊断摘要，确认无严重问题
- [ ] `python main.py --user` 无报错
- [ ] 阅读诊断摘要，确认无严重问题
- [ ] 如发现问题，修复后重新执行

### 第四阶段：交付确认
- [ ] 向用户展示改动摘要
- [ ] 等待用户确认"本地审查通过"
```

---

## 五、测试计划

### 5.1 单元测试

| 测试文件 | 测试内容 |
|----------|----------|
| `test_diagnostic_engine.py` | 新增的 `quick_check()` 方法 |
| `test_main_args.py` | 参数解析逻辑 |

### 5.2 集成测试

| 测试场景 | 验证点 |
|----------|--------|
| `--dev` 默认启用诊断 | 诊断报告生成 |
| `--diagnose=false` 禁用诊断 | 无诊断输出 |
| 诊断检查点触发 | 各检查点正确执行 |

### 5.3 手动验证

```bash
# 1. 验证参数移除
python main.py --help | grep -v "autonomous-test"

# 2. 验证诊断启用
python main.py --dev 2>&1 | grep "诊断摘要"

# 3. 验证诊断禁用
python main.py --dev --diagnose=false 2>&1 | grep -v "诊断摘要"
```

---

## 六、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 诊断增加执行时间 | 低 | 只在关键节点检查，总开销 <10s |
| 诊断误报 | 中 | 提供置信度，低置信度问题标记为 ℹ️ |
| 向后兼容性 | 低 | `--diagnose` 默认值由模式决定 |

---

## 七、执行步骤

### Step 1：创建分支

```bash
git branch refactor/autonomous-test-integration main
git worktree add ../MS-Rewards-Automator-test refactor/autonomous-test-integration
```

### Step 2：代码迁移

- 创建 `src/diagnosis/` 目录
- 迁移 `diagnostic_engine.py` → `engine.py`
- 迁移 `page_inspector.py` → `inspector.py`
- 迁移 `screenshot_manager.py` → `screenshot.py`
- 新建 `reporter.py`（中文报告生成）
- 新建 `__init__.py`

### Step 3：更新 pytest 配置

- 修改 `pytest.ini`，排除 `tests/autonomous`

### Step 4：修改 main.py

- 移除 `--autonomous-test`、`--quick-test`、`--test-type` 参数
- 新增 `--diagnose` 参数
- 移除 `run_autonomous_test()` 函数

### Step 5：修改 MSRewardsApp

- 添加诊断配置参数
- 实现登录检查逻辑（文件登录 → 用户登录 → 退出）
- 在关键节点调用诊断
- 结束时打印诊断摘要

### Step 6：更新文档

- 更新 `docs/plans/REWARDS_V2_ADAPTATION.md`
- 更新 `docs/reference/BRANCH_GUIDE.md`

### Step 7：测试验证

- 运行单元测试
- 运行 `--dev` 验证诊断输出
- 运行 `--user` 验证诊断输出

---

## 八、DoD (Definition of Done)

### 第一阶段：代码质量

- [x] `ruff check .` 通过
- [x] `ruff format . --check` 通过

### 第二阶段：自动化测试

- [x] `pytest tests/ -v -m "not slow and not real"` 通过
- [x] 新增代码有对应测试覆盖

### 第三阶段：实战测试 + 诊断

- [ ] `python main.py --dev` 无报错
- [ ] 诊断摘要正确显示
- [ ] `python main.py --user` 无报错
- [ ] `--diagnose=false` 正确禁用诊断

### 第四阶段：交付确认

- [x] 向用户展示改动摘要
- [ ] 等待用户确认"本地审查通过"
