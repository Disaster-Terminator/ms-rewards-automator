# Checklist

## 全局 Rule（project_rules.md）

- [x] 状态标签字典已定义（[REQ_DEV], [REQ_TEST], [REQ_DOCS], [BLOCK_NEED_MASTER]）
- [x] 通信媒介文件已定义（current_task.md, test_report.md, blocked_reason.md）
- [x] Master Agent 路由规则已定义
- [x] 所有执行细节已移除，Rule 极薄化

## Master Agent 配置（master.md）

- [x] 身份与权限已定义
- [x] 任务分发流程已定义（写入 current_task.md）
- [x] 状态标签响应规则已定义
- [x] Memory MCP 读写时机已明确

## test-agent 配置

- [x] 身份与边界已定义（禁止修改 src/）
- [x] 强制反推演机制已添加
- [x] 标准化阻断协议已添加（连续 2 次失败触发 [BLOCK_NEED_MASTER]）
- [x] 状态标签输出规则已定义
- [x] 文件读取流程已定义（current_task.md → 执行 → test_report.md）

## dev-agent 配置

- [x] 身份与边界已定义（禁止 Playwright）
- [x] 禁止猜测原则已添加
- [x] 上下文阻塞协议已添加
- [x] 状态标签输出规则已定义

## docs-agent 配置

- [x] 身份与边界已定义（只允许 *.md）
- [x] 状态标签输出规则已定义

## Skill 文件

- [x] test-execution: 详细测试步骤已移入，触发条件明确
- [x] dev-execution: 详细开发步骤已移入，触发条件明确
- [x] master-execution: 详细协调步骤已移入，触发条件明确
- [x] docs-execution: 详细文档步骤已移入，触发条件明确

## 通信媒介文件

- [x] current_task.md 模板已创建
- [x] test_report.md 模板已创建
- [x] blocked_reason.md 模板已更新

## 整体验证

- [x] 三层控制流架构清晰（Rule → Agent → Skill）
- [x] 状态标签在所有文件中一致
- [x] 通信媒介文件路径在所有文件中一致
- [x] 权限隔离未被破坏
