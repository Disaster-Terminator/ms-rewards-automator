# Tasks

- [x] Task 1: 创建归档目录
  - [x] SubTask 1.1: 创建 `docs/reference/archive/` 目录

- [x] Task 2: 归档旧 skill
  - [x] SubTask 2.1: 移动 `ai-reviewer-guide/SKILL.md` 到 `docs/reference/archive/v1-ai-reviewer-guide.md`
  - [x] SubTask 2.2: 移动 `request-reviews/SKILL.md` 到 `docs/reference/archive/v1-request-reviews-mcp.md`
  - [x] SubTask 2.3: 删除 `.trae/skills/ai-reviewer-guide/` 目录
  - [x] SubTask 2.4: 删除 `.trae/skills/request-reviews/` 目录

- [x] Task 3: 重写 fetch-reviews skill
  - [x] SubTask 3.1: 删除肉眼识别教程（☑、✅ 相关内容）
  - [x] SubTask 3.2: 删除 Playwright DEPRECATED 部分
  - [x] SubTask 3.3: 添加 JSON 字段解析说明（local_status, is_resolved, source）
  - [x] SubTask 3.4: 添加业务裁决规则（Bug 必须修复，Suggestion 可自主决断）
  - [x] SubTask 3.5: 添加降级策略链接

- [x] Task 4: 重写 resolve-review-comment skill
  - [x] SubTask 4.1: 删除 Playwright DEPRECATED 部分
  - [x] SubTask 4.2: 简化为单行 CLI 调用说明
  - [x] SubTask 4.3: 保留参数说明和禁止事项

- [x] Task 5: 清理旧文档
  - [x] SubTask 5.1: 删除 `.trae/documents/skill文档与v2计划矛盾分析.md`
  - [x] SubTask 5.2: 更新 `.trae/documents/审查评论模块改进计划.md` 标记为已完成

# Task Dependencies

- Task 1 是 Task 2 的前置依赖
- Task 2, Task 3, Task 4 可以并行执行
- Task 5 独立执行
