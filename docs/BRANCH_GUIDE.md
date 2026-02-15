# 分支管理开发指南

## 一、分支结构

```
main                          # 核心分支：登录 + 搜索（必须稳定）
├── feature/daily-tasks       # 每日任务系统（问答、投票、URL奖励）
├── feature/theme-management  # Bing主题管理
├── feature/health-monitor    # 健康监控与自诊断
├── feature/notifications     # 通知系统
├── dev                       # 开发集成分支（合并测试）
└── backup-before-cleanup-*   # 备份分支
```

## 二、分支职责

### 2.1 main 分支（核心）

**目标**：保持稳定，只包含核心功能

| 功能模块 | 目录 | 状态 |
|----------|------|------|
| 登录系统 | `src/login/` | ✅ 核心保留 |
| 搜索系统 | `src/search/` | ✅ 核心保留 |
| 浏览器控制 | `src/browser/` | ✅ 核心保留 |
| 账户管理 | `src/account/` | ✅ 核心保留 |
| 基础设施 | `src/infrastructure/` | ✅ 部分保留 |

**配置禁用的功能**：
```yaml
task_system.enabled: false      # 每日任务
notification.enabled: false     # 通知
scheduler.enabled: false        # 调度器
bing_theme.enabled: false       # 主题管理
monitoring.health_check.enabled: false  # 健康监控
```

### 2.2 功能分支

| 分支 | 功能 | 包含文件 |
|------|------|----------|
| `feature/daily-tasks` | 每日任务 | `src/tasks/` |
| `feature/theme-management` | 主题管理 | `src/ui/bing_theme_manager.py` |
| `feature/health-monitor` | 健康监控 | `src/infrastructure/health_monitor.py`, `self_diagnosis.py` |
| `feature/notifications` | 通知系统 | `src/infrastructure/notificator.py` |

### 2.3 dev 分支

开发集成分支，用于：
- 合并各功能分支进行集成测试
- 验证功能间的兼容性
- 通过测试后再合并到 main

## 三、开发工作流

### 3.1 新功能开发

```bash
# 1. 从 main 创建功能分支
git checkout main
git pull origin main
git checkout -b feature/new-feature

# 2. 开发功能
# ... 编写代码 ...

# 3. 提交更改
git add .
git commit -m "feat: 添加新功能描述"

# 4. 合并到 dev 进行集成测试
git checkout dev
git merge feature/new-feature

# 5. 运行测试
pytest tests/

# 6. 测试通过后合并到 main
git checkout main
git merge dev

# 7. 推送到远程
git push origin main
```

### 3.2 Bug 修复

```bash
# 1. 从 main 创建修复分支
git checkout main
git checkout -b fix/bug-description

# 2. 修复 bug
# ... 修改代码 ...

# 3. 提交并合并
git add .
git commit -m "fix: 修复问题描述"
git checkout main
git merge fix/bug-description

# 4. 删除修复分支
git branch -d fix/bug-description
```

### 3.3 紧急修复

```bash
# 直接在 main 上修复
git checkout main
# ... 修复 ...
git add .
git commit -m "hotfix: 紧急修复描述"
git push origin main
```

## 四、测试验证

### 4.1 main 分支验证命令

```bash
# 开发模式（2+2搜索，无拟人行为，最小等待时间，DEBUG日志）
python main.py --dev

# 测试模式（3+3搜索，保留拟人行为和防检测，INFO日志）
python main.py --usermode

# 生产环境（30+20搜索，完整功能）
python main.py

# 仅测试登录
python main.py --dev --desktop-only --dry-run
```

### 4.2 模式对比

| 模式 | 桌面搜索 | 移动搜索 | 拟人行为 | 防检测 | 日志级别 | 用途 |
|------|----------|----------|----------|--------|----------|------|
| `--dev` | 2 | 2 | ❌ 禁用 | ❌ 禁用 | DEBUG | 快速迭代调试 |
| `--usermode` | 3 | 3 | ✅ 启用 | ✅ 启用 | INFO | 稳定性测试 |
| 默认 | 30 | 20 | ✅ 启用 | ✅ 启用 | INFO | **生产环境** |

### 4.3 功能分支验证

```bash
# 切换到功能分支
git checkout feature/daily-tasks

# 启用对应功能配置
# 修改 config.yaml 中 task_system.enabled: true

# 运行测试
python main.py --dev
pytest tests/unit/test_task_manager.py
```

## 五、配置管理

### 5.1 main 分支配置（config.yaml）

```yaml
# 核心功能
search:
  desktop_count: 30
  mobile_count: 20
  wait_interval: 5

browser:
  headless: false
  type: "chromium"

login:
  auto_login:
    enabled: false

# 禁用非核心功能
task_system:
  enabled: false

notification:
  enabled: false

scheduler:
  enabled: false

bing_theme:
  enabled: false

monitoring:
  health_check:
    enabled: false
```

### 5.2 功能分支配置示例

```yaml
# feature/daily-tasks 分支
task_system:
  enabled: true
  debug_mode: true

# feature/notifications 分支
notification:
  enabled: true
  telegram:
    bot_token: "your_token"
    chat_id: "your_chat_id"
```

## 六、依赖关系图

```
main 分支核心依赖：
┌─────────────────────────────────────────────────────────────┐
│                      MSRewardsApp                           │
│                     (应用主控制器)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   登录系统   │   │   搜索系统   │   │   浏览器    │
│  (login/)   │   │  (search/)  │   │ (browser/)  │
└─────────────┘   └─────────────┘   └─────────────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │     账户管理         │
              │   (account/)        │
              └─────────────────────┘

功能分支依赖（可选）：
┌─────────────────┐   ┌─────────────────┐
│   任务系统       │   │   通知系统       │
│  (tasks/)       │   │ (notificator)   │
└─────────────────┘   └─────────────────┘
```

## 七、版本发布流程

1. **开发阶段**：在功能分支开发
2. **集成阶段**：合并到 dev 分支测试
3. **预发布阶段**：在 dev 分支进行完整测试
4. **发布阶段**：合并到 main，打 tag
5. **维护阶段**：在 main 上进行 bug 修复

## 八、常用 Git 命令

```bash
# 查看分支
git branch -a

# 切换分支
git checkout <branch>

# 创建并切换
git checkout -b <new-branch>

# 合并分支
git merge <branch>

# 删除分支
git branch -d <branch>

# 查看差异
git diff main..feature/xxx

# 暂存工作
git stash
git stash pop

# 查看历史
git log --oneline --graph --all
```

## 九、注意事项

1. **main 分支必须保持稳定**：任何合并前必须通过测试
2. **功能分支独立开发**：避免功能间的交叉依赖
3. **配置禁用优于代码删除**：保留代码，通过配置控制
4. **测试先行**：合并前必须运行测试
5. **文档同步**：功能变更时更新本文档
