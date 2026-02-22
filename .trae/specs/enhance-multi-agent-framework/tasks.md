# Tasks

- [x] Task 1: 重构全局 Rule（project_rules.md）
  - [x] SubTask 1.1: 定义状态标签字典（Tags）
  - [x] SubTask 1.2: 定义通信媒介文件（Artifacts）
  - [x] SubTask 1.3: 定义 Master Agent 路由规则
  - [x] SubTask 1.4: 移除所有执行细节

- [x] Task 2: 重构 Master Agent 配置（master.md）
  - [x] SubTask 2.1: 定义身份与权限
  - [x] SubTask 2.2: 定义任务分发流程（写入 current_task.md）
  - [x] SubTask 2.3: 定义状态标签响应规则
  - [x] SubTask 2.4: 定义 Memory MCP 读写时机

- [x] Task 3: 重构 test-agent 配置
  - [x] SubTask 3.1: 定义身份与边界（禁止修改 src/）
  - [x] SubTask 3.2: 定义强制反推演机制
  - [x] SubTask 3.3: 定义标准化阻断协议
  - [x] SubTask 3.4: 定义状态标签输出规则（[REQ_DEV]/[REQ_DOCS]/[BLOCK_NEED_MASTER]）
  - [x] SubTask 3.5: 定义文件读取流程（current_task.md → 执行 → test_report.md）

- [x] Task 4: 重构 dev-agent 配置
  - [x] SubTask 4.1: 定义身份与边界（禁止 Playwright）
  - [x] SubTask 4.2: 定义禁止猜测原则
  - [x] SubTask 4.3: 定义上下文阻塞协议
  - [x] SubTask 4.4: 定义状态标签输出规则（[REQ_TEST]/[BLOCK_NEED_MASTER]）

- [x] Task 5: 重构 docs-agent 配置
  - [x] SubTask 5.1: 定义身份与边界（只允许 *.md）
  - [x] SubTask 5.2: 定义状态标签输出规则

- [x] Task 6: 重构 Skill 文件
  - [x] SubTask 6.1: test-execution - 移入详细测试步骤
  - [x] SubTask 6.2: dev-execution - 移入详细开发步骤
  - [x] SubTask 6.3: master-execution - 移入详细协调步骤
  - [x] SubTask 6.4: docs-execution - 移入详细文档步骤

- [x] Task 7: 创建通信媒介文件模板
  - [x] SubTask 7.1: 创建 current_task.md 模板
  - [x] SubTask 7.2: 创建 test_report.md 模板
  - [x] SubTask 7.3: 更新 blocked_reason.md 模板

# Task Dependencies

- [Task 2] 依赖 [Task 1]：Master Agent 配置需要全局 Rule 的状态标签定义
- [Task 3] 依赖 [Task 1]：test-agent 配置需要全局 Rule 的状态标签定义
- [Task 4] 依赖 [Task 1]：dev-agent 配置需要全局 Rule 的状态标签定义
- [Task 5] 依赖 [Task 1]：docs-agent 配置需要全局 Rule 的状态标签定义
- [Task 6] 依赖 [Task 2-5]：Skill 文件需要 Agent 配置中的引用
- [Task 7] 依赖 [Task 1]：通信媒介文件需要全局 Rule 的定义
- [Task 3, 4, 5] 可并行执行
