# REQUIREMENTS

**Project:** RewardsCore Technical Debt Reduction & Simplification
**Branch:** refactor/test-cleanup
**Date:** 2026-03-21

---

## Scope Summary

- **类型：** 技术债收敛与简化（非纯删除）
- **策略：** 删除无价值代码 + 收缩复杂实现 + 治理异常处理
- **核心：** 保持功能无回退，配置主路径兼容
- **成功：** 源码行数减少 10%-20%，质量指标改善

---

## Legend

| Priority | Description |
|----------|-------------|
| **MUST** | 必须完成，阻塞发布 |
| **SHOULD** | 强烈建议，高价值 |
| **NICE** | 如果有时间/资源则做 |

| Status | Description |
|--------|-------------|
| 📋 Planned | 尚未开始 |
| 🚧 In Progress | 进行中 |
| ✅ Done | 已完成 |
| ❌ Blocked | 受阻 |

---

## REQ-001: 删除死代码与未使用模块

**Type:** Removal
**Priority:** MUST
**Status:** 📋 Planned

**Description:**
识别并删除整个代码库中从未被使用的函数、类、方法和模块。

**Acceptance Criteria:**
- [ ] 使用静态分析工具（如 `vulture`, `pyflakes`）识别潜在死代码
- [ ] 人工验证每条死代码确实无调用方（避免误删）
- [ ] 删除至少 30 处死代码项
- [ ] 所有核心功能测试通过，无功能回退
- [ ] 提交 PR 包含详细删除清单

**Out of Scope:**
注释掉的代码块（单独需求 REQ-002）
临时脚本（单独需求 REQ-003）

**Related:**
REQ-002, REQ-003

---

## REQ-002: 清理注释废代码与冗余文档

**Type:** Removal
**Priority:** MUST
**Status:** 📋 Planned

**Description:**
移除大段注释掉的代码块、过时的 TODO 注释、以及已废弃的文档。

**Acceptance Criteria:**
- [ ] 搜索并移除 `# 注释` 形式的已废弃代码（>5 行连续注释的代码块）
- [ ] 保留有历史价值的注释（如复杂算法说明），但将代码逻辑移除
- [ ] 检查 `docs/` 目录，移除过时文档或标记为废弃
- [ ] README 和项目文档保持更新，反映当前状态
- [ ] 所有删除通过 git history 可追溯

**Examples:**
```python
# BAD: 大段注释掉的旧实现
# def old_function():
#     pass
# 应该直接删除

# GOOD: 解释性注释保留
# 使用状态机模式管理登录流程（见 ARCHITECTURE.md）
```

---

## REQ-003: 删除无调用方模块与冗余文件

**Type:** Removal
**Priority:** SHOULD
**Status:** 📋 Planned

**Description:**
识别完全独立、无任何导入引用的模块，评估后删除。

**Acceptance Criteria:**
- [ ] 使用工具（如 `pigar`, `python-fingen`）或 `grep -r "import"` 分析每个模块
- [ ] 对于无任何导入的 `.py` 文件：
  - 验证是否被 CLI 动态导入（`importlib.import_module()`）
  - 验证是否被测试文件导入
  - 验证是否被配置文件引用（如自定义处理器注册）
- [ ] 删除确认无用的模块（预期：2-5 个）
- [ ] 删除临时脚本（`tools/` 中的开发辅助脚本，除 `check_environment.py` 和 `search_terms.txt` 外）
- [ ] 验证核心功能不受影响

**Out of Scope:**
被注释掉的导入（已在 REQ-002 处理）

---

## REQ-004: 删除重复实现

**Type:** Removal
**Priority:** SHOULD
**Status:** 📋 Planned

**Description:**
查找并合并重复或高度相似的代码逻辑。

**Acceptance Criteria:**
- [ ] 识别重复的检测逻辑（如多个处理器中的相同模式）
- [ ] 识别重复的错误处理代码
- [ ] 识别重复的配置获取代码
- [ ] 提取公共方法到工具模块，删除重复代码
- [ ] 预期减少 100-300 行重复代码

**Examples:**
- 多个登录处理器中类似的 `get_state()` 方法
- 多个任务处理器中相同的 `is_completed()` 检查
- 各处的配置验证逻辑（应统一到 `ConfigValidator`）

---

## REQ-005: 收缩过度复杂的核心模块

**Type:** Refactoring (Simplification)
**Priority:** MUST
**Status:** 📋 Planned

**Description:**
针对高复杂度、单行的核心模块进行功能收缩或拆分，降低维护成本。

**Targets from CONCERNS.md:**
1. **`search_engine.py`** (732 lines) - 搜索引擎包含太多职责
2. **`task_parser.py`** (656 lines) - 任务解析器依赖硬编码选择器
3. **`health_monitor.py`** (632 lines) - 健康监控性能开销大

**Acceptance Criteria (per module):**
- [ ] 分析当前职责，识别可提取的独立功能
- [ ] 提取策略类或辅助模块
- [ ] 拆分后每个模块 < 400 行
- [ ] 核心功能测试通过
- [ ] 性能基准无退化（或改善）

**For `search_engine.py`:**
- 提取主题管理（ThemeManager）到独立模块
- 提取限流/反检测策略到独立模块
- 简化主循环，使用策略模式委托

**For `task_parser.py`:**
- 提取选择器定义到独立配置模块
- 实现选择器版本控制和回退机制
- 简化解析逻辑，拆分任务类型检测

**For `health_monitor.py`:**
- 减少监控频率（可配置间隔）
- 批量收集指标，减少 psutil 调用
- 实现采样策略（避免每次调用）

---

## REQ-006: 治理静默异常处理

**Type:** Refactoring (Error Handling)
**Priority:** MUST
**Status:** 📋 Planned

**Description:**
替换代码库中的静默异常处理（`except: pass`）为适当日志记录和错误传播。

**Baseline:** 当前存在 100+ 处 `except Exception: pass` 模式

**Acceptance Criteria:**
- [ ] 使用 grep 定位所有 `except.*:pass` 实例
- [ ] 分类分析：
  - ** MUST 修复：** 关键路径（登录、搜索、任务）中吞掉实际错误的
  - ** SHOULD 修复：** 潜在数据丢失或状态不一致的
  - ** CAN SKIP：** 明确需要静默的场景（如 cleanup 中的 `os.remove`）
- [ ] 修复目标：从 100+ 处降至 <20 处（仅保留明确需要静默的）
- [ ] 所有修复必须添加日志记录（至少 `logger.debug()`）
- [ ] 对于确需静默的场景，添加注释说明理由

**Implementation:**
```python
# BAD
try:
    do_something()
except Exception:
    pass

# GOOD
try:
    do_something()
except Exception as e:
    logger.error(f"Failed to do something: {e}")
    raise  # 或 return error code

# ONLY IF absolutely needed
try:
    do_cleanup()
except Exception:
    logger.debug("Cleanup already done")  # 至少记录DEBUG
```

**Out of Scope:**
`except Exception as e: logger.error(...)` 但不 raise 的情况（已改善）

---

## REQ-007: 规范函数返回值语义

**Type:** Refactoring (API Design)
**Priority:** SHOULD
**Status:** 📋 Planned

**Description:**
消除"空列表返回值无说明"的问题，明确返回值的语义（成功/失败/空结果）。

**Problem:** 多个函数返回 `[]` 而不区分"查询无结果"和"查询失败"。

**Targets:**
- `src/search/bing_api_client.py` - `search()`
- `src/search/query_engine.py` - `generate_queries()`
- `src/login/handlers/logged_in_handler.py` - 某些检查方法
- `src/browser/element_detector.py` - `find_element()` 返回 None vs 空列表

**Acceptance Criteria:**
- [ ] 选择 3-5 个关键函数进行分析
- [ ] 定义清晰的返回值语义（使用 `Result[T, E]` 模式或文档说明）
- [ ] 实现选择：
  - **Option A:** 返回 `(success: bool, data: T)` 元组
  - **Option B:** 成功返回数据 `T`，失败抛出具体异常 `SpecificError`
  - **Option C:** 使用 `Result[T]` 类型（需要引入 `result` 库或自定���）
- [ ] 更新调用方以处理错误情况
- [ ] 文档化返回值语义

**Recommendation:**
对于本项目，使用 **Option B**（成功返回值，失败抛异常）更简洁，因为失败本身就是异常情况。

---

## REQ-008: 核心模块补充最小回归测试

**Type:** Testing
**Priority:** MUST
**Status:** 📋 Planned

**Description:**
为高风险模块补充最小回归测试，确保重构时不会破坏核心功能。

**Critical Modules (从未测试或测试不足):**
1. **登录处理器** (`src/login/handlers/*.py`) - 10+ 个处理器，当前 0 测试
2. **任务处理器** (`src/tasks/handlers/*.py`) - 3 个处理器，当前 0 测试
3. **积分检测器** (`src/account/points_detector.py`) - DOM 解析，当前 0 测试
4. **健康监控** (`src/infrastructure/health_monitor.py`) - 监控逻辑
5. **通知器** (`src/infrastructure/notificator.py`) - 通知发送

**Acceptance Criteria:**
- [ ] 为每个关键处理器编写单元测试（使用 Mock 对象）
- [ ] 覆盖主要执行路径（happy path + 1-2 个错误路径）
- [ ] 目标：每个文件 ≥ 80% 行覆盖率
- [ ] 测试必须独立、快速（<1s 每个）
- [ ] 测试运行命令为 `pytest tests/unit/ -m "not real"` 时全部通过

**Test Structure (per module):**
```python
class TestXxxHandler:
    """Xxx 处理器单元测试"""

    def test_happy_path(self, mocker):
        """测试正常执行流程"""
        ...

    def test_error_handling(self, mocker):
        """测试异常处理"""
        ...
```

**Out of Scope:**
E2E 测试（未来里程碑）

---

## REQ-009: 清理未使用的依赖项

**Type:** Removal
**Priority:** SHOULD
**Status:** 📋 Planned

**Description:**
检查 `pyproject.toml` 和 `requirements.txt`，移除未使用的依赖包。

**Acceptance Criteria:**
- [ ] 使用 `deptry` 或 `pip-audit` 扫描未使用的依赖
- [ ] 人工验证每个"未使用"依赖（可能是动态导入）
- [ ] 移除确认未使用的包（预期：1-3 个）
- [ ] 更新 `requirements.txt` 和 `pyproject.toml`
- [ ] 验证 `pip install -e .` 和测试运行正常

**Candidates to Check:**
- `aiohttp` - 用于 DuckDuckGo/Wikipedia 查询，是否被使用？
- `httpx` - 声明了但可能未使用
- `APScheduler` - 声明了但可能未使用（使用 `schedule` 库）
- `orjson` - 可选，是否被实际使用？
- `pytest-benchmark` - 仅性能测试使用，可移至 `dev` 依赖

---

## REQ-010: 配置系统兼容性验证

**Type:** Compatibility
**Priority:** MUST
**Status:** 📋 Planned

**Description:**
确保现有 `config.yaml` 配置文件在删除/重构后保持兼容。

**Breakage Points:**
- 配置键名变更（不能移除已有键）
- 配置值类型变更（如 int → str）
- 配置默认值变更（语义改变）
- CLI 参数移除（废弃可以，但移除不行）

**Acceptance Criteria:**
- [ ] 在 `ConfigManager` 添加向后兼容性检查（单元测试）
- [ ] 对于每个删除的配置项，提供迁移路径（废弃警告）
- [ ] 测试现有 `config.example.yaml` 中的所有配置都能加载
- [ ] `ConfigValidator` 自动修复仍然有效

**Implementation Strategy:**
- 配置键只增不减（旧键保持兼容，新功能使用新键）
- 废弃配置项时，记录到 `RETIRED_CONFIG_KEYS` 并在加载时警告
- 重大变更放入 v2.0 里程碑，不在本项目中移除

---

## REQ-011: 性能基准与回归检测

**Type:** Quality
**Priority:** SHOULD
**Status:** 📋 Planned

**Description:**
建立性能基准，确保删除和简化不降低执行性能。

**Metrics:**
- 总执行时间（端到端运行时间）
- 内存使用峰值（ Resident Set Size）
- 搜索成功率（成功搜索数/总搜索数）
- CPU 使用率（HealthMonitor 本身开销）

**Acceptance Criteria:**
- [ ] 建立基准测试（使用 `--dev` 模式运行 5 次取平均）
- [ ] 记录基准结果到 `docs/performance/benchmarks.md`
- [ ] 每个阶段完成后对比基准，确保无退化 >5%
- [ ] 如果性能改善，记录并分析原因

**Baseline (example from current state):**
```
Total time: ~15 minutes (20 desktop searches)
Memory peak: ~200MB
```

---

## REQ-012: 文档同步更新

**Type:** Documentation
**Priority:** SHOULD
**Status:** 📋 Planned

**Description:**
随着代码变更，同步更新相关文档以保持准确性。

**Documents to Update:**
- `CLAUDE.md` - 项目指令、架构概览、常用命令
- `README.md` - 项目介绍、快速开始
- `docs/guides/用户指南.md` - 完整使用说明
- `docs/reference/WORKFLOW.md` - 开发工作流
- `docs/reports/技术参考.md` - 技术细节

**Acceptance Criteria:**
- [ ] 每个阶段完成后审查相关文档
- [ ] 移除文档中引用已删除功能的部分
- [ ] 更新架构图（如果重要变化）
- [ ] 更新代码示例（如有必要）

---

## Requirements Traceability Matrix

| REQ-ID | Phase | Dependencies | Testable | Priority |
|--------|-------|--------------|----------|----------|
| REQ-001 | Phase 2 | None | ✅ Yes | MUST |
| REQ-002 | Phase 2 | None | ✅ Yes | MUST |
| REQ-003 | Phase 2 | None | ✅ Yes | SHOULD |
| REQ-004 | Phase 2 | REQ-001 | ✅ Yes | SHOULD |
| REQ-005 | Phase 3 | None | ✅ Yes | MUST |
| REQ-006 | Phase 4 | None | ✅ Yes | MUST |
| REQ-007 | Phase 4 | None | ✅ Yes | SHOULD |
| REQ-008 | Phase 5 | None | ✅ Yes | MUST |
| REQ-009 | Phase 5 | None | ✅ Yes | SHOULD |
| REQ-010 | All | All | ✅ Yes | MUST |
| REQ-011 | Phase 5 | None | ✅ Yes | SHOULD |
| REQ-012 | All | None | ✅ Partial | SHOULD |

---

## Notes

- **"缺测试"不单独作为删除理由** - 代码的价值由功能决定，测试覆盖率是事后问题
- **核心功能无回退** - 任何删除/重构必须保持核心功能（搜索、登录、任务、积分）正常工作
- **配置主路径兼容** - 用户现有的 `config.yaml` 应该还能用，新增配置可有默认值
- **渐进式交付** - 每个阶段独立验证，可以停止在任意阶段而不破坏项目