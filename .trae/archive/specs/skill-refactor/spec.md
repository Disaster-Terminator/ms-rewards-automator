# Skill 重构 Spec

## Why

当前 skill 存在以下问题：
1. `ai-reviewer-guide` 内容过长（260 行），包含大量参考信息，不适合作为执行指令
2. `fetch-reviews` 仍包含肉眼识别教程（☑、✅），与 v2 架构不符
3. `request-reviews` 使用 GitHub MCP，与 v2 GraphQL 架构不一致
4. Skill 数量过多（6 个），增加 agent 认知负担

## What Changes

- **BREAKING**: 删除 `ai-reviewer-guide` skill，归档到 `docs/reference/archive/`
- **BREAKING**: 删除 `request-reviews` skill，归档到 `docs/reference/archive/`
- 重写 `fetch-reviews` skill，删除肉眼识别教程，改为 JSON 字段解析说明
- 重写 `resolve-review-comment` skill，简化为 CLI 调用说明
- 创建 `docs/reference/archive/` 目录存放旧文档

## Impact

- Affected specs: `review-comments-resolution`, `review-resolution-v2-audit`
- Affected code: 无代码变更，仅文档变更
- Affected skills: `fetch-reviews`, `resolve-review-comment`, `ai-reviewer-guide`, `request-reviews`

## ADDED Requirements

### Requirement: Skill 精简

系统 SHALL 将 skill 数量从 6 个减少到 4 个。

#### Scenario: Agent 调用 fetch-reviews
- **WHEN** agent 调用 fetch-reviews skill
- **THEN** skill 提供 CLI 调用方式和 JSON 字段解析说明
- **AND** skill 不包含肉眼识别教程（☑、✅ 等）

#### Scenario: Agent 调用 resolve-review-comment
- **WHEN** agent 调用 resolve-review-comment skill
- **THEN** skill 提供单行 CLI 调用说明
- **AND** skill 不包含 Playwright 相关内容

### Requirement: 降级策略

系统 SHALL 在 `docs/reference/archive/` 目录保存旧版本文档作为降级策略。

#### Scenario: CLI 失败时降级
- **WHEN** CLI 工具或 GraphQL API 失败
- **THEN** 用户可以查阅 `docs/reference/archive/` 中的旧版本文档
- **AND** 使用 MCP 或 Playwright 作为降级方案

## MODIFIED Requirements

### Requirement: fetch-reviews skill 内容

原内容包含：
- Qodo 解析规则（肉眼识别 ☑、✅）
- Playwright 降级逻辑

修改为：
- CLI 调用方式
- JSON 输出字段解析（local_status, is_resolved, source 等）
- 业务裁决规则（Bug 必须修复，Suggestion 可自主决断）
- 降级策略链接

### Requirement: resolve-review-comment skill 内容

原内容包含：
- Playwright 导航和点击操作
- 详细的使用示例

修改为：
- 单行 CLI 调用说明
- 参数说明（thread_id, resolution_type, reply）
- 禁止事项（不使用 Playwright）

## REMOVED Requirements

### Requirement: ai-reviewer-guide skill

**Reason**: 内容过长，适合作为参考文档而非执行指令
**Migration**: 移动到 `docs/reference/archive/v1-ai-reviewer-guide.md`

### Requirement: request-reviews skill

**Reason**: 使用频率低，且使用 GitHub MCP 与 v2 架构不一致
**Migration**: 移动到 `docs/reference/archive/v1-request-reviews-mcp.md`
