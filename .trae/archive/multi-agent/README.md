# 多Agent框架归档备忘

## 归档时间

2026-02-23（整理于 2026-02-24）

## 归档原因

多Agent框架过于复杂，需要隔离归档并重构为单Agent工作流，使分支能够合并。

## 整理记录

2026-02-24 整理：
- 删除 7 个冗余/过时文档
- 合并 2 组问题分析文档
- 整合架构问题到主报告
- 清空 artifacts 内容，保留格式模板

---

## 归档内容清单

### agents/

| 文件 | 说明 |
|------|------|
| `dev-agent.md` | 开发智能体配置 |
| `test-agent.md` | 测试智能体配置 |
| `docs-agent.md` | 文档智能体配置 |

### skills/

| 目录 | 说明 |
|------|------|
| `dev-execution/` | 开发执行流程 |
| `test-execution/` | 测试执行流程 |
| `docs-execution/` | 文档执行流程 |
| `master-execution/` | Master Agent执行流程 |
| `master-recovery/` | Master Agent恢复流程 |
| `mcp-acceptance/` | MCP验收流程 |
| `pr-review/` | PR审查流程 |
| `fetch-reviews/` | 获取AI审查评论 |

### prompts/

| 文件 | 说明 |
|------|------|
| `master.md` | Master Agent提示词 |

### artifacts/

| 文件 | 说明 |
|------|------|
| `current_task.md` | 任务上下文模板（已清空具体内容） |
| `test_report.md` | 测试报告模板（已清空具体内容） |
| `blocked_reason.md` | 阻塞原因模板（已清空具体内容） |

### docs/

| 文件 | 说明 |
|------|------|
| `MCP_WORKFLOW.md` | MCP驱动开发工作流 |
| `BRANCH_GUIDE.md` | 分支管理指南 |

### documents/

| 文件 | 说明 |
|------|------|
| `多智能体协作框架全面分析报告_v2.md` | 最完整的框架分析报告（含架构问题） |
| `多agent框架隔离计划.md` | 隔离决策文档 |
| `plan.md` | 分析计划 |
| `问题分析合集.md` | 合并后的问题分析 |
| `工程化闭环补丁实现反思.md` | 设计反思 |
| `规则分层优化计划.md` | 规则设计经验 |
| `agent-prompt-optimization.md` | 提示词优化经验 |
| `master-agent-constraint-enhancement.md` | 约束增强经验 |

### specs/

| 目录 | 说明 |
|------|------|
| `isolate-multi-agent-framework/` | 隔离多Agent框架spec |

---

## 架构反思

### Markdown通信的问题

原框架使用Markdown文件作为Agent间通信媒介：

```
current_task.md  → 任务分发
test_report.md   → 测试结果
blocked_reason.md → 阻塞原因
```

**问题**：
1. 无结构验证，字段缺失难以检测
2. 解析依赖正则表达式，脆弱易错
3. 无法强制必填字段
4. 版本演进困难

### 推荐方案：JSON Schema 验证

Agent间通信应使用JSON格式，配合JSON Schema验证：

```json
// current_task.json
{
  "task_id": "req-001",
  "type": "dev",
  "status": "pending",
  "dev_retry_count": 0,
  "max_retries": 3,
  "description": "修复登录超时问题",
  "context": {
    "files": ["src/login/auth.py"],
    "related_rules": ["[AUTH_TIMEOUT]"]
  }
}
```

**优势**：
1. 结构验证：字段类型、必填项自动检查
2. 枚举约束：状态值限定在预定义范围
3. 默认值：可选字段可设置默认值
4. 工具支持：成熟的验证库（jsonschema、ajv等）

### 未来改进方向

如需恢复多Agent架构，建议：

1. **通信层**：使用JSON + JSON Schema
2. **状态机**：使用状态图（XState等）定义状态转换
3. **消息队列**：考虑使用消息队列替代文件通信
4. **监控**：添加Agent行为日志和追踪

---

## 替代方案

当前采用单Agent工作流，详见：

- 项目规则：`.trae/rules/project_rules.md`
- E2E验收：`.trae/skills/e2e-acceptance/SKILL.md`
- AI审查：`.trae/skills/fetch-reviews/SKILL.md`
