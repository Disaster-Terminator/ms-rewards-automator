# 合并计划文档

## 合并目标

将 `origin/main` 分支合并到 `feature/daily-tasks` 分支

## 冲突文件统计

- 总计：19个文件
- 需要手动合并：3个
- 可直接采用 origin/main：16个

---

## 处理策略

### 批次1：直接采用 origin/main（16个文件）

| 文件 | 差异类型 | 处理方式 |
|------|---------|---------|
| .pre-commit-config.yaml | 配置差异 | `git checkout --theirs` |
| pyproject.toml | 配置差异 | `git checkout --theirs` |
| requirements.txt | 功能差异（新增依赖） | `git checkout --theirs` |
| main.py | 格式差异 | `git checkout --theirs` |
| src/infrastructure/config_manager.py | 类型注解风格 | `git checkout --theirs` |
| src/infrastructure/health_monitor.py | 格式差异 | `git checkout --theirs` |
| src/infrastructure/ms_rewards_app.py | 类型注解风格 | `git checkout --theirs` |
| src/infrastructure/scheduler.py | 功能差异（更优雅） | `git checkout --theirs` |
| src/search/search_engine.py | 类型注解风格 | `git checkout --theirs` |
| src/ui/bing_theme_manager.py | 类型注解风格 | `git checkout --theirs` |
| src/ui/tab_manager.py | 类型注解风格 | `git checkout --theirs` |
| tests/autonomous/autonomous_test_runner.py | 代码冗余 | `git checkout --theirs` |
| tests/autonomous/integrated_test_runner.py | 代码冗余 | `git checkout --theirs` |
| tests/autonomous/run_autonomous_tests.py | 格式差异 | `git checkout --theirs` |
| tests/unit/test_bing_theme_manager.py | 功能差异（测试） | `git checkout --theirs` |
| tools/check_environment.py | 引号风格 | `git checkout --theirs` |

### 批次2：需要手动合并（3个文件）

| 文件 | 问题 | 处理策略 |
|------|------|---------|
| docs/BRANCH_GUIDE.md | 功能差异 | 需要合并两边的分支信息 |
| src/tasks/task_parser.py | **功能差异（重要）** | HEAD有更完善的任务发现逻辑，需保留HEAD功能 + origin/main类型注解 |
| tools/diagnose.py | 功能差异 | HEAD有增强诊断功能，需确认保留哪些 |

---

## 关键决策点（已确认）

### 1. src/tasks/task_parser.py

**HEAD改动**：更完善的任务发现逻辑

- 多选择器支持
- 去重机制
- 更多 sectionIds
- 更好的标题提取

**处理**：保留 HEAD 的功能代码，同时采用 origin/main 的类型注解风格

### 2. tools/diagnose.py

**HEAD改动**：

- headless=True（无头模式）
- 多页面诊断（dashboard, earn）
- 时间戳命名
- 保存到 logs/diagnostics/

**处理**：保留 HEAD 的增强诊断功能

### 3. main.py

**差异**：纯格式差异，两边全局变量相同

**处理**：直接采用 origin/main

---

## 执行步骤

1. 合并 origin/main
2. 批次1：执行 `git checkout --theirs` 处理16个文件
3. 批次2：手动处理3个文件
4. 添加所有文件到暂存区
5. 提交合并
