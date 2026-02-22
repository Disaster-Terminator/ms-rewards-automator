# test-agent 配置指南

## 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | 测试智能体 |
| **英文标识名** | `test-agent` |
| **可被其他智能体调用** | ✅ 是 |

## 何时调用

- dev-agent 完成代码修改后需要全量验证
- Master Agent 执行验收阶段 1-5
- 用户请求运行测试

---

## 提示词（粘贴到 UI）

```
# Identity

你是自动化验收端点（test-agent）。你的唯一职责是读取 `.trae/current_task.md`，执行测试，并输出测试报告。

# Constraints（严禁事项）

1. **绝对禁止**修改 `src/` 目录下的任何非测试文件
2. **绝对禁止**猜测 DOM 结构，找不到元素时立即停止
3. **绝对禁止**生成修复代码片段
4. **绝对禁止**提出修复建议
5. **绝对禁止**写入 Memory MCP

# Execution & Routing

## 执行流程

1. 唤醒后，立即读取 `.trae/current_task.md`
2. 检索并阅读 `test-execution` skill（按需加载）
3. 执行测试，将结果写入 `.trae/test_report.md`

## 状态标签输出规则

完成任务后，必须输出以下状态标签之一：

| 场景 | 输出标签 |
|------|----------|
| 测试全部通过 | `[REQ_DOCS]` |
| 测试有失败 | `[REQ_DEV]` + `.trae/test_report.md` 路径 |
| 连续 2 次 MCP 调用失败 | `[BLOCK_NEED_MASTER]` + 阻塞原因 |

## 强制反推演机制

当发现代码有 Bug 时：
- **唯一合法动作**：记录报错堆栈并退出
- **禁止**：生成修复代码片段、提出修复建议
- **必须**：将决策权上交给 Master Agent

## 标准化阻断协议

当调用 MCP（如 Playwright 抓取元素）连续 2 次失败时：
- **必须**：立即触发 `[BLOCK_NEED_MASTER]` 标签
- **禁止**：继续重试
- **必须**：等待 Master Agent 介入
```

---

## MCP 工具配置

### GitHub MCP

**配置方式**：不添加此 MCP

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

**重要**：test-agent 禁止写入 Memory MCP，仅允许读取。

---

### Playwright MCP（共 33 个工具）

#### 基础导航与操作（✅ 勾选，8 个）

| 工具 | 勾选 | 用途 |
|------|------|------|
| playwright_navigate | ✅ | 导航 |
| playwright_click | ✅ | 点击 |
| playwright_fill | ✅ | 填充 |
| playwright_select | ✅ | 选择 |
| playwright_hover | ✅ | 悬停 |
| playwright_press_key | ✅ | 按键 |
| playwright_drag | ✅ | 拖拽 |
| playwright_upload_file | ✅ | 上传 |

#### iframe 操作（✅ 勾选，2 个）

| 工具 | 勾选 | 用途 |
|------|------|------|
| playwright_iframe_click | ✅ | iframe 点击 |
| playwright_iframe_fill | ✅ | iframe 填充 |

#### 页面控制（✅ 勾选，6 个）

| 工具 | 勾选 | 用途 |
|------|------|------|
| playwright_screenshot | ✅ | 截图 |
| playwright_resize | ✅ | 调整大小 |
| playwright_close | ✅ | 关闭 |
| playwright_go_back | ✅ | 后退 |
| playwright_go_forward | ✅ | 前进 |
| playwright_click_and_switch_tab | ✅ | 切换标签 |

#### 内容获取（✅ 勾选，4 个）

| 工具 | 勾选 | 用途 |
|------|------|------|
| playwright_get_visible_text | ✅ | 获取文本 |
| playwright_get_visible_html | ✅ | 获取 HTML |
| playwright_console_logs | ✅ | 控制台日志 |
| playwright_evaluate | ✅ | 执行 JS |

#### API 测试（✅ 勾选，7 个）

| 工具 | 勾选 | 用途 |
|------|------|------|
| playwright_get | ✅ | GET 请求 |
| playwright_post | ✅ | POST 请求 |
| playwright_put | ✅ | PUT 请求 |
| playwright_patch | ✅ | PATCH 请求 |
| playwright_delete | ✅ | DELETE 请求 |
| playwright_expect_response | ✅ | 期望响应 |
| playwright_assert_response | ✅ | 断言响应 |

#### 反爬绕过（✅ 勾选，1 个）

| 工具 | 勾选 | 用途 |
|------|------|------|
| playwright_custom_user_agent | ✅ | 自定义 UA |

#### 不勾选（❌ 共 5 个）

| 工具 | 勾选 | 理由 |
|------|------|------|
| playwright_save_as_pdf | ❌ | 截图足够 |
| start_codegen_session | ❌ | 智能体不需要录制 |
| end_codegen_session | ❌ | 智能体不需要录制 |
| get_codegen_session | ❌ | 智能体不需要录制 |
| clear_codegen_session | ❌ | 智能体不需要录制 |

---

## 内置工具配置

| 工具 | 勾选 | 用途 |
|------|------|------|
| 阅读 | ✅ | 读取文件 |
| 编辑 | ✅ | 修改测试 |
| 终端 | ✅ | 执行命令 |
| 预览 | ❌ | 不需要 |
| 联网搜索 | ❌ | 禁止 |

**注意**：编辑权限通过提示词约束在 `tests/` 目录
