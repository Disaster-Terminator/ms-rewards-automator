# ROADMAP

**Project:** RewardsCore Technical Debt Reduction
**Branch:** refactor/test-cleanup
**Created:** 2026-03-21

---

## Overview

这是一个**5 阶段的渐进式简化项目**。每个阶段独立交付、可验证，可以随时停止而不破坏项目。总目标：源码减少 10%-20%，质量指标改善。

**阶段策略：**
- **Phase 1:** 建立基线，冻结兼容边界（规划阶段，不执行代码变更）
- **Phase 2:** 低风险删除（死代码、注释代码、冗余文件）
- **Phase 3:** 核心模块收缩（拆分支离复杂实现）
- **Phase 4:** 异常治理（修复静默异常、规范返回值）
- **Phase 5:** 测试补锁 + 依赖清理（补充测试、移除未用依赖）

---

## Milestone: V1.0 - Technical Debt Reduction Complete

**Goal:** 降低技术债至可维护水平，代码量减少 10-20%，核心功能无回退

**Success Criteria:**
- ✅ 源码行数从 ~8,600 降至 6,880–7,740 之间
- ✅ 所有 core 功能测试通过（保持基线）
- ✅ 静默异常从 100+ 处降至 <20 处
- ✅ 高风险模块（登录、任务、积分）有基本回归测试
- ✅ 主路径配置 100% 向后兼容

---

## Phase 1: 冻结兼容边界与调用图

**Phase Number:** 1
**Phase Name:** 兼容边界冻结与调用图基线
**Duration:** Planning only (no code changes)
**Goal:** 建立变更边界和调用关系图，确保后续删除不会误伤

**Plans:** 1 plan

**Plans:**
- [ ] 01-01-PLAN.md — 基线调查（调用图、配置边界、性能基准、测试基线）

### REQ Mapping

- REQ-010 (配置兼容性) - **Core**
- REQ-011 (性能基准) - **Core**

### Deliverables

**1.1 调用图生成**
- 工具：使用 `pyan3` 或 `snakeviz` 生成调用关系
- 输出：`.planning/codebase/CALL_GRAPH.md` 或可视化图表
- 内容：
  - 核心入口（`cli.py` → `MSRewardsApp.run()`）
  - 所有子系统的导入关系
  - 标记未知引用（动态导入、插件）
- 验收：调用图覆盖 95%+ 代码，主要孤立节点清晰

**1.2 配置边界定义**
- 分析 `config.example.yaml` 和 `ConfigManager`
- 标记为 **REQUIRED**（必须保留） vs **OPTIONAL**（可废弃）
- 输出：`.planning/config_boundary.md`
- 规则：
  - 所有现有配置键默认 `REQUIRED`（除非证据证明无用）
  - 废弃配置需提供迁移路径和警告

**1.3 性能基准测试**
- 基准环境：`--dev` 模式，2 次桌面搜索，无真实积分
- 运行 5 次取平均值，记录：
  - 总执行时间
  - 内存峰值（`psutil.Process().memory_info().rss`）
  - 搜索成功率
- 输出：`.planning/benchmarks/baseline.md`

**1.4 测试基线验证**
- 运行 `pytest tests/unit/ -m "not real"`
- 记录：
  - 总测试数、通过数、失败数
  - 各模块覆盖率（使用 `--cov=src`）
- 输出：`.planning/test_baseline.md`
- 验收：基线测试 100% 通过（现有失败需修复或记录）

### Verification Criteria

- [ ] 调用图已生成并审查
- [ ] 配置边界已定义，所有配置项状态明确
- [ ] 基准测试完成，数据已记录
- [ ] 测试基线确认，问题清单已创建

### Risk Mitigation

- **风险：** 调用图不完整，动态导入遗漏
- **缓解：** 人工审查核心模块，补充文档中的动态导入

---

## Phase 2: 低风险纯删除

**Phase Number:** 2
**Phase Name:** 低风险纯删除
**Duration:** 3–5 天
**Goal:** 安全删除无价值代码，减少 500–1,500 行

### REQ Mapping

- REQ-001 (删除死代码) - **Core**
- REQ-002 (清理注释废代码) - **Core**
- REQ-003 (删除无调用方模块) - **Core**
- REQ-004 (删除重复实现) - **Partial** (仅删除完全重复，不合并)

### Deliverables

**2.1 死代码删除**
- 使用 `vulture` 扫描 + 人工验证
- 删除至少 **30 处** 死代码（函数、类、导入）
- 提交 PR 包含 `vulture` 输出和删除清单

**2.2 注释废代码清理**
- 搜索 `# .*\n(?:.*\n)*? def ` 等模式找出大段注释代码
- 删除所有 >5 行的注释代码块
- 预期删除：10–20 处

**2.3 无调用方模块删除**
- 调用图分析，找出孤立模块
- 验证无动态导入、测试引用
- 预期删除：2–5 个模块（如工具脚本、过时处理器）
- 删除文件：`tools/` 中的非必要脚本

**2.4 重复实现删除**
- 识别完全相同的函数（如重复的配置检查）
- 删除冗余版本，保留最佳实现
- 预期删除：100–300 行

**2.5 冗余文档删除**
- 检查 `docs/` 中过时文档
- 删除或标记为 `DEPRECATED`
- 更新 `README.md` 删除已废弃功能介绍

### Verification Criteria

- [ ] 源码行数减少 500–1,500 行（验证：`wc -l src/**/*.py`）
- [ ] 所有核心功能测试通过（无功能回退）
- [ ] `config.yaml` 加载正常，无 missing keys
- [ ] git diff 可清晰看到删除内容，无争议删除

### Example Commands

```bash
# 死代码扫描
vulture src/ --exclude "src/diagnosis/*" --min-confidence 80

# 查找注释块
grep -r "^#" src/ | grep -A5 "def "   # 手动检查

# 查找孤立文件
find src/ -name "*.py" -exec sh -c 'import {} 2>/dev/null || echo {}' \;
```

---

## Phase 3: 核心模块收缩

**Phase Number:** 3
**Phase Name:** 核心模块收缩
**Duration:** 5–7 天
**Goal:** 拆分之此复杂的核心模块，降低单文件复杂度

### REQ Mapping

- REQ-005 (收缩复杂模块) - **Core**
- REQ-004 (删除重复) - **Partial** (在拆分过程中删除重复逻辑)

### Targets

**Target 1: `src/search/search_engine.py`** (732 lines → 目标 ~400 行)

**问题：**
- 包含主题管理、限流、反检测、搜索循环等混合职责
- 函数过长，条件分支过多

**拆分策略：**
1. 提取 `ThemeManager` 到 `src/browser/theme_manager.py`（独立模块）
2. 提取 `SearchThrottler` 到 `src/search/throttler.py`（限流逻辑）
3. 提取 `SearchStrategy` 基类，Desktop/Mobile 策略分离
4. 主循环精简为策略调度

**Validation:**
- 拆分后各模块 < 400 行
- 桌面/移动搜索都正常工作（测试验证）
- 性能基准无退化

---

**Target 2: `src/tasks/task_parser.py`** (656 lines → 目标 ~350 行)

**问题：**
- 硬编码选择器，脆弱
- 任务类型检测逻辑复杂
- 缺少抽象层

**拆分策略：**
1. 提取选择器定义到 `src/tasks/selectors.py`（集中管理）
2. 提取 `TaskTypeDetector` 类，分离类型检测
3. 提取 `CardParser` 类，专注单张任务卡片解析
4. 简化主 `discover_tasks()` 为编排函数

**Validation:**
- 拆分配置可通过 `config["task_selectors"]` 覆盖
- 至少支持 3 种任务类型（URL、Quiz、Poll）检测
- 测试覆盖主要路径

---

**Target 3: `src/infrastructure/health_monitor.py`** (632 lines → 目标 ~300 行)

**问题：**
- 频繁调用 `psutil`，性能开销
- 监控逻辑与资源检查混合

**拆分/简化策略：**
1. 提取 `ProcessMonitor` 到 `src/infrastructure/process_monitor.py`
2. 实现监控间隔可配置（默认 10s → 60s）
3. 批量收集指标，减少系统调用频率
4. 移除不必要的实时检查（如内存泄漏检测）

**Validation:**
- 性能基准：HealthMonitor 自身开销降低 50%+
- 关键指标仍被监控（内存、CPU、浏览器存活）
- 不影响错误告警

---

### Deliverables

- [ ] `ThemeManager` 独立模块（100–150 行）
- [ ] `SearchThrottler` 独立模块（80–120 行）
- [ ] `TaskTypeDetector` + `selectors.py`（150–200 行）
- [ ] `ProcessMonitor` 独立模块（100–150 行）
- [ ] 所有修改通过核心功能测试
- [ ] 每个新模块有基本 docstring 和类型注解

### Verification Criteria

- [ ] 上述 3 个主文件每行减少 200+ 行
- [ ] 新模块独立且职责单一
- [ ] 性能基准无退化（ preferably 改善）
- [ ] 所有核心功能测试通过

---

## Phase 4: 异常与返回语义治理

**Phase Number:** 4
**Phase Name:** 异常与返回语义治理
**Duration:** 4–6 天
**Goal:** 消除静默异常，规范函数返回值，提升错误可排查性

### REQ Mapping

- REQ-006 (治理静默异常) - **Core**
- REQ-007 (规范返回值语义) - **Core**

### Background

当前存在 100+ 处 `except Exception: pass`，严重掩盖错误。需要系统性地改进异常处理策略。

### Strategy

**分类处理：**

**A. 关键路径异常（必须修复）**
- 登录流程（`src/login/`）
- 搜索执行（`src/search/search_engine.py`）
- 任务发现（`src/tasks/task_parser.py`）
- 积分检测（`src/account/points_detector.py`）

**修复：**
```python
# 替换为
try:
    ...
except Exception as e:
    logger.error(f"[Context] Failed: {e}")
    raise   # 或 return False/error code
```

**B. 非关键路径异常（可选择修复）**
- 诊断模式的辅助检查
- Cleanup 操作（删除临时文件）
- 通知失败（已部分处理）

**策略：** 至少修复 80%，剩余的必须添加 `logger.debug()`

**C. 返回值语义规范化**

**目标函数：**
- `SearchEngine.execute_desktop_searches()` - 当前返回 `True/False`，但失败细节丢失
- `QueryEngine.generate_queries()` - 返回 `[]` 无法区分空结果和错误
- `PointsDetector.get_current_points()` - 失败时可能返回 `0`，但 `0` 也可能是真实值

**改进方案（Option B - Exception-based）：**
```python
# Current
def get_current_points() -> int:
    try:
        ... parse DOM ...
        return points
    except:
        return 0  # Ambiguous: is 0 a real value or error?

# Proposed
def get_current_points() -> int:
    ... parse DOM ...
    if not element:
        raise PointsParseError("Points element not found")
    return points
```

**新异常类：**
```python
class PointsParseError(Exception):
    """积分解析失败"""
    pass

class TaskParseError(Exception):
    """任务解析失败"""
    pass
```

### Deliverables

- [ ] 关键路径静默异常修复（>80%）
- [ ] 定义关键异常类（`src/infrastructure/errors.py` 或类似）
- [ ] 3–5 个核心函数返回值语义明确化
- [ ] 更新调用方处理新异常模式
- [ ] 单元测试覆盖新的错误路径

### Verification Criteria

- [ ] `grep -r "except.*: pass" src/ | wc -l` < 20
- [ ] 至少 50 处 `except` 现在有日志记录
- [ ] 核心函数文档清晰说明返回值语义
- [ ] 关键异常都已定义并抛出

### Out of Scope

- 100% 静默异常消除（太激进，风险高）
- 全面的错误处理架构重构（超出范围）

---

## Phase 5: 测试补锁与依赖清理

**Phase Number:** 5
**Phase Name:** 测试补锁与依赖清理
**Duration:** 3–5 天
**Goal:** 为高风险模块补充最小回归测试，清理未使用的依赖

### REQ Mapping

- REQ-008 (核心模块测试) - **Core**
- REQ-009 (依赖清理) - **Core**
- REQ-012 (文档更新) - **Partial**

### Part 1: 测试补锁

**高风险模块（当前覆盖率 ~0%）：**

| Module | Files | Test Goal | Approach |
|--------|-------|-----------|----------|
| 登录处理器 | `src/login/handlers/*.py` (10+) | 每处理器 2+ 测试用例 | Mock Playwright page/context，测试状态转换 |
| 任务处理器 | `src/tasks/handlers/*.py` (3) | 每处理器 3+ 测试用例 | Mock DOM elements，测试任务执行逻辑 |
| 积分检测器 | `src/account/points_detector.py` | 5+ 测试用例 | Mock HTML 片段，解析验证 |
| 通知器 | `src/infrastructure/notificator.py` | 3+ 测试用例 | Mock HTTP 请求，测试消息格式 |
| 健康监控 | `src/infrastructure/health_monitor.py` | 3+ 测试用例 | Mock psutil，测试指标收集 |

**测试指南：**
- 使用 `pytest` + `pytest-asyncio`
- Mock Playwright 对象（`page`, `context`）
- 使用测试 fixtures 提供固定数据
- 覆盖率目标：每个文件 ≥ 80% 行覆盖

**Example Test Structure:**
```python
class TestTotp2faHandler:
    """TOTP 2FA 处理器测试"""

    def test_handle_success(self, mocker):
        """测试成功输入 TOTP 并提交"""
        mock_page = mocker.AsyncMock()
        mock_handler = Totp2FAHandler(config, logger)
        result = await mock_handler.handle(mock_page, "123456")
        assert result is True
        mock_page.fill.assert_called_once_with("------", "123456")

    def test_invalid_code(self, mocker):
        """测试 TOTP 无效时重试"""
        ...
```

### Part 2: 依赖清理

**分析未使用依赖：**

使用工具扫描：
```bash
pip install deptry
deptry .
# 或
pip install pip-check
pip check --unused
```

**预期可移除的依赖：**
- `httpx` - 声明但未使用？需验证
- `APScheduler` - 声明但未使用（使用 `schedule` 库）
- `orjson` - 可选，可能未使用
- `pytest-benchmark` - 仅性能测试需要，可移至 `[tool.poetry.group.dev]`

**操作：**
- 更新 `pyproject.toml`，移除确认未使用的依赖
- 更新 `requirements.txt`（如果已生成）
- 验证 `pip install -e .` 成功

### Part 3: 最终文档更新

- [ ] 更新 `CLAUDE.md` 架构图（如有重大变化）
- [ ] 更新 `REQUIREMENTS.md` 状态为已完成
- [ ] 创建 `POST_MORTEM.md` 或 `CHANGELOG.md` 记录所有删除和变更

---

## Phase Interdependencies

```
Phase 1 (基线) → Phase 2 (删除) → Phase 3 (收缩) → Phase 4 (异常) → Phase 5 (测试+清理)
                │                 │                 │
                └── 兼容性检查 ───┴── 性能基准 ────┴── 测试覆盖
```

- **Phase 1** 为所有后续阶段提供基线数据和边界
- **Phase 2-3** 代码变更较大，每步需验证功能
- **Phase 4** 依赖 Phase 3 的模块结构
- **Phase 5** 最后执行，补充测试覆盖变更

---

## Skipping Criteria

可以在以下情况跳过该阶段：
- 阶段任务全部完成且验证通过，但下一阶段不必要（如不需要收缩核心）
- 发现删除/变更风险过高（如核心模块收缩导致不可接受风险）
- 资源限制（时间不够）

**Skip Decision:** 需记录原因并更新此 ROADMAP

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| 误删核心功能代码 | Low | High | Phase 1 调用图 + 人工审查 |
| 配置兼容性破坏 | Medium | High | REQ-010 强制验证，只增不减 |
| 性能退化 | Medium | Medium | Phase 1 基准测试 + 每阶段验证 |
| 引入回归 bug | Medium | High | 核心功能测试 + 新回归测试 |
| 时间超支 | High | Low | 阶段化交付，随时可停 |

---

## Phases Summary Table

| Phase | Focus | Est. Duration | Est. Δ LOC | Priority |
|-------|-------|---------------|------------|----------|
| 1 | 基线冻结 | 1 天 | 0 | MUST |
| 2 | 纯删除 | 3–5 天 | -500 to -1,500 | MUST |
| 3 | 核心收缩 | 5–7 天 | -1,000 to -2,000 | MUST |
| 4 | 异常治理 | 4–6 天 | 0 (reorg) | SHOULD |
| 5 | 测试+清理 | 3–5 天 | +500 (tests) | SHOULD |

**Total Estimated Reduction:** -2,000 to -3,500 lines (25–40% of 8,600)
**Note:** Test code added in Phase 5 offsets some deletion gains.

---

## Next Steps

1. ✅ Review and approve this ROADMAP
2. 🚧 Execute Phase 1 - Baseline & Call Graph
3. 🚧 Phase 1 complete → Proceed to Phase 2

---

**Status:** Ready for review
**Last Updated:** 2026-03-21
