---
phase: 01-兼容边界冻结与调用图基线
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/codebase/CALL_GRAPH.md
  - .planning/config_boundary.md
  - .planning/benchmarks/baseline.md
  - .planning/test_baseline.md
  - .planning/benchmarks/raw_data.json
  - .planning/test_baseline_raw.txt
autonomous: true
requirements: ["REQ-010", "REQ-011"]
user_setup: []
must_haves:
  truths:
    - "调用图已生成，覆盖 ≥95% 静态导入，核心路径清晰标注"
    - "配置边界已定义，所有配置键分类明确（REQUIRED/OPTIONAL/DERIVED/DEPRECATED）"
    - "性能基准已建立，5次运行数据完整记录（时间、内存、成功率）"
    - "测试基线已确认，通过率、覆盖率、失败清单已记录"
  artifacts:
    - path: ".planning/codebase/CALL_GRAPH.md"
      provides: "调用关系图文档，包含依赖矩阵、关键路径、孤立节点"
    - path: ".planning/config_boundary.md"
      provides: "配置边界文档，分类所有配置键，标注读取位置"
    - path: ".planning/benchmarks/baseline.md"
      provides: "性能基准报告，包含平均值、标准差、环境信息"
    - path: ".planning/test_baseline.md"
      provides: "测试基线摘要，统计、覆盖率、已知问题清单"
  key_links:
    - from: "Task 1 (调用图生成)"
      to: "后续所有阶段"
      via: "提供模块依赖关系，指导删除安全边界"
      pattern: "CALL_GRAPH.md 被 Phase 2-3 引用"
    - from: "Task 2 (配置边界)"
      to: "REQ-010 配置兼容性"
      via: "标记 REQUIRED 键确保不删除，标记 DEPRECATED 提供迁移路径"
      pattern: "config_boundary.md 分类结果"
    - from: "Task 3 (性能基准)"
      to: "REQ-011 性能基准"
      via: "建立基线用于后续阶段对比，退化 >5% 需告警"
      pattern: "baseline.md 中的指标数据"
    - from: "Task 4 (测试基线)"
      to: "Phase 4-5 无回归保证"
      via: "记录当前测试状态，确保不引入新失败"
      pattern: "test_baseline.md 中的失败清单"
---

<objective>
建立技术债务治理前的"事实基线"，通过四项独立调查任务生成关键决策文档：调用关系图、配置边界定义、性能基准、测试基线。

Purpose: 为 Phase 2-5 的删除/重构工作提供安全边界和回归检测基准，确保核心功能无回退、配置主路径兼容、性能无退化。

Output: 四个规划文档（.planning/codebase/CALL_GRAPH.md, .planning/config_boundary.md, .planning/benchmarks/baseline.md, .planning/test_baseline.md）
</objective>

<execution_context>
@/home/raystorm/.claude/get-shit-done/workflows/execute-plan.md
@/home/raystorm/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/REQUIREMENTS.md
@.planning/phases/01-兼容边界冻结与调用图基线/01-CONTEXT.md

# 技术栈参考
@.planning/codebase/STACK.md
@.planning/codebase/ARCHITECTURE.md
@.planning/codebase/TESTING.md

# 核心代码参考（用于理解架构）
@src/cli.py
@src/infrastructure/ms_rewards_app.py
@src/infrastructure/config_manager.py
@config.example.yaml
</context>

<tasks>

<task type="auto">
  <name>Task 1: 生成调用关系图</name>
  <files>
    .planning/codebase/CALL_GRAPH.md
    .planning/codebase/call_graph.dot
  </files>
  <action>
    1. 安装 pyan3：`pip install pyan3`
    2. 运行静态分析生成 DOT 文件：`pyan3 src/**/*.py --dot > .planning/codebase/call_graph.dot`
    3. 分析 DOT 文件，提取：
       - 核心入口路径（cli.py → MSRewardsApp.run() → 各子系统）
       - 模块依赖关系
       - 孤立节点（无入度或无出度的模块）
    4. 人工审查以下文件的动态导入模式，补充到文档：
       - `src/infrastructure/ms_rewards_app.py`（set_* 依赖注入方法）
       - `src/infrastructure/system_initializer.py`（组件工厂模式）
       - `src/cli.py`（可能的动态加载）
       - `src/tasks/handlers/` 目录（任务处理器注册）
       - 搜索 `importlib`、`pkg_resources`、`entry_points` 的使用
    5. 创建 `.planning/codebase/CALL_GRAPH.md`，包含：
       - 依赖矩阵表格（Markdown 表格，行/列均为模块名）
       - 关键路径文字描述（从 cli.py 到各子系统）
       - 孤立节点清单（列出文件名和为什么孤立）
       - 动态导入/未知引用清单（至少 5 处）
       - 局限性说明（pyan3 无法捕获的部分）
    6. 验证覆盖率：`find src -name "*.py" | wc -l` 对比 pyan3 处理的文件数，确保 ≥95%
    </action>
  <verify>
    <automated>grep -q "核心入口路径" .planning/codebase/CALL_GRAPH.md && grep -q "依赖矩阵" .planning/codebase/CALL_GRAPH.md && test -f .planning/codebase/call_graph.dot</automated>
  </verify>
  <done>
    调用图文档已生成，包含依赖矩阵、关键路径、孤立节点清单；DOT 文件存在；覆盖率 ≥95%
  </done>
</task>

<task type="auto">
  <name>Task 2: 定义配置边界</name>
  <files>
    .planning/config_boundary.md
  </files>
  <read_first>
    - config.example.yaml（必须读取以获取所有配置键）
    - src/infrastructure/config_manager.py（必须读取以理解配置加载逻辑）
    - src/infrastructure/config_validator.py（了解验证规则）
    - .planning/REQUIREMENTS.md（REQ-010 配置兼容性要求）
  </read_first>
  <action>
    1. 提取 `config.example.yaml` 所有叶子键（最终配置项）：
       - 使用 `yq` 或手动遍历：所有具有最终值的键（如 `search.desktop_count`）
       - 忽略中间节点（如仅包含子键的 `search:`）
    2. 对每个叶子键，在源码中搜索读取位置：
       - `grep -r "config\.get(\"${key}\")" src/` 或 `grep -r "config\[" src/`
       - 记录所有匹配的文件路径和行号
    3. 根据读取位置数量及上下文判断分类：
       - REQUIRED：主路径必用（有 ≥1 读取位置且在核心流程中）
       - OPTIONAL：非关键功能可关闭（仅在可选功能如通知中读取）
       - DERIVED：由其他配置计算得出（极少情况）
       - DEPRECATED：已废弃但为兼容保留（无读取位置但有历史备注）
    4. 构建分类表格（Markdown）：
       | config_key | category | read_locations | notes |
       |------------|----------|----------------|-------|
       | search.desktop_count | REQUIRED | src/infrastructure/config_manager.py:45, src/search/search_engine.py:78 | 主搜索次数配置 |
    5. 按配置模块分组统计（如 `search.*` 类键总数、各分类数量）
    6. 对 DEPRECATED 键添加迁移建议：
       - "在 v2.0 移除，添加 backward-compat shim 并 warnings.warn"
    7. 写入 `.planning/config_boundary.md`
    </action>
  <verify>
    <automated>test -s .planning/config_boundary.md && grep -q "| REQUIRED" .planning/config_boundary.md && grep -q "config_key" .planning/config_boundary.md</automated>
  </verify>
  <done>
    配置边界文档已生成，包含所有叶子键的分类、读取位置、统计；DEPRECATED 键有迁移建议
  </done>
</task>

<task type="auto">
  <name>Task 3: 建立性能基准</name>
  <files>
    .planning/benchmarks/baseline.md
    .planning/benchmarks/raw_data.json
  </files>
  <read_first>
    - CLAUDE.md（运行命令和环境要求）
    - config.example.yaml（确保配置一致）
  </read_first>
  <action>
    1. 记录基准环境信息：
       - Python 版本：`python --version`
       - Playwright 版本：`pip show playwright | grep Version`
       - 关键依赖版本：`pip list | grep -E "pytest|ruff|mypy|psutil"`
    2. 准备测试脚本 `tools/benchmark_runner.py` 或使用 shell 脚本：
       ```python
       # 内容要求：
       - 每次运行前清理：rm -f storage_state.json; rm -rf logs/
       - 使用 subprocess.run(["rscore", "--dev", "--dry-run"], capture_output=True)
       - 记录：start = time.perf_counter(), end = time.perf_counter()
       - 采集内存：psutil.Process().memory_info().rss / 1024 / 1024
       - 判断成功：returncode == 0（dry-run 应该 100% 成功）
       - 返回 dict: {run: N, time: seconds, memory: MB, returncode: int}
       ```
    3. 强制环境约束：
       - config.yaml 中 `search.desktop_count=2`（覆盖为 2）
       - `browser.headless=false`（确保稳定）
       - `browser.type=chromium`
    4. 运行 5 次循环，每次独立环境清理，保存原始数据到 `raw_data.json`（JSON 数组）
    5. 计算统计量：
       - avg_time = mean(times)
       - std_time = stdev(times)
       - avg_memory = mean(memories)
       - std_memory = stdev(memories)
       - success_rate = (成功次数 / 总次数) * 100%
    6. 生成 `baseline.md`，包含：
       - 环境信息表格（Python、Playwright、硬件）
       - 5次运行详细数据表格
       - 平均值±标准差汇总行
       - 简要分析（"基线建立完成，用于后续对比"）
    7. 验证：确保 5 次运行全部成功（returncode=0），标准差合理（时间标准差 < 平均值的 20%）
    </action>
  <verify>
    <automated>test -s .planning/benchmarks/baseline.md && test -s .planning/benchmarks/raw_data.json && grep -q "平均值" .planning/benchmarks/baseline.md</automated>
  </verify>
  <done>
    基准测试完成 5 次，数据记录完整；baseline.md 包含环境信息、详细表格、统计摘要；全部运行成功
  </done>
</task>

<task type="auto">
  <name>Task 4: 验证测试基线</name>
  <files>
    .planning/test_baseline.md
    .planning/test_baseline_raw.txt
  </files>
  <read_first>
    - tests/ 目录结构（了解测试组织）
    - pyproject.toml 中的 pytest 配置
    - CLAUDE.md 中的测试命令约定
  </read_first>
  <action>
    1. 运行完整测试套件（排除真实浏览器测试）：
       ```bash
       pytest tests/unit/ -v -m "not real" --cov=src --cov-report=term > .planning/test_baseline_raw.txt 2>&1
       ```
    2. 解析输出文件 `test_baseline_raw.txt`：
       - 提取 "passed X, failed Y, skipped Z" 数字
       - 提取覆盖率汇总：`TOTAL ...%`
       - 如有失败，提取失败测试清单（文件名::函数名）和错误信息
    3. 按模块统计覆盖率（从 `--cov-report=term` 输出提取）
    4. 分类失败原因：
       - 环境问题：依赖缺失、配置错误（如 playwright 未安装）
       - 已知问题：确认为 bug 但不在本项目修复范围的
       - 新回归：本次出现但不应存在的失败
    5. 生成 `test_baseline.md`，包含：
       - 测试统计表格（passed/failed/skipped/total）
       - 覆盖率摘要（按模块，行覆盖率 %）
       - 失败测试详细列表（如有，包括错误类型）
       - 已知问题清单（用于 Phase 2-5 对比）
       - 建议后续改进方向
    6. 通过率验收：failures 必须为 0 或已明确记录为"已知问题"；Phase 2-5 执行时不得引入新回归
    </action>
  <verify>
    <automated>test -s .planning/test_baseline.md && test -s .planning/test_baseline_raw.txt && grep -q "测试统计" .planning/test_baseline.md</automated>
  </verify>
  <done>
    测试基线文档已生成，包含完整统计、覆盖率、失败清单（如有）；原始输出已保存；基准通过率确认（无新回归）
  </done>
</task>

</tasks>

<verification>
Phase 1 完成验证：
- [ ] CALL_GRAPH.md 存在且包含依赖矩阵、关键路径、孤立节点
- [ ] config_boundary.md 存在且所有配置键已分类
- [ ] baseline.md 存在且包含 5 次运行数据和统计
- [ ] test_baseline.md 存在且包含测试统计和覆盖率
- [ ] 所有文档在 .planning/ 目录下正确位置
</verification>

<success_criteria>
Phase 1 成功的可衡量标准：
1. 调用图覆盖率 ≥95%（pyan3 处理文件数 / src/**/*.py 总数）
2. 配置边界文档覆盖 config.example.yaml 100% 叶子键
3. 性能基准完成 5 次独立运行，成功率 100%
4. 测试基线记录当前状态，failures 数明确（用于后续对比）
5. 四个文档均被提交到 Git（或中立位置 .planning/）
</success_criteria>

<output>
After completion, create `.planning/phases/01-兼容边界冻结与调用图基线/01-SUMMARY.md` summarizing:
- Call graph results (key findings, isolated modules count)
- Config boundary summary (REQUIRED/OPTIONAL/DEPRECATED counts)
- Performance baseline numbers (avg time, avg memory, success rate)
- Test baseline stats (tests passed/failed, coverage %)
- Any issues or blockers encountered
</output>
