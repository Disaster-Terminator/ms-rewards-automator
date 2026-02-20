# 分支管理指南

## 一、分支结构

```
main                          # 核心分支：登录 + 搜索（必须稳定）
├── feature/xxx               # 功能分支
├── fix/xxx                   # Bug修复分支
├── hotfix/xxx                # 紧急修复分支
└── integration/xxx           # 临时集成分支
```

## 二、分支职责

### 2.1 main 分支

**目标**：保持稳定，只包含核心功能

| 功能模块 | 目录 | 状态 |
|----------|------|------|
| 登录系统 | `src/login/` | ✅ 核心 |
| 搜索系统 | `src/search/` | ✅ 核心 |
| 浏览器控制 | `src/browser/` | ✅ 核心 |
| 账户管理 | `src/account/` | ✅ 核心 |

**配置禁用的功能**：

```yaml
task_system.enabled: false
notification.enabled: false
scheduler.enabled: false
bing_theme.enabled: false
```

### 2.2 功能分支命名

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feature/` | 新功能 | `feature/daily-tasks` |
| `fix/` | Bug修复 | `fix/login-timeout` |
| `hotfix/` | 紧急修复 | `hotfix/crash` |
| `integration/` | 多分支集成 | `integration/temp` |

## 三、开发工作流

### ⚠️ 核心规则：所有合并必须通过 PR

```
❌ 禁止：git checkout main && git merge feature/xxx
✅ 正确：创建 Pull Request 通过 GitHub 合并
```

### 3.1 新功能开发

```bash
# 1. 从 main 创建功能分支
git checkout main && git pull
git checkout -b feature/new-feature

# 2. 开发并提交
git add . && git commit -m "feat: 功能描述"

# 3. 推送并运行验收测试
git push origin feature/new-feature

# 4. 测试通过后创建 PR
gh pr create --base main --head feature/new-feature
```

### 3.2 Bug 修复

```bash
git checkout main && git pull
git checkout -b fix/bug-description
# ... 修复 ...
git add . && git commit -m "fix: 问题描述"
git push origin fix/bug-description
gh pr create --base main --head fix/bug-description
```

## 四、验收标准

> **详细验收流程**：[MCP_WORKFLOW.md](./MCP_WORKFLOW.md)

### 8 阶段验收概览

```
阶段 1-3: CI 自动化（静态检查 → 单元测试 → 集成测试）
阶段 4-6: MCP 验收（Dev无头 → User无头 → 有头）
阶段 7-8: PR 管理（创建PR → 合并确认）
```

### 测试类型

| 类型 | 目录 | 运行方式 |
|------|------|----------|
| 单元测试 | `tests/unit/` | `pytest tests/unit/ -m "not real"` |
| 集成测试 | `tests/integration/` | `pytest tests/integration/` |
| 功能验证 | CLI | `rscore --dev/--user` |

## 五、命令行参数

| 参数 | 搜索次数 | 调度器 | 用途 |
|------|----------|--------|------|
| 默认 | 20 | ✅ 启用 | 生产环境 |
| `--user` | 3 | ❌ 禁用 | 稳定性测试 |
| `--dev` | 2 | ❌ 禁用 | 快速调试 |
| `--headless` | - | - | 无头模式 |

## 六、常用 Git 命令

```bash
git branch -a                    # 查看分支
git checkout -b <branch>         # 创建并切换
git push origin <branch>         # 推送分支
gh pr create --base main         # 创建 PR
git log --oneline --graph --all  # 查看历史
```

## 七、注意事项

1. **main 必须稳定**：合并前通过 8 阶段验收
2. **功能分支独立**：避免交叉依赖
3. **配置禁用优于代码删除**：保留代码，配置控制
4. **严禁本地合并**：必须通过 PR
5. **MCP 工具优先**：验收时使用 MCP 直接验证

---

*最后更新：2026-02-21*
