# 健康监控增强功能开发报告

## 开发概述

**开发分支**: `feature/health-monitor-enhanced`
**开发日期**: 2026-02-15
**开发者**: AI Assistant

## 功能增强

### 1. 浏览器健康检查

新增 `_check_browser_health()` 方法，实现以下功能：

- 检测浏览器连接状态
- 监控浏览器内存使用（通过 psutil）
- 统计打开的页面数量
- 返回结构化的健康状态报告

### 2. 浏览器实例注册

新增 `register_browser()` 方法：

- 允许外部注册浏览器实例到健康监控器
- 支持注册 Browser 和 BrowserContext
- 自动开始监控浏览器健康状态

### 3. 实时状态报告

新增 `get_detailed_status()` 方法：

- 返回完整的系统状态快照
- 包含所有监控指标的当前值
- 适用于实时监控面板集成

### 4. 异步任务清理改进

改进 `stop_monitoring()` 方法：

- 添加 5 秒超时等待
- 使用 `asyncio.wait_for()` 防止无限等待
- 添加 `finally` 块确保任务清理

### 5. 新增监控指标

| 指标名 | 类型 | 说明 |
|--------|------|------|
| `browser_memory_mb` | float | 浏览器内存使用量（MB） |
| `browser_page_count` | int | 打开的页面数量 |

### 6. 进度跟踪系统优化（新增）

新增 `ProgressTracker` 类，实现阶段化进度跟踪：

**阶段定义**:

| 阶段 | 名称 | 权重 |
|------|------|------|
| `init` | 初始化 | 5% |
| `login` | 登录 | 10% |
| `desktop_search` | 桌面搜索 | 40% |
| `mobile_search` | 移动搜索 | 35% |
| `daily_tasks` | 日常任务 | 10% |

**智能时间估算**:

- 基于历史阶段耗时估算
- 基于实际搜索速度估算
- 显示下一阶段名称

**改进的显示**:

```
📋 当前阶段: 桌面搜索
   操作: 执行搜索...
📊 总体进度: [████████░░░░░░░░░░░░] 42.5%
🖥️  桌面搜索: [██████████░░░░░░░░░] 15/30
⏱️  运行时间: 2分30秒
⏳ 预计剩余: 3分15秒 (下一阶段: 移动搜索)
```

## 代码修改清单

### 核心文件

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `src/infrastructure/health_monitor.py` | 增强 | 主要功能增强 |
| `src/ui/real_time_status.py` | 增强 | 新增 ProgressTracker 类 |
| `src/infrastructure/task_coordinator.py` | 改进 | 使用阶段化进度跟踪 |
| `src/infrastructure/self_diagnosis.py` | 修复 | 异常链处理 |
| `src/login/login_state_machine.py` | 修复 | 闭包变量绑定 |
| `src/login/state_handler.py` | 修复 | TYPE_CHECKING 导入 |
| `tests/conftest.py` | 修复 | 排除非测试文件 |

### 新增类和方法

```python
# real_time_status.py - 新增 ProgressTracker 类

class ProgressTracker:
    STAGES = {
        "init": {"name": "初始化", "weight": 0.05},
        "login": {"name": "登录", "weight": 0.10},
        "desktop_search": {"name": "桌面搜索", "weight": 0.40},
        "mobile_search": {"name": "移动搜索", "weight": 0.35},
        "daily_tasks": {"name": "日常任务", "weight": 0.10},
    }
    
    def start_stage(self, stage: str) -> None
    def complete_stage(self, stage: str) -> None
    def update_stage_progress(self, stage: str, progress: float) -> None
    def get_overall_progress(self) -> float
    def estimate_remaining_time(self) -> Optional[float]
    def record_search_time(self, search_time: float) -> None

# RealTimeStatusDisplay 新增方法

def start_stage(self, stage: str)
def complete_stage(self, stage: str)
def update_stage_progress(self, stage: str, progress: float)
def record_search_time(self, search_time: float)

# StatusManager 新增类方法

@classmethod
def start_stage(cls, stage: str)
@classmethod
def complete_stage(cls, stage: str)
@classmethod
def update_stage_progress(cls, stage: str, progress: float)
@classmethod
def record_search_time(cls, search_time: float)
```

### 改进方法

```python
# health_monitor.py

async def stop_monitoring(self):
    """改进：添加超时和 finally 清理"""

def _calculate_overall_health(self) -> str:
    """改进：排除 unknown 状态"""

def get_health_summary(self) -> Dict[str, Any]:
    """改进：包含浏览器指标"""

# task_coordinator.py

async def handle_login(self, page, context):
    """改进：使用 StatusManager.start_stage/complete_stage"""

async def execute_desktop_search(self, page):
    """改进：使用阶段化进度跟踪"""

async def execute_mobile_search(self, page):
    """改进：使用阶段化进度跟踪"""

async def execute_daily_tasks(self, page):
    """改进：使用阶段化进度跟踪"""
```

## 验收测试结果

### 阶段1: 静态检查 ✅

```bash
python -m ruff check src/
# 无错误
```

### 阶段2: 单元测试 ✅

```bash
pytest tests/unit/ -m "not real" -v
# 30 passed
```

### 阶段3: 集成测试 ✅

```bash
pytest tests/integration/ -v
# 8 passed
```

### 阶段4: Dev快速验证 ✅

```bash
python main.py --dev --headless
# 退出码: 0
```

### 阶段5: 自动化诊断测试 ✅

```bash
python tests/autonomous/run_autonomous_tests.py --user-mode --headless
# 结果: 4/4 测试通过
# 问题: 0 个
# 严重问题: 0 个
```

### 阶段6: 有头验收 ⏳

待开发者手动验收。

## 技术细节

### 浏览器健康检查逻辑

```
浏览器状态判断:
├── 未注册浏览器 → "unknown" (不影响总体评估)
├── 连接正常 + 内存正常 + 页面数正常 → "healthy"
├── 连接正常 + 内存/页面数异常 → "warning"
└── 连接失败 → "error"
```

### 进度估算算法

```
estimate_remaining_time():
1. 获取剩余阶段列表
2. 对于每个剩余阶段:
   - 如果有历史耗时数据 → 使用平均值
   - 如果是搜索阶段 → 使用实际搜索速度估算
   - 否则 → 使用默认估算值
3. 考虑当前阶段进度，计算剩余部分
4. 返回总剩余时间
```

### 异步任务清理流程

```
stop_monitoring():
1. 检查任务是否存在且未完成
2. 取消任务 (task.cancel())
3. 等待任务结束 (asyncio.wait_for 5秒超时)
4. 捕获 CancelledError 和 TimeoutError
5. finally 块清理任务引用
```

## 已知问题

1. **测试清理警告**: 测试结束时可能出现异步资源清理警告，不影响功能
2. **浏览器进程检测**: 依赖 psutil，在某些环境下可能需要额外权限

## 后续建议

1. **集成到主应用**: 在 `MSRewardsApp` 中调用 `register_browser()` 注册浏览器实例
2. **监控面板**: 可使用 `get_detailed_status()` 构建实时监控 UI
3. **告警阈值**: 可配置内存和页面数的告警阈值
4. **搜索耗时记录**: 在 SearchEngine 中调用 `record_search_time()` 提高估算精度

## 文件变更统计

- 新增代码行数: ~300
- 修改代码行数: ~80
- 修复问题数: 5
- 测试通过率: 100%

---

**报告生成时间**: 2026-02-15
**验收状态**: 阶段1-5通过，待阶段6人工验收
