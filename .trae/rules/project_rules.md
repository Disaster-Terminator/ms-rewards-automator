# 项目规则

---

## Skill 触发（必须调用）

| 用户说 | 调用 Skill |
|--------|-----------|
| "处理评论"、"解决评论"、"PR 评论" | review-workflow |
| "验收"、"测试"、"开发完成" | acceptance-workflow |
| "获取评论"、"查看评论" | fetch-reviews |
| "解决某个评论" | resolve-review-comment |
| "申请新审查"、"重新审查" | request-reviews |

**强制调用检查**：当用户请求包含上述关键词时，Agent **必须**首先调用对应 Skill。

---

## 执行约束

**Agent 在执行 Skill 时必须遵循以下规则**：

1. **完整性检查**：Skill 中列出的所有阶段必须执行，不可跳过
2. **顺序检查**：必须按 Skill 定义的顺序执行
3. **失败处理**：某个阶段失败时，必须停止并报告，不可跳过继续
4. **完成确认**：所有阶段完成后，必须输出完整性检查结果

**违反以上规则的输出将被视为无效。**

---

## 工作流协调规则

**Agent 必须遵循以下工作流协调规则**：

1. **评论处理后必须验收**：处理 PR 评论并修改代码后，**必须**调用 `acceptance-workflow` 验收
2. **验收通过后必须解决评论**：验收通过后，**必须**调用 CLI 解决评论
3. **不可直接运行 pytest**：验收**必须**调用 `acceptance-workflow`，不可直接运行 pytest
4. **验收前检查评论状态**：如果有"必须修复"的评论未处理，**建议**先处理评论

---

## pytest 执行规范

**优先使用并行测试**：Agent 必须先检查 xdist 可用性：

```bash
python -c "import xdist" 2>$null; if ($LASTEXITCODE -eq 0) { echo "xdist_available" } else { echo "xdist_missing" }
```

| 环境状态 | 执行命令 |
|----------|----------|
| xdist 可用 | `pytest tests/unit/ -n auto -v` |
| xdist 不可用 | `pytest tests/unit/ -v` |

---

## 熔断机制

| 条件 | 动作 |
|------|------|
| 连续 2 次验收失败 | 停止执行，等待人类干预 |
| 连续 3 次验证失败 | 停止执行，向用户报告 |
| 依赖缺失 | 停止执行，不自行安装 |

---

## 最佳实践

- DOM 选择器从实际页面获取，不凭猜测
- 保存 HTML 时仅保留精简取证内容
- E2E 测试结束后及时关闭 Playwright 页面
