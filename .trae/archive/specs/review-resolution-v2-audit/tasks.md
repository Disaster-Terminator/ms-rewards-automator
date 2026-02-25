# Tasks

- [x] Task 1: 创建数据模型 (`src/review/models.py`)
  - [x] SubTask 1.1: 创建 `ReviewThreadState` 模型（以 Thread 为核心）
  - [x] SubTask 1.2: 添加 `id` 字段（Thread ID）
  - [x] SubTask 1.3: 添加 `is_resolved` 和 `local_status` 双状态字段
  - [x] SubTask 1.4: 创建 `ReviewMetadata` 和 `ReviewDbSchema` 模型

- [x] Task 2: 创建 Qodo 解析器 (`src/review/parsers.py`)
  - [x] SubTask 2.1: 实现严谨的锚点正则 `^\s*(?:[-*]\s*)?(?:☑|✅\s*Addressed)`
  - [x] SubTask 2.2: 兼容 Markdown 列表符号 (- 或 *)
  - [x] SubTask 2.3: 实现 `is_auto_resolved` 方法
  - [x] SubTask 2.4: 实现 `detect_source` 方法

- [x] Task 3: 创建 GraphQL 客户端 (`src/review/graphql_client.py`)
  - [x] SubTask 3.1: 实现 `fetch_pr_threads` 方法（返回 Thread ID）
  - [x] SubTask 3.2: 实现 `resolve_thread` mutation
  - [x] SubTask 3.3: 实现 `reply_to_thread` mutation
  - [x] SubTask 3.4: 添加错误处理和日志

- [x] Task 4: 创建状态管理器 (`src/review/comment_manager.py`)
  - [x] SubTask 4.1: 实现 TinyDB 初始化
  - [x] SubTask 4.2: 实现 `save_threads` 方法
  - [x] SubTask 4.3: 实现远端状态同步（isResolved=true 时强制更新 local_status）
  - [x] SubTask 4.4: 实现 `mark_resolved_locally` 方法
  - [x] SubTask 4.5: 实现 `get_pending_threads` 方法
  - [x] SubTask 4.6: 添加 FileLock 并发安全

- [x] Task 5: 创建整合器 (`src/review/resolver.py`)
  - [x] SubTask 5.1: 实现 `resolve_thread` 方法（API First, DB Second）
  - [x] SubTask 5.2: 实现回复 → 解决 → 更新本地 DB 的流程
  - [x] SubTask 5.3: 添加异常处理确保数据一致性

- [x] Task 6: 创建 CLI 入口 (`tools/manage_reviews.py`)
  - [x] SubTask 6.1: 实现 `resolve` 子命令
  - [x] SubTask 6.2: 实现 `fetch` 子命令
  - [x] SubTask 6.3: 实现 `list` 子命令
  - [x] SubTask 6.4: 添加 JSON 输出格式

- [x] Task 7: 更新 Skill 文档
  - [x] SubTask 7.1: 更新 `resolve-review-comment` skill 调用 Python CLI
  - [x] SubTask 7.2: 更新 `fetch-reviews` skill 使用新的 GraphQL 查询
  - [x] SubTask 7.3: 标记旧的 Playwright 逻辑为 DEPRECATED

- [x] Task 8: 编写测试用例
  - [x] SubTask 8.3: 测试 Qodo 解析规则的边界情况（17 个测试全部通过）
  - [ ] SubTask 8.1: 测试 Thread ID 获取（需要真实 API 调用）
  - [ ] SubTask 8.2: 测试解决评论 API 调用（需要真实 API 调用）
  - [ ] SubTask 8.4: 测试 API 失败时的数据一致性（需要模拟测试）

# Task Dependencies

- Task 1 是 Task 3, Task 4, Task 5 的前置依赖
- Task 2 独立执行
- Task 3 和 Task 4 可以并行执行
- Task 5 依赖 Task 1, Task 3, Task 4
- Task 6 依赖 Task 5
- Task 7 依赖 Task 6
- Task 8 依赖所有其他任务完成
