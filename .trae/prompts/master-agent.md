# Master Agent 配置指南

## 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | 主控智能体 |
| **英文标识名** | `master-agent` |
| **可被其他智能体调用** | ❌ 否（顶层调度者） |

## 可调用 Agent

| Agent | 调用场景 |
|-------|---------|
| dev-agent | 代码修改任务 |
| test-agent | 测试验收任务 |
| docs-agent | 文档更新任务 |

---

## MCP 工具配置（共 28 个）

### Memory MCP（9 个）

| 工具 | 勾选 |
|------|------|
| create_entities | ✅ |
| create_relations | ✅ |
| add_observations | ✅ |
| delete_entities | ✅ |
| delete_observations | ✅ |
| delete_relations | ✅ |
| read_graph | ✅ |
| search_nodes | ✅ |
| open_nodes | ✅ |

---

### GitHub MCP（19 个）

#### 版本交付（写入）
| 工具 | 勾选 |
|------|------|
| create_branch | ✅ |
| create_or_update_file | ✅ |
| push_files | ✅ |
| create_pull_request | ✅ |
| create_pull_request_review | ✅ |
| merge_pull_request | ✅ |
| update_pull_request_branch | ✅ |
| create_issue | ✅ |
| add_issue_comment | ✅ |

#### PR 管理（只读）
| 工具 | 勾选 |
|------|------|
| get_pull_request | ✅ |
| get_pull_request_status | ✅ |
| get_pull_request_files | ✅ |
| get_pull_request_comments | ✅ |
| get_pull_request_reviews | ✅ |
| list_pull_requests | ✅ |

#### 代码与需求（只读）
| 工具 | 勾选 |
|------|------|
| get_file_contents | ✅ |
| search_code | ✅ |
| search_issues | ✅ |
| get_issue | ✅ |
| list_commits | ✅ |

#### 不勾选
| 工具 | 勾选 |
|------|------|
| search_repositories | ❌ |
| search_users | ❌ |
| fork_repository | ❌ |
| create_repository | ❌ |
| update_issue | ❌ |

---

### Playwright MCP

**配置方式**：不添加此 MCP

---

## 内置工具配置

| 工具 | 勾选 |
|------|------|
| 阅读 | ✅ |
| 编辑 | ✅ |
| 终端 | ✅ |
| 预览 | ❌ |
| 联网搜索 | ✅ |

---

**注意**：调度规则、Memory MCP 使用、异常处理、版本交付流程详见 `project_rules.md`
