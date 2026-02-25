---
name: dev-execution
description: 开发执行详细流程。dev-agent 执行代码修改时调用。
---

# 开发执行详细流程

## 前置检查（强制拦截）

执行任何操作前，必须确认：

- [ ] 文件移动/重命名 → 使用 `Move-Item` 命令
- [ ] 批量删除 → 使用 `Remove-Item` 命令
- [ ] 环境依赖 → 禁止自行安装，发现缺失时触发阻断协议

### 环境异常阻断协议

若发现代码运行缺少第三方依赖库：

1. **绝对禁止**自行执行 `pip install` 或 `conda install`
2. 立刻终止当前任务
3. 输出 `[BLOCK_NEED_MASTER]` 标签
4. 在 `.trae/blocked_reason.md` 中说明：
   - `reason_type: missing_context`
   - 缺失依赖名称
   - 建议用户执行的安装命令

### 权限隔离约束

- 使用 Playwright MCP → 禁止（无此工具）
- 写入 Memory MCP → 禁止（只读权限）
- 写入 GitHub MCP → 禁止（只读权限）
- 猜测 DOM 结构/选择器 → 禁止，触发 `[BLOCK_NEED_MASTER]`

---

## 触发条件

- 收到 `[REQ_DEV]` 标签
- Master Agent 分发代码修改任务

## 执行流程

### 1. 读取任务上下文

```
读取 `.trae/current_task.md` 获取任务详情
```

### 2. 检查重试计数（熔断器检查）

**必须先检查 `dev_retry_count` 和 `max_retries`**：

```yaml
---
dev_retry_count: <当前重试次数>
max_retries: <最大重试次数，默认 3>
---
```

| 条件 | 动作 |
|------|------|
| `dev_retry_count >= max_retries` | **禁止继续**，输出 `[BLOCK_NEED_MASTER]`，设置 `reason_type: retry_exhausted` |
| `dev_retry_count < max_retries` | 继续执行 |

### 3. 检索历史知识

```
使用 Memory MCP search_nodes 检索相关规则
检索标签：[REWARDS_DOM], [ANTI_BOT]
```

### 4. 修改代码

修改业务代码（`src/` 等非测试目录）。

### 5. 局部验证（< 30秒）

```bash
ruff check .
ruff format --check .
mypy src/ --strict
pytest tests/<相关单文件>.py -v
```

### 6. 验证失败处理

- 调用【阅读】工具查看前一次终端完整日志
- 修复并重试（最大重试次数：3）

### 7. 输出状态标签

| 场景 | 输出标签 |
|------|----------|
| 代码修改完成，需要测试验证 | `[REQ_TEST]` |
| 连续 3 次局部验证失败 | `[BLOCK_NEED_MASTER]` + 阻塞原因 |
| 缺少 DOM 结构等上下文 | `[BLOCK_NEED_MASTER]` + 需要的信息 |

## 禁止猜测原则

当无法定位元素或缺少前端结构数据时：

- **必须**：生成 `blocked_reason.md`，说明需要的 DOM 结构
- **禁止**：随意猜测选择器
- **必须**：挂起任务，等待 Master Agent 提供补充数据

## 上下文阻塞协议

当遇到以下情况时，必须触发 `[BLOCK_NEED_MASTER]`：

- 连续 3 次局部验证失败
- 缺少必要的上下文信息（如 DOM 结构）
- 遇到无法理解的报错

## 触发阻断

若第 3 次重试仍失败，停止操作：

1. 生成 `.trae/blocked_reason.md`
2. 设置 `reason_type: logic_unimplementable` 或 `missing_context`
3. 记录 3 种尝试过的修复方案
4. 附上完整 Traceback（最多 10 行）
5. 输出 `[BLOCK_NEED_MASTER]` 标签

## 输出格式（强制）

写入 `.trae/current_task.md`（更新）：

```markdown
---
task_id: <任务ID>
status: success | blocked
dev_retry_count: <当前重试次数>
max_retries: <最大重试次数>
---

### 变更摘要

- `<文件路径>`: <变更核心逻辑说明>

### 验证结果

- [x] `ruff check` 通过
- [x] `ruff format --check` 通过
- [x] `mypy` 通过
- [x] 局部单元测试通过

### 移交说明

- **验证入口**: `python main.py --task <具体命令>`
- **受影响模块**: `<具体文件或类名>`
- **需重点验证**: <如：代理切换时的 Session 保持>
```

## Memory MCP 知识库交互

1. **动手编码前 (`search_nodes`)**：检索目标文件或核心函数的 Entity，读取过去的 observations，确认是否有特殊的业务约束（如并发锁机制、特定的 API 字段转换规则）。
2. **禁止写入 Memory MCP**：如果发现需要记录的重要信息，返回给 Master Agent 处理。

## GitHub MCP 调用策略（条件触发）

仅在以下场景**必须**调用 GitHub MCP，其余时间优先依赖本地上下文：

1. **关联任务**：当用户指令包含 "Issue #..." 或 "PR #..." 时，使用 `get_issue` / `get_pull_request` 获取详细背景。
2. **未知报错**：当本地修复陷入僵局，无法理解报错原因时，使用 `search_issues` 搜索社区或历史解决方案。
3. **涉及第三方库升级时**：**建议**先使用 `search_code` 确认该库在项目中的其他引用位置，防止破坏性变更。

## 信息获取协议

为了防止幻觉和重复造轮子：

1. **收到报错修复任务时**：如果未提供完整 Log，**禁止**直接开始修改代码。**必须**先要求用户提供 Log，或尝试 `search_issues` 搜索类似错误。
2. **涉及第三方库升级时**：**建议**先使用 `search_code` 确认该库在项目中的其他引用位置，防止破坏性变更。
