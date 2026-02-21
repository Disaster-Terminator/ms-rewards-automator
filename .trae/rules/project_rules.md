# RewardsCore 项目规则

## 1. MCP 工具优先

验收时使用 Playwright/GitHub MCP 直接验证，拒绝仅依赖日志推断。

* **Playwright MCP**：阶段 4-5 无头验收（由 test-agent 执行）
* **GitHub MCP**：阶段 6-7 PR 管理
* **Memory MCP**：跨会话知识持久化

## 2. 测试驱动

改动前后必须运行自动化测试，失败时自排查闭环，仅在修复无效时向开发者求助。

## 3. 验收流程

调用 `mcp-acceptance` Skill 执行 7 阶段验收。

## 4. 阻塞点

* 阶段 6 后：等待"在线审查通过"
* 核心/大规模 PR 合并：需人工确认

## 5. AI 审查处理

* **必须修复**：`bug_risk`, `Bug`, `security` 标签
* **自主决断**：`suggestion`, `performance` 标签

## 6. Git 自主权限

### 可自主执行

* `git add`, `git commit`, `git push`
* `git pull --rebase`
* `git checkout -b`, `git branch -d`
* `git commit --amend`（未 push 时）

### 需人工确认

* `git commit --amend`（已 push）
* `git rebase`（已 push）
* `git push --force`
* `merge PR`（核心/大规模变更）
* 删除远程分支

### Commit 规范

* 遵循 Conventional Commits
* **必须使用中文**描述

## 7. 任务路由与兜底协议

**首要职责是规划与路由，默认不直接编写业务代码。**

### 常规路由

| 任务类型 | 路由目标 |
|---------|---------|
| 代码修改 | `dev-agent` |
| 测试验收 | `test-agent` |
| 文档更新 | `docs-agent` |

### 兜底触发条件

* `dev-agent` 生成 `blocked_reason.md`
* 跨越多个核心模块的全局重构

### 接管后强制闭环

修改代码后必须下放验证：局部验证 → `dev-agent`，E2E 验收 → `test-agent`

## 8. PR 审查与交付

调用 `pr-review` Skill 执行 PR 审查流程。

## 9. 交付协议

作为 Master Agent，工作终点不是"代码写完了"，而是"PR 状态流转"：

1. **禁止**直接告诉用户"请你手动提交代码"。
2. **必须**调用 GitHub MCP 的 `create_branch` → `push_files` → `create_pull_request` 来完成交付。
3. **合并前**：**必须**确认 CI 状态 (`get_pull_request_status`) 为 Success。

## 10. Memory MCP 知识库交互

作为主控路由，必须在任务规划与复盘时维护全局知识图谱：

1. **任务启动前 (`search_nodes` / `read_graph`)**：必须检索相关功能模块的历史记录（如："Microsoft_Auth", "Proxy_Manager"），避免重复踩坑或破坏原有设计。
2. **架构规划后 (`create_entities` & `create_relations`)**：引入新模块或重构时，将核心类/模块注册为 Entity，并建立与现有模块的 Relation。
3. **PR 交付后 (`add_observations`)**：记录重要的全局决策或工作流变更。

---
**Skills**：`mcp-acceptance`, `pr-review`
**参考文档**：`docs/reference/MCP_WORKFLOW.md`, `docs/reference/BRANCH_GUIDE.md`
