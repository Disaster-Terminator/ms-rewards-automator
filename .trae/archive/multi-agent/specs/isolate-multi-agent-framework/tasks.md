# Tasks

- [x] Task 1: 创建归档目录结构
  - [x] SubTask 1.1: 创建 `.trae/archive/multi-agent/` 及子目录
  - [x] SubTask 1.2: 创建 `.trae/skills/` 目录

- [x] Task 2: 归档多Agent框架文件
  - [x] SubTask 2.1: 移动 `.trae/agents/*` 到归档目录
  - [x] SubTask 2.2: 移动 `.trae/skills/*` 到归档目录
  - [x] SubTask 2.3: 移动 `.trae/specs/*` 到归档目录
  - [x] SubTask 2.4: 移动 `.trae/prompts/*` 到归档目录
  - [x] SubTask 2.5: 移动 `.trae/documents/*` 到归档目录
  - [x] SubTask 2.6: 移动 `.trae/blocked_reason.md` 到归档目录
  - [x] SubTask 2.7: 移动 `.trae/current_task.md` 到归档目录
  - [x] SubTask 2.8: 移动 `.trae/test_report.md` 到归档目录
  - [x] SubTask 2.9: 移动 `.trae/rules/project_rules.md` 到归档目录

- [x] Task 3: 归档docs工作流文档
  - [x] SubTask 3.1: 移动 `docs/reference/MCP_WORKFLOW.md` 到归档目录
  - [x] SubTask 3.2: 移动 `docs/reference/BRANCH_GUIDE.md` 到归档目录

- [x] Task 4: 创建新的project_rules.md
  - [x] SubTask 4.1: 编写简化的项目规则文件

- [x] Task 5: 创建E2E验收Skill
  - [x] SubTask 5.1: 创建 `.trae/skills/e2e-acceptance/SKILL.md`
  - [x] SubTask 5.2: 定义Dev无头验收流程
  - [x] SubTask 5.3: 定义User无头验收流程
  - [x] SubTask 5.4: 定义Playwright MCP调用规范
  - [x] SubTask 5.5: 定义精简取证规范

- [x] Task 6: 创建AI审查获取Skill
  - [x] SubTask 6.1: 创建 `.trae/skills/fetch-reviews/SKILL.md`
  - [x] SubTask 6.2: 定义GitHub MCP调用方式
  - [x] SubTask 6.3: 定义评论类型判断逻辑

- [x] Task 7: 创建单Agent工作流文档
  - [x] SubTask 7.1: 创建 `docs/reference/WORKFLOW.md`
  - [x] SubTask 7.2: 定义完整验收流程
  - [x] SubTask 7.3: 定义MCP工具配置
  - [x] SubTask 7.4: 定义安全边界

- [x] Task 8: 清理空目录
  - [x] SubTask 8.1: 删除归档后的空目录

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 2]
- [Task 5] depends on [Task 1]
- [Task 6] depends on [Task 1]
- [Task 7] depends on [Task 4, Task 5, Task 6]
- [Task 8] depends on [Task 2, Task 3]
