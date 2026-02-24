# AI 审查评论解决流程 Spec

## Why

当前流程存在以下问题：
1. 没有明确区分"代码修复"和"标记解决"
2. 没有规范的解决依据，每个解决都应该有明确的依据
3. 没有利用 Playwright 的点击解决能力
4. GitHub MCP 无法直接在机器人评论下追加回复

## What Changes

- 新增 `resolve-review-comment` skill：单评论解决（回复 + 标记解决）
- 修改 `fetch-reviews` skill：增加 comment_id、comment_url、resolution_status 字段
- 修改 `acceptance-workflow` skill：阶段 3.5 增加自动标记解决
- 定义解决依据类型：code_fixed、adopted、rejected、false_positive、outdated
- 定义何时需要回复说明：rejected、false_positive 必须回复

## Impact

- Affected specs: fetch-reviews skill, acceptance-workflow skill
- Affected code: `.trae/skills/fetch-reviews/SKILL.md`, `.trae/skills/acceptance-workflow/SKILL.md`
- New files: `.trae/skills/resolve-review-comment/SKILL.md`

## ADDED Requirements

### Requirement: 单评论解决流程

系统应提供 `resolve-review-comment` skill，用于解决单个 AI 审查评论。

#### Scenario: 代码已修复，标记解决

- **GIVEN** 评论 ID 和评论 URL
- **AND** resolution_type = code_fixed
- **WHEN** 调用 resolve-review-comment skill
- **THEN** 导航到评论页面
- **AND** 点击 "Resolve conversation" 按钮
- **AND** 验证解决状态已更新
- **AND** 返回成功结果

#### Scenario: 拒绝建议，回复说明后标记解决

- **GIVEN** 评论 ID 和评论 URL
- **AND** resolution_type = rejected
- **AND** reply_content = "拒绝原因说明"
- **WHEN** 调用 resolve-review-comment skill
- **THEN** 导航到评论页面
- **AND** 点击 "Reply" 按钮
- **AND** 填写回复内容
- **AND** 点击 "Comment" 提交
- **AND** 点击 "Resolve conversation" 按钮
- **AND** 验证解决状态已更新
- **AND** 返回成功结果

#### Scenario: 误报，回复说明后标记解决

- **GIVEN** 评论 ID 和评论 URL
- **AND** resolution_type = false_positive
- **AND** reply_content = "误报原因说明"
- **WHEN** 调用 resolve-review-comment skill
- **THEN** 导航到评论页面
- **AND** 点击 "Reply" 按钮
- **AND** 填写回复内容
- **AND** 点击 "Comment" 提交
- **AND** 点击 "Resolve conversation" 按钮
- **AND** 验证解决状态已更新
- **AND** 返回成功结果

### Requirement: 评论获取增强

`fetch-reviews` skill 应返回评论 ID 和 URL，便于后续标记解决。

#### Scenario: 返回评论元数据

- **WHEN** 调用 fetch-reviews skill
- **THEN** 返回每个评论的 comment_id
- **AND** 返回每个评论的 comment_url
- **AND** 返回每个评论的 resolution_status（pending / resolved）
- **AND** 返回已解决评论的 resolution_type

### Requirement: 验收流程集成

`acceptance-workflow` skill 的阶段 3.5 应支持自动标记解决。

#### Scenario: 自动标记已修复评论

- **GIVEN** 阶段 3.5 审查评论检查
- **AND** 存在已修复但未标记解决的评论
- **WHEN** 执行阶段 3.5
- **THEN** 对每个已修复评论调用 resolve-review-comment skill
- **AND** 记录解决依据
- **AND** 输出解决结果统计

## MODIFIED Requirements

### Requirement: 规范化处理流程

处理 AI 审查评论时必须遵循以下规范：

1. **严禁一次性解决所有评论**：每个评论必须单独处理
2. **严禁无依据标记解决**：必须先确认问题已通过代码修复或其他方式解决
3. **严禁批量操作**：必须逐个评论处理
4. **严禁跳过说明评论**：rejected、false_positive 必须在原评论下回复说明

### Requirement: 解决依据类型定义

| 依据 | 说明 | 是否需要回复 |
|------|------|--------------|
| code_fixed | 代码已修复 | ❌ |
| adopted | 已采纳建议 | ❌ |
| rejected | 拒绝建议 | ✅ |
| false_positive | 误报 | ✅ |
| outdated | 过时 | ❌ |
