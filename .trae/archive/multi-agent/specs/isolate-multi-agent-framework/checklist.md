# Checklist

## 归档验证

- [x] `.trae/archive/multi-agent/agents/` 包含所有agent配置文件
- [x] `.trae/archive/multi-agent/skills/` 包含所有skill定义
- [x] `.trae/archive/multi-agent/specs/` 包含所有spec目录
- [x] `.trae/archive/multi-agent/prompts/` 包含master.md
- [x] `.trae/archive/multi-agent/documents/` 包含所有文档
- [x] `.trae/archive/multi-agent/artifacts/` 包含通信媒介文件
- [x] `.trae/archive/multi-agent/rules/` 包含旧project_rules.md
- [x] `.trae/archive/multi-agent/docs/` 包含MCP_WORKFLOW.md和BRANCH_GUIDE.md

## 新文件验证

- [x] `.trae/rules/project_rules.md` 存在且内容正确
- [x] `.trae/skills/e2e-acceptance/SKILL.md` 存在且内容正确
- [x] `.trae/skills/fetch-reviews/SKILL.md` 存在且内容正确
- [x] `docs/reference/WORKFLOW.md` 存在且内容正确

## 目录结构验证

- [x] `.trae/agents/` 目录已删除
- [x] `.trae/prompts/` 目录已删除
- [x] `.trae/documents/` 目录已删除
- [x] `.trae/blocked_reason.md` 已移动
- [x] `.trae/current_task.md` 已移动
- [x] `.trae/test_report.md` 已移动

## 内容验证

- [x] project_rules.md 包含仓库信息
- [x] project_rules.md 包含环境安全约束
- [x] project_rules.md 包含文件操作规范
- [x] project_rules.md 包含熔断机制
- [x] project_rules.md 包含禁止事项
- [x] e2e-acceptance skill 包含Dev验收流程
- [x] e2e-acceptance skill 包含User验收流程
- [x] e2e-acceptance skill 包含Playwright MCP调用规范
- [x] e2e-acceptance skill 包含精简取证规范
- [x] fetch-reviews skill 包含GitHub MCP调用方式
- [x] fetch-reviews skill 包含评论类型判断逻辑
- [x] WORKFLOW.md 包含完整验收流程（静态检查→单元测试→集成测试→Dev无头→User无头）
- [x] WORKFLOW.md 包含可选有头验收说明
- [x] WORKFLOW.md 包含PR创建/合并由用户负责的说明
- [x] WORKFLOW.md 包含MCP工具配置
- [x] WORKFLOW.md 包含安全边界
