# Checklist

## EnrichedContext 数据模型

- [x] `EnrichedContext` 类存在于 `src/review/models.py`
- [x] `issue_type` 字段默认值为 "suggestion"
- [x] `issue_to_address` 字段为 Optional[str]
- [x] `code_context` 字段为 Optional[str]
- [x] `ReviewThreadState` 包含 `enriched_context: Optional[EnrichedContext]` 字段

## Qodo Emoji 解析

- [x] `parse_qodo_issue_types()` 方法存在于 `src/review/parsers.py`
- [x] 正确识别 `🐞 Bug` 模式
- [x] 正确识别 `📘 Rule violation` 模式
- [x] 正确识别 `⛨ Security` 模式
- [x] 正确识别 `⚯ Reliability` 模式
- [x] 正确识别 `✓ Correctness` 模式
- [x] 多类型正确拼接（如 "Bug, Security"）
- [x] 无匹配时返回默认值 "suggestion"

## Sourcery Prompt 映射

- [x] `_map_prompt_to_threads()` 方法存在于 `src/review/resolver.py`
- [x] 使用 `file_path` + `line_number` 进行匹配
- [x] 只匹配 `is_resolved=False` 的 Thread
- [x] 同一行多 Thread 时只注入第一个
- [x] 找不到匹配 Thread 时丢弃摘要（Left Join）

## Issue Comments 获取

- [x] `fetch_threads()` 调用 `fetch_issue_comments()`
- [x] `is_qodo_pr_reviewer_guide()` 方法正确识别 PR Reviewer Guide
- [x] `is_qodo_review_summary()` 方法正确识别 Review Summary
- [x] PR Reviewer Guide 存储为 `IssueCommentOverview`
- [x] Review Summary 标记 `is_code_change_summary=True`

## 数据迁移

- [x] `ReviewOverview` 不再填充 `prompt_individual_comments` 字段
- [x] `overviews` 命令从 Thread 数据输出 enriched_context
- [x] `IssueCommentOverview` 不再包含 `local_status` 字段

## CLI 表格输出

- [x] `rich` 库已添加到依赖
- [x] `list` 命令支持 `--format table` 参数
- [x] 表格包含 ID, Source, Status, Enriched, Location 列
- [x] Enriched 列正确显示 ✅ + 类型缩写
- [x] 必须修复类型显示为红色
- [x] 建议类型显示为黄色
- [x] 默认输出格式为 table

## Skill 文档

- [x] `fetch-reviews/SKILL.md` 说明 Thread 是主要操作对象
- [x] `fetch-reviews/SKILL.md` 说明 Overview 是只读参考
- [x] `enriched_context` 字段说明已添加
- [x] 输出格式示例已更新
- [x] 降级策略说明已添加（CLI 失败时参考归档文档）

## 归档文档修正

- [x] Sourcery 机器人 ID 已添加（`sourcery-ai bot`）
- [x] Copilot 机器人 ID 已添加（`Copilot AI`）
- [x] Qodo 机器人 ID 已添加（`qodo-code-review bot`）
- [x] Qodo 行级评论格式已修正（移除错误的 ☑ 符号）
- [x] Code Review by Qodo API 返回说明已修正（"截断" → "空字符串"）
- [x] 行级评论格式说明已添加

## 单元测试

- [ ] Qodo Emoji 解析测试通过
- [ ] Sourcery 映射逻辑测试通过
- [ ] Issue Comment 过滤测试通过
