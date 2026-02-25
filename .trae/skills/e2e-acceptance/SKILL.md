---
name: e2e-acceptance
description: |
  E2E无头验收。
  注意：此 skill 由 acceptance-workflow 内部调用，不应单独使用。
  执行Dev和User无头验收，失败时使用MCP Playwright诊断页面布局。
---

# E2E 无头验收流程

## 触发条件

- 由 acceptance-workflow skill 内部调用
- 静态检查、单元测试、集成测试已通过

---

## 执行流程

### 1. Dev 无头验收（降级策略）

```bash
# 步骤 1：尝试 rscore
rscore --dev --headless

# 步骤 2：失败则降级
python main.py --dev --headless
```

### 2. User 无头验收（降级策略）

```bash
# 步骤 1：尝试 rscore
rscore --user --headless

# 步骤 2：失败则降级
python main.py --user --headless
```

---

## rscore 与 python main.py 降级策略

### 问题形式分析

#### rscore 可能的问题

| 问题类型 | 错误特征 | 原因 |
|----------|----------|------|
| **命令不存在** | `command not found: rscore` | 包未安装（`pip install -e .` 未执行） |
| **模块找不到** | `ModuleNotFoundError: No module named 'cli'` | `pyproject.toml` 入口点配置错误 |
| **入口点包装失败** | 其他异常但 python main.py 正常 | 入口点包装器失效 |
| **业务逻辑错误** | Timeout/Assertion/业务异常 | 代码逻辑问题 |

#### python main.py 可能的问题

| 问题类型 | 错误特征 | 原因 |
|----------|----------|------|
| **依赖缺失** | `ModuleNotFoundError: No module named 'xxx'` | 核心依赖未安装 |
| **业务逻辑错误** | Timeout/Assertion/业务异常 | 代码逻辑问题 |

### 降级流程

```
rscore --dev --headless
    │
    ├─ ✅ 成功（Exit 0） → 继续 User 验收
    │
    └─ ❌ 失败 → python main.py --dev --headless
                    │
                    ├─ ✅ 成功 → rscore 入口问题（配置问题）
                    │
                    └─ ❌ 失败 → 业务逻辑问题或环境问题
```

### 二维诊断矩阵

| rscore 结果 | python main.py 结果 | 诊断结论 | Agent 动作 |
|-------------|---------------------|----------|------------|
| ✅ 成功（Exit 0） | - | 验证通过 | 继续 User 验收 |
| ❌ `command not found` | ✅ 成功 | 包未安装 | 报告用户：执行 `pip install -e .` |
| ❌ `ModuleNotFoundError: cli` | 任意 | 入口点配置错误 | 报告用户：检查 `pyproject.toml` |
| ❌ 任意异常 | ✅ 成功 | 入口点包装器失效 | 报告用户：检查 CLI 入口配置 |
| 任意 | ❌ `ModuleNotFoundError` | 核心依赖缺失 | 报告用户：执行 `pip install -e ".[dev]"` |
| ❌ 业务逻辑错误 | ❌ 业务逻辑错误 | 代码逻辑问题 | MCP Playwright 诊断页面布局 |

---

## MCP Playwright 能力边界

### ✅ 能做到的

| 能力 | 说明 |
|------|------|
| 导航任意URL | 可以访问任何网页 |
| 截图/获取内容 | 可以获取页面布局、文本、HTML |
| 有头模式 | `headless: false` 让用户手动登录 |
| 执行JS | 可以在页面中执行脚本 |

### ❌ 做不到的

| 限制 | 原因 |
|------|------|
| 监控脚本执行 | MCP 无法连接项目启动的浏览器进程 |
| 加载项目的 `storage_state.json` | MCP 工具未暴露此参数 |
| 自动继承项目的登录状态 | 完全独立的浏览器实例 |

### 实际用途

**E2E 验收期间**：Agent 执行脚本命令，脚本自己运行（Agent 不监控）

**E2E 失败后**：Agent 可以用 MCP Playwright 导航到页面，获取页面布局来诊断问题

---

## 失败诊断（MCP Playwright）

**触发条件**：rscore 和 python main.py 都失败，且为业务逻辑错误

**执行方式**：

```javascript
// 1. 导航到目标页面
playwright_navigate(url="https://rewards.microsoft.com")

// 2. 获取页面布局
playwright_get_visible_text()
playwright_get_visible_html()

// 3. 截图
playwright_screenshot()

// 4. 关闭
playwright_close()
```

**注意**：MCP Playwright 无法继承项目的登录状态，如需登录页面需使用有头模式让用户手动登录。

---

## 精简取证规范

**严禁保存完整 HTML**，仅提取以下三项：

### 1. Traceback（最后 10 行）

```
<最后抛出异常的 10 行 Traceback>
```

### 2. 关键 DOM 节点

仅提取与异常相关的 DOM 节点，不保存完整页面。

### 3. Network 请求（最后 3 个）

| URL | 状态码 | 方法 |
|-----|--------|------|
| <URL> | <状态码> | <GET/POST/...> |

---

## 进程安全

- 截图后必须调用 `playwright_close` 关闭页面
- 防止无头浏览器进程残留

---

## 输出格式

### 成功

```
✅ Dev 无头验收通过
✅ User 无头验收通过
```

### 失败

```
❌ Dev 无头验收失败

### 诊断结论
<根据二维诊断矩阵得出的结论>

### Traceback（最后 10 行）
```

<Traceback>
```

### 页面布局诊断（如适用）

<通过 MCP Playwright 获取的页面信息>

```
