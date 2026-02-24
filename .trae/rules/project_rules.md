# 项目规则

## 仓库信息

| 属性 | 值 |
|------|-----|
| owner | `Disaster-Terminator` |
| repo | `RewardsCore` |
| default_branch | `main` |

## 熔断机制

| 条件 | 动作 |
|------|------|
| 连续 3 次验证失败 | 停止执行，向用户报告 |
| 缺少必要上下文 | 停止执行，向用户请求信息 |
| 依赖缺失 | 停止执行，向用户报告 |

## Skill 触发规则

**Agent 必须主动调用 Skill 的场景**：

| 场景 | 必须调用的 Skill | 原因 |
|------|-----------------|------|
| 验收代码（开发完成后） | `acceptance-workflow` | 自动化完整验收流程（静态检查→单元测试→集成测试→E2E） |
| E2E 验收（手动阶段4-5） | `e2e-acceptance` | Dev/User 无头验收，含降级策略和诊断 |
| 处理 PR 审查评论 | `fetch-reviews` + `resolve-review-comment` | 获取和解决 AI 审查评论 |

**注意**：Agent 不应凭记忆执行验收流程，必须调用 `acceptance-workflow` skill。

## Git 洁癖

- 提交 commit 时，仅在开始新工作时新建 commit
- 同一任务的后续修改，使用 `git commit --amend` 追加（可调整描述）
- 保持提交历史整洁，避免碎片化提交

## 最佳实践

- 依赖缺失时，停止并报告给用户，不自行安装
- DOM 选择器从实际页面获取，不凭猜测
- 保存 HTML 时仅保留精简取证内容
- E2E 测试结束后及时关闭 Playwright 页面
