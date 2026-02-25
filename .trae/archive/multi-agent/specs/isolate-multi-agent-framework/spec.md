# 单Agent工作流重构 Spec

## Why

当前多agent框架过于复杂，需要隔离归档并重构为单agent工作流，使分支能够合并。同时将功能拆分为skill，提高可维护性。

## What Changes

- **BREAKING**: 归档多agent框架到 `.trae/archive/multi-agent/`
- **BREAKING**: 归档 `docs/reference/MCP_WORKFLOW.md` 和 `docs/reference/BRANCH_GUIDE.md`
- 新建单agent工作流文档 `docs/reference/WORKFLOW.md`
- 新建skill定义文件
- 新建简化的 `project_rules.md`

## Impact

- Affected specs: 全部多agent相关spec将被归档
- Affected code: `.trae/` 目录结构重组，`docs/reference/` 文档更新

---

## ADDED Requirements

### Requirement: Solo Agent Workflow

系统应提供单Agent工作流，整合所有能力到一个Agent。

#### Scenario: 完整验收流程

- **WHEN** Agent完成代码修改
- **THEN** 执行以下验收阶段：
  1. 静态检查（ruff check + format check）
  2. 单元测试（pytest unit）
  3. 集成测试（pytest integration）
  4. Dev无头验收（E2E）
  5. User无头验收（E2E）

#### Scenario: 可选有头验收

- **WHEN** 用户请求有头验收
- **THEN** 执行有头模式验收（用户手动操作）

#### Scenario: PR创建

- **WHEN** 验收全部通过
- **THEN** 通知用户创建PR
- **AND** Agent不自动创建PR

#### Scenario: PR合并

- **WHEN** 用户确认合并
- **THEN** 用户手动合并PR
- **AND** Agent不自动合并

### Requirement: E2E验收Skill

系统应提供E2E验收skill，用于Dev和User无头验收。

#### Scenario: Dev无头验收

- **WHEN** 调用E2E验收skill
- **THEN** 执行 `rscore --dev --headless` 或降级到 `python main.py --dev --headless`
- **AND** 使用Playwright MCP监控页面状态
- **AND** 捕获异常时进行精简取证

#### Scenario: User无头验收

- **WHEN** Dev验收通过
- **THEN** 执行 `rscore --user --headless` 或降级到 `python main.py --user --headless`
- **AND** 使用Playwright MCP监控页面状态

### Requirement: AI审查获取Skill

系统应提供AI审查获取skill，用于获取PR的机器人评论。

#### Scenario: 获取审查评论

- **WHEN** 用户创建PR后
- **THEN** Agent调用skill获取Sourcery/Copilot/Qodo评论
- **AND** 分析评论类型（bug_risk/Bug/security/suggestion/performance）
- **AND** 报告给用户

### Requirement: 项目规则简化

项目规则应简化为核心约束，不包含详细工作流。

#### Scenario: 规则内容

- **WHEN** Agent读取项目规则
- **THEN** 获取以下内容：
  - 仓库信息
  - 环境安全约束
  - 文件操作规范
  - 熔断机制
  - 禁止事项

---

## REMOVED Requirements

### Requirement: 多Agent协作

**Reason**: 框架过于复杂，隔离归档

**Migration**: 所有多agent文件移动到 `.trae/archive/multi-agent/`

### Requirement: 状态标签路由

**Reason**: 单Agent不需要状态标签路由

**Migration**: 保留在归档中供参考

### Requirement: 通信媒介文件

**Reason**: 单Agent不需要Agent间通信

**Migration**: `current_task.md`, `test_report.md`, `blocked_reason.md` 归档
