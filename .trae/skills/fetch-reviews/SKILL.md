---
name: fetch-reviews
description: 获取PR的AI审查评论。解析Sourcery/Copilot/Qodo评论并汇总未解决问题。
---

# AI 审查获取流程

## 触发条件

- 用户请求获取审查评论
- 用户请求查看PR状态
- 推送前检查

## 获取流程

### 步骤 1：GitHub MCP 获取评论

```
get_pull_request_reviews(owner, repo, pull_number)
get_pull_request_comments(owner, repo, pull_number)
get_pull_request_status(owner, repo, pull_number)
```

**Sourcery 数据提取**：

- 从 `reviews.body` 提取 "Prompt for AI Agents" 中的问题列表
- 从 `comments.body` 提取解决状态（`✅ Addressed`）

**注意**：GitHub API 对 Qodo 评论会截断。

### 步骤 2：Playwright MCP 获取 Qodo 完整评论

**必须使用 Playwright**，因为 GitHub API 会截断 Qodo 评论。

```javascript
// 1. 无头模式导航
playwright_navigate(url="https://github.com/{owner}/{repo}/pull/{number}", headless=true)

// 2. 点击 "View more" 展开所有问题
playwright_click(selector='summary:has-text("View more")')

// 3. 提取 Code Review by Qodo 评论
playwright_evaluate(script=`
(function() {
  let allMarkdown = document.querySelectorAll('.markdown-body');
  let fullContent = '';
  allMarkdown.forEach(el => {
    let text = el.innerText;
    if (text.includes('Code Review by Qodo') && text.includes('Bugs')) {
      fullContent = text;
    }
  });
  return fullContent;
})()
`)

// 4. 提取 PR Reviewer Guide 评论
playwright_evaluate(script=`
(function() {
  let allMarkdown = document.querySelectorAll('.markdown-body');
  let guideContent = '';
  allMarkdown.forEach(el => {
    let text = el.innerText;
    if (text.includes('PR Reviewer Guide') && text.includes('Estimated effort')) {
      guideContent = text;
    }
  });
  return guideContent;
})()
`)

// 5. 关闭浏览器
playwright_close()
```

### 步骤 3：解析评论类型

详见 `ai-reviewer-guide` skill。

**快速参考**：

| 来源 | 已解决标志 |
|------|-----------|
| Sourcery | `✅ Addressed in {commit}` |
| Qodo (Code Review) | `☑ ☑ ☑ ☑ ☑`（5个勾） |
| Qodo (PR Reviewer Guide) | 不包含具体问题，只是审查指南 |
| Copilot | 无 |

---

## 输出格式

### 审查评论处理表（必须输出）

```markdown
## 审查评论处理表

### 审查指南（Qodo PR Reviewer Guide）

| 项目 | 内容 |
|------|------|
| 审查工作量 | X/5 |
| 测试覆盖 | ✅/❌ |
| 安全问题 | 有/无 |
| 关注重点 | ... |

### 必须修复

| ID | 来源 | 类型 | 文件 | 行号 | 描述 | 状态 |
|----|------|------|------|------|------|------|
| #1 | Sourcery | bug_risk | xxx.py | 42 | ... | 待处理 |
| #2 | Qodo | Security | yyy.py | 15 | ... | 待处理 |

### 建议性评论

| ID | 来源 | 类型 | 文件 | 描述 | 状态 |
|----|------|------|------|------|------|
| #3 | Sourcery | suggestion | xxx.py | ... | 待判断 |
| #4 | Copilot | suggestion | yyy.py | ... | 待判断 |

### 已解决

| ID | 来源 | 文件 | 状态 |
|----|------|------|------|
| #5 | Sourcery | xxx.py | ✅ Addressed |
| #6 | Qodo | yyy.py | ☑ |
```

---

## 状态定义

| 状态 | 含义 | 可推送？ |
|------|------|----------|
| 待处理 | 必须修复项，未处理 | ❌ 禁止推送 |
| 待判断 | 建议性，需决定是否采纳 | ⚠️ 需确认 |
| 已忽略 | 建议性，决定不采纳 | ✅ 可推送 |
| 已解决 | 已修复或已确认解决 | ✅ 可推送 |

---

## 推送前检查

**调用时机**：准备推送代码前

**检查逻辑**：

```
1. 统计各状态数量
2. 如果有"待处理"状态 → 停止推送，报告用户
3. 如果有"待判断"状态 → 提示用户确认
4. 如果全部是"已解决"或"已忽略" → 允许推送
```

**输出**：

```
✅ 推送检查通过
- 必须修复：0 待处理
- 建议性：2 已忽略，0 待判断
- 已解决：3

或

❌ 推送检查失败
- 必须修复：2 待处理
- 请先处理上述问题
```

---

## 处理建议

| 评论类型 | Agent 行为 |
|----------|------------|
| `bug_risk`, `Bug`, `Security`, `Rule violation`, `Reliability` | 报告给用户，等待修复指令 |
| `suggestion`, `performance`, `Correctness` | 报告给用户，自主决断是否采纳 |
| PR Reviewer Guide | 直接报告给用户 |

## 合并提醒

- **Agent 不自动合并 PR**，需通知用户确认
- 详细命令参考见 `ai-reviewer-guide` skill
