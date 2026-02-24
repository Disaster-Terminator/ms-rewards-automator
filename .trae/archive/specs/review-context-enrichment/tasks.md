# Tasks

- [x] Task 1: 添加 rich 库依赖
  - [x] SubTask 1.1: 在 `pyproject.toml` 的 dev dependencies 中添加 `rich>=13.0.0`
  - [x] SubTask 1.2: 验证 rich 库可以正常导入

- [x] Task 2: 创建 EnrichedContext 数据模型
  - [x] SubTask 2.1: 在 `src/review/models.py` 中添加 `EnrichedContext` 类
  - [x] SubTask 2.2: 在 `ReviewThreadState` 中添加 `enriched_context: Optional[EnrichedContext] = None` 字段

- [x] Task 3: 实现 Qodo Emoji 类型解析
  - [x] SubTask 3.1: 在 `src/review/parsers.py` 中添加 Emoji 正则表达式
  - [x] SubTask 3.2: 实现 `parse_qodo_issue_types(body: str) -> str` 方法
  - [ ] SubTask 3.3: 编写单元测试验证 Emoji 解析

- [x] Task 4: 实现 Sourcery Prompt 映射逻辑
  - [x] SubTask 4.1: 在 `src/review/resolver.py` 中实现 `_map_prompt_to_threads()` 方法
  - [x] SubTask 4.2: 实现 Left Join 策略（只匹配 `is_resolved=False` 的 Thread）
  - [x] SubTask 4.3: 实现同一行多 Thread 的 First Match 策略

- [x] Task 5: 实现 Issue Comments 获取与过滤
  - [x] SubTask 5.1: 在 `src/review/resolver.py` 的 `fetch_threads()` 中调用 `fetch_issue_comments()`
  - [x] SubTask 5.2: 在 `src/review/parsers.py` 中实现 `is_qodo_pr_reviewer_guide()` 方法
  - [x] SubTask 5.3: 在 `src/review/parsers.py` 中实现 `is_qodo_review_summary()` 方法
  - [x] SubTask 5.4: 在 `resolver.py` 中实现 Issue Comment 过滤和存储逻辑

- [x] Task 6: 实现 Qodo Thread 类型注入
  - [x] SubTask 6.1: 在 `resolver.py` 中为 Qodo Thread 调用 `parse_qodo_issue_types()`
  - [x] SubTask 6.2: 将解析结果存入 `Thread.enriched_context.issue_type`

- [x] Task 7: 数据迁移 - 移除 prompt_individual_comments
  - [x] SubTask 7.1: 从 `ReviewOverview` 模型中移除 `prompt_individual_comments` 字段
  - [x] SubTask 7.2: 修改 `overviews` 命令从 Thread 数据重建 individual comments 输出
  - [x] SubTask 7.3: 更新 `comment_manager.py` 的 `save_overviews()` 方法

- [x] Task 8: 移除 IssueCommentOverview.local_status
  - [x] SubTask 8.1: 从 `IssueCommentOverview` 模型中移除 `local_status` 字段
  - [x] SubTask 8.2: 更新相关代码以适应模型变化

- [x] Task 9: 增强 CLI 表格输出
  - [x] SubTask 9.1: 在 `tools/manage_reviews.py` 中导入 rich 库
  - [x] SubTask 9.2: 实现 `print_threads_table()` 函数
  - [x] SubTask 9.3: 添加 `--format` 参数支持 `table` 和 `json` 两种输出格式
  - [x] SubTask 9.4: 实现 Enriched 列的类型缩写显示
  - [x] SubTask 9.5: 实现颜色区分（红色=必须修复，黄色=建议）

- [x] Task 10: 更新 Skill 文档
  - [x] SubTask 10.1: 更新 `fetch-reviews/SKILL.md` 说明 Thread 是主要操作对象
  - [x] SubTask 10.2: 更新 `fetch-reviews/SKILL.md` 说明 Overview 是只读参考
  - [x] SubTask 10.3: 添加 `enriched_context` 字段说明
  - [x] SubTask 10.4: 更新输出格式示例
  - [x] SubTask 10.5: 添加降级策略说明（CLI 失败时参考归档文档）

- [x] Task 11: 更新归档文档（修正已知错误）
  - [x] SubTask 11.1: 添加三种机器人的 GitHub 用户名
  - [x] SubTask 11.2: 修正 Qodo 行级评论格式（移除错误的 ☑ 符号）
  - [x] SubTask 11.3: 修正 Code Review by Qodo 的 API 返回说明（"截断" → "空字符串"）
  - [x] SubTask 11.4: 添加行级评论格式说明

- [x] Task 12: 更新计划文档
  - [x] SubTask 12.1: 在计划文档中标记已完成的改进项
  - [x] SubTask 12.2: 记录实际实现与计划的差异

# Task Dependencies

- Task 1 独立执行
- Task 2 是 Task 4, Task 6 的前置依赖
- Task 3 是 Task 6 的前置依赖
- Task 4, Task 5, Task 6 可以并行执行
- Task 7 依赖 Task 4 完成
- Task 8 独立执行，可与 Task 7 并行
- Task 9 依赖 Task 2, Task 4, Task 6 完成
- Task 10 依赖 Task 9 完成
- Task 11 独立执行，可与 Task 10 并行
- Task 12 在所有任务完成后执行
