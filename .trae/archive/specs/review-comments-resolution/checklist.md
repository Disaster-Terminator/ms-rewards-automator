# Checklist

## resolve-review-comment skill

- [x] SKILL.md 文件存在于 `.trae/skills/resolve-review-comment/` 目录
- [x] 定义了 comment_id 输入参数
- [x] 定义了 comment_url 输入参数
- [x] 定义了 resolution_type 输入参数（枚举：code_fixed/adopted/rejected/false_positive/outdated）
- [x] 定义了 reply_content 输入参数（条件必需）
- [x] 定义了 Playwright 导航流程
- [x] 定义了回复流程（rejected/false_positive 时）
- [x] 定义了解决按钮点击流程
- [x] 定义了验证解决状态的流程
- [x] 定义了输出格式（success, resolution_type, reply_posted）

## fetch-reviews skill 修改

- [x] 返回 comment_id 字段
- [x] 返回 comment_url 字段
- [x] 返回 resolution_status 字段（pending/resolved）
- [x] 返回 resolution_type 字段（已解决评论）

## acceptance-workflow skill 修改

- [x] 阶段 3.5 包含自动标记解决逻辑
- [x] 对已修复但未标记解决的评论调用 resolve-review-comment skill
- [x] 输出解决结果统计

## ai-reviewer-guide skill 修改

- [x] 包含解决依据类型定义表
- [x] 包含何时需要回复说明的规则
- [x] 包含严禁事项列表

## 规范完整性

- [x] 严禁一次性解决所有评论
- [x] 严禁无依据标记解决
- [x] 严禁批量操作
- [x] 严禁跳过说明评论
