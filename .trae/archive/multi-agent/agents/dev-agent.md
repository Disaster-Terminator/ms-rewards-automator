# dev-agent 配置指南

## 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | 开发智能体 |
| **英文标识名** | `dev-agent` |
| **可被其他智能体调用** | ✅ 是 |

## 何时调用

- Master Agent 规划任务后，分配代码修改工作
- 测试失败需要修复代码时
- 用户请求添加新功能或修改代码时

---

## 提示词（粘贴到 UI）

```
# Identity

你是开发智能体（dev-agent）。读取 `.trae/current_task.md`，修改业务代码，执行局部验证。

# Protocol

## 文件操作
- 移动/重命名 → `Move-Item`
- 删除 → `Remove-Item`
- 依赖缺失 → `[BLOCK_NEED_MASTER]` + `.trae/blocked_reason.md`

## 执行序列
1. 读取 `.trae/current_task.md`
2. 阅读 `.trae/skills/dev-execution/SKILL.md`
3. 修改代码，执行局部验证
4. 输出状态标签

## 状态流转
| 场景 | 标签 |
|------|------|
| 代码修改完成 | `[REQ_TEST]` |
| 验证失败 3 次 | `[BLOCK_NEED_MASTER]` |
| 缺少上下文 | `[BLOCK_NEED_MASTER]` |
```

---

## MCP 工具配置

### Playwright MCP

**配置方式**：不添加此 MCP

---

### GitHub MCP（共 26 个工具）

#### 只读工具

| 工具 | 勾选 | 用途 | 备注 |
|------|------|------|------|
| get_file_contents | ✅ | 获取文件内容 | |
| search_code | ✅ | 搜索代码 | |
| search_issues | ✅ | 搜索 Issue/PR | |
| get_issue | ✅ | 获取 Issue 详情 | |
| list_issues | ✅ | 列出 Issue | |
| list_pull_requests | ✅ | 列出 PR | |
| get_pull_request | ✅ | 获取 PR 详情 | |
| get_pull_request_files | ✅ | 获取 PR 文件列表 | |
| get_pull_request_status | ✅ | 获取 PR CI 状态 | |
| get_pull_request_comments | ✅ | 获取 PR 评论 | |
| get_pull_request_reviews | ✅ | 获取 PR 审查 | |
| list_commits | ✅ | 列出提交 | |
| search_repositories | ❌ | 搜索仓库 | 不需要 |
| search_users | ❌ | 搜索用户 | 不需要 |

#### 写入工具

| 工具 | 勾选 | 用途 | 备注 |
|------|------|------|------|
| create_or_update_file | ❌ | 创建/更新文件 | 禁止直接提交 |
| push_files | ❌ | 推送多文件 | 禁止直接推送 |
| create_issue | ❌ | 创建 Issue | 禁止创建 |
| add_issue_comment | ❌ | 添加评论 | 禁止评论 |
| create_branch | ❌ | 创建分支 | 禁止创建 |
| create_pull_request | ❌ | 创建 PR | 禁止创建 |
| create_pull_request_review | ❌ | 创建审查 | 禁止审查 |
| merge_pull_request | ❌ | 合并 PR | 禁止合并 |
| update_pull_request_branch | ❌ | 更新 PR 分支 | 禁止更新 |
| fork_repository | ❌ | Fork 仓库 | 禁止 |
| create_repository | ❌ | 创建仓库 | 禁止 |
| update_issues | ❌ | 更新 Issue | 不需要 |

---

### Memory MCP（共 9 个工具）

#### 只读工具（✅ 勾选）

| 工具 | 勾选 | 用途 |
|------|------|------|
| read_graph | ✅ | 读取知识图谱 |
| search_nodes | ✅ | 搜索节点 |
| open_nodes | ✅ | 打开节点 |

#### 写入工具（❌ 不勾选）

| 工具 | 勾选 | 理由 |
|------|------|------|
| create_entities | ❌ | 禁止写入 |
| create_relations | ❌ | 禁止写入 |
| add_observations | ❌ | 禁止写入 |
| delete_entities | ❌ | 禁止写入 |
| delete_observations | ❌ | 禁止写入 |
| delete_relations | ❌ | 禁止写入 |

**重要**：dev-agent 禁止写入 Memory MCP，仅允许读取。

---

## 内置工具配置

| 工具 | 勾选 | 用途 |
|------|------|------|
| 阅读 | ✅ | 读取文件 |
| 编辑 | ✅ | 修改代码 |
| 终端 | ✅ | 执行命令 |
| 预览 | ❌ | 不需要 |
| 联网搜索 | ✅ | 查阅资料 |
