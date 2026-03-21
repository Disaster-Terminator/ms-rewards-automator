# Phase 1: 兼容边界冻结与调用图基线 - Context

**Gathered:** 2026-03-21  
**Status:** Ready for planning (no discuss-phase conducted)  
**Source:** Direct planning with requirements only

---

<domain>
## Phase Boundary

Phase 1 是纯规划/调查阶段，不涉及任何代码修改。目标是通过四项调查任务建立技术基线和变更边界，为后续 4 个阶段的删除/重构工作提供安全网。

交付物均为文档类产出：
- 调用图（分析结果）
- 配置边界定义（决策文档）
- 性能基准报告（测量数据）
- 测试基线摘要（测试结果）

本阶段的核心价值在于**事实发现**而非事实改变。
</domain>

<decisions>
## Implementation Decisions

### 调查方法总体策略

- **工具选择原则：** 优先使用成熟、低摩擦、易复现的工具，避免引入临时性重依赖
- **数据来源：** 静态分析 + 实际测量 + 测试运行，三者互补
- **结果格式：** Markdown 文档，兼容量大，易于后续阶段引用
- **质量控制：** 所有数据需标注采集环境、时间、方法，确保可追溯性

### 1. 调用图生成

**推荐工具：`pyan3`**

- **为什么选它：** 纯 Python 静态分析工具，无需安装复杂依赖，能生成可读的调用关系
- **命令示例：**
  ```bash
  pyan3 src/**/*.py --html > call_graph.html
  pyan3 src/**/*.py --dot > call_graph.dot
  ```
- **适用范围：** 覆盖所有静态 `import` 语句
- **局限性：** 无法追踪动态导入（`importlib.import_module`）、插件式加载、反射调用
- **补充方案：** 人工审查关键模块（`cli.py`、`MSRewardsApp`、`TaskCoordinator`）的动态导入；在结果中明确标注"动态边界"

**输出格式：**
- `.planning/codebase/CALL_GRAPH.md` 包含：
  - 核心入口路径（`cli.py` → `MSRewardsApp.run()` → 各子系统）
  - 模块依赖矩阵（表格形式）
  - 孤立节点清单（无入度或出度的模块）
  - 动态导入/未知引用列表（需人工标记）

### 2. 配置边界定义

**分类体系：**

| 类别 | 含义 | 后续处理 |
|------|------|----------|
| `REQUIRED` | 主路径必用，删除会破坏功能 | 保持原样，100% 兼容 |
| `OPTIONAL` | 有默认值、非关键功能可关闭 | 可废弃，但需警告和迁移期 |
| `DERIVED` | 由其他配置计算得出，非用户直接设置 | 可重构为内部常量 |
| `DEPRECATED` | 已废弃但为兼容保留 | 标记警告，计划移除 |

**分析方法：**
1. 静态分析 `config.example.yaml` 和 `ConfigManager` 代码
2. 追踪每个配置键的读取位置（grep + 人工判断）
3. 标记 NEVER READ 的键为 `OPTIONAL` 或 `DEPRECATED`
4. 输出：`.planning/config_boundary.md`，包含表格："键路径 | 分类 | 读取位置 | 备注"

**关键假设：**
- 主路径 = `config.example.yaml` 中提供的全部键（默认都是 `REQUIRED`）
- 废弃配置必须提供 `warnings.warn` 或日志告警，不得静默删除

### 3. 性能基准测试

**测试环境恒定要求：**

- **模式：** `--dev`（2 次桌面搜索，`search.desktop_count=2`）
- **无头模式：** `false`（首次运行稳定）
- **浏览器：** Chromium
- **无真实账户：** 使用 `--dry-run` 或 mock 账户（避免积分检测等待）
- **后置清理：** 每次运行后删除 `storage_state.json` 和日志，确保独立

**测量指标：**

| 指标 | 采集方法 | 单位 |
|------|----------|------|
| 总执行时间 | `time.perf_counter()` 包裹 `MSRewardsApp.run()` | 秒 |
| 内存峰值 | `psutil.Process().memory_info().rss` 采样 | MB |
| 搜索成功率 | `SearchEngine` 返回值 + 积分增量验证 | % |
| CPU 平均使用 | `psutil.cpu_percent(interval=1)`（可选） | % |

**运行次数：** 5 次，取算术平均值（排除最大/最小异常值）

**输出格式：** `.planning/benchmarks/baseline.md`
```markdown
| Run | Time (s) | Memory (MB) | Success Rate |
|-----|----------|-------------|---------------|
| 1   | 45.2     | 195         | 100%          |
| 2   | 43.8     | 198         | 100%          |
| ... | ...      | ...         | ...           |
| Avg | 44.5±1.2 | 196.5±2.1   | 100%          |
```

**对比基准：** 后续阶段每次变更后需重新运行 1 次，对比基线，退化 >5% 需告警

### 4. 测试基线验证

**测试集：**
```bash
pytest tests/unit/ -v -m "not real"
```
- 排除 `real` 标记（需要真实凭证）
- 包含单元测试和轻量集成测试

**记录内容：**
- 总测试数、通过、失败、跳过
- 各文件通过率（基于 pytest 输出解析）
- 覆盖率（`--cov=src --cov-report=term-missing`）
- 失败测试清单（用于基线问题记录）

**验收标准：**
- **通过率 ≥ 100%**（当前所有测试必须通过）
- 覆盖率 ≥ 前次水平（首次建立基线即可）

**失败处理：**
- 已知失败：记录到 `.planning/test_baseline.md` 的"已知问题"段落，继续建立基线
- 未知回归：标记为阻塞，需修复后再完成本阶段

</decisions>

<canonical_refs>
## Canonical References

**下游计划执行者（执行调查任务）必须阅读以下文档：**

- `.planning/ROADMAP.md` — Phase 1 交付物定义
- `.planning/REQUIREMENTS.md` — REQ-010, REQ-011 的具体要求
- `CLAUDE.md` — 项目开发工作流、测试命令、性能调优建议
- `config.example.yaml` — 配置键全量清单
- `src/infrastructure/config_manager.py` — 配置加载逻辑

**工具参考（非必读但推荐）：**
- `pyan3` 文档：https://github.com/stephanj/pyan
- `pytest-cov` 使用：https://pytest-cov.readthedocs.io/

</canonical_refs>

<specifics>
## 具体执行思路（非强制，供参考）

### 调用图生成步骤
1. 安装 `pyan3`（若未装）：`pip install pyan3`
2. 运行静态分析：`pyan3 src/**/*.py --dot > call_graph.dot`
3. 转换为 PNG（可选）：`dot -Tpng call_graph.dot -o call_graph.png`
4. 人工审查：检查 `cli.py`、`MSRewardsApp`、`AccountManager` 等核心模块是否有未捕获的动态导入
5. 将结果整合为 Markdown 文档，嵌入 PNG（若有）或提供 DOT 下载链接

### 配置边界定义步骤
1. 列出 `config.example.yaml` 所有叶子键（使用 `yq` 或手动）
2. 对每个键，grep 搜索源码：`grep -r "config.get(\"key\")" src/`
3. 计数读取位置，若无读取 => `OPTIONAL`（或 `DEPRECATED` 若有历史备注）
4. 输出表格，并按模块分组

### 性能基准步骤
1. 编写脚本 `tools/benchmark_runner.py`，封装 `rscore --dev --dry-run` 并采集指标
2. 确保每次运行前清理 `logs/` 和 `storage_state.json`
3. 循环 5 次，记录到 JSON 文件
4. 计算平均值、标准差，生成 Markdown 报告

### 测试基线步骤
1. 运行：`pytest tests/unit/ -v -m "not real" --cov=src --cov-report=term-missing > test_output.txt`
2. 解析输出，提取测试数、覆盖率
3. 生成 Markdown 摘要，附失败测试清单（如有）
4. 保存原始输出 `test_output.txt` 供复查

</specifics>

<deferred>
## 前置决策项（可选）

如果资源/时间受限，可推迟：
- 调用图可视化（保留 DOT 文件即可，Markdown 中描述即可）
- 性能基准的 CPU 指标（仅记录时间和内存）
- 覆盖率百分比精确到小数点后 1 位

**None 必需；所有推迟项不会影响 Phase 1 交付物完整性。**
</deferred>

---

*Phase: 1 - 兼容边界冻结与调用图基线*  
*Context prepared: 2026-03-21 (no discuss-phase - assumptions explicit in plan)*
