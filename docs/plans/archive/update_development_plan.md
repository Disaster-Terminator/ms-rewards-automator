# 计划：更新 REWARDS_V2_ADAPTATION.md 开发计划

## 背景

诊断分支 (`refactor/diagnosis-integration`) 已合并到 main，项目经历了极大程度的重构：
- **#9**: 重构诊断系统与 PR 审查工作流，引入 MCP 驱动的多智能体框架
- **#8**: 调整搜索次数默认值并重命名项目为 RewardsCore

需要更新开发计划文档以反映最新状态。

---

## 当前项目状态

### 已合并 PR（最新）
| PR | 标题 | 状态 |
|----|------|------|
| #9 | 重构诊断系统与 PR 审查工作流 | ✅ 已合并 |
| #8 | 调整搜索次数默认值并重命名项目 | ✅ 已合并 |
| #7 | 搜索功能改进和拟人化行为集成 | ✅ 已合并 |
| #6 | earn页面任务系统 | ✅ 已合并 |
| #5 | 参数精简与调度器整改 | ✅ 已合并 |

### 分支状态
| 分支 | 状态 | 说明 |
|------|------|------|
| `main` | 🟢 最新 (771ad45) | 诊断系统已集成 |
| `feature/frontend-ui` | 🔄 工作树存在 (85f5997) | 待合并 |
| `feature/notifications` | 📋 待开发 | 通知系统 |
| `refactor/diagnosis-integration` | ✅ 已合并 | 工作树已清理 |
| `fix/search-count-rename` | ✅ 已合并 | 工作树已清理 |

### 代码结构变化
- **新增模块**：
  - `src/diagnosis/` - 诊断系统（从 tests/autonomous 迁移）
  - `src/review/` - PR 审查系统（MCP 驱动）
- **移除**：
  - `tests/autonomous/` - 已迁移到 src/diagnosis/
- **重命名**：
  - 项目名称: `MS-Rewards-Automator` → `RewardsCore`

---

## 更新内容

### 1. 最新进展部分
- 更新已合并 PR 列表（添加 #8, #9）
- 更新分支状态表
- 更新工作树状态
- 更新最近提交历史

### 2. 分支规划部分
- 标记 `refactor/diagnosis-integration` 为已合并
- 标记 `fix/search-count-rename` 为已合并
- 更新开发顺序建议

### 3. 问题记录部分
- 移除已解决的"自主测试框架未集成"问题
- 更新测试流程问题分析（诊断系统已集成）

### 4. 待清理/待开发部分
- 更新待清理列表
- 更新待开发列表

### 5. 任务文档归档
- 将已完成的任务文档移动到 `docs/tasks/archive/`

---

## 具体修改

### REWARDS_V2_ADAPTATION.md 修改点

1. **〇、最新进展**：
   - 添加 #8, #9 到已合并 PR 列表
   - 更新分支状态表
   - 更新工作树列表
   - 更新提交历史

2. **三、分支规划**：
   - 标记 `refactor/diagnosis-integration` 为 ✅ 已合并
   - 标记 `fix/search-count-rename` 为 ✅ 已合并
   - 更新开发顺序建议

3. **六、开发流程改进**：
   - 更新问题记录（诊断系统已集成）
   - 更新验收流程规范

4. **七、架构优化建议**：
   - 移除"问题6：自主测试框架集成改造"（已完成）
   - 更新其他问题状态

5. **八、后续行动**：
   - 更新待清理列表
   - 更新待开发列表

### 任务文档归档

- `docs/tasks/TASK_refactor_autonomous_test.md` → `docs/tasks/archive/`
- `docs/tasks/TASK_fix_search_count_rename.md` → `docs/tasks/archive/`

---

## 执行步骤

1. 更新 `REWARDS_V2_ADAPTATION.md` 文档
2. 归档已完成的任务文档
3. 验证文档更新正确性

---

## DoD

- [ ] REWARDS_V2_ADAPTATION.md 反映最新项目状态
- [ ] 已完成的任务文档已归档
- [ ] 分支状态、工作树状态准确
- [ ] 开发顺序建议已更新
