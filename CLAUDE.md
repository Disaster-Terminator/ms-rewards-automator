# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Microsoft Rewards 自动化工具，基于 Playwright 实现浏览器自动化，完成每日搜索和任务以获取积分。

**核心技术栈**：Python 3.10+, async/await, Playwright 1.49+, playwright-stealth, pydantic 2.9+

**项目规模**：86 个 Python 源文件，64 个测试文件，完整的类型注解和严格 lint 规则

**最新重大重构**：2026-03-06 完成 BingThemeManager 重写（3077行 → 75行），删除巨型类并引入简洁实现

## 常用命令

### 开发环境设置
```bash
# 安装依赖（开发环境 - 包含测试、lint、viz工具）
pip install -e ".[dev]"

# 生产环境（仅运行所需）
pip install -e .

# 安装 Chromium 浏览器（首次）
playwright install chromium

# 验证环境
python tools/check_environment.py

# 启用 rscore 命令
pip install -e .
```

### 代码质量
```bash
# 完整检查（lint + 格式化检查）
ruff check . && ruff format --check .

# 修复问题
ruff check . --fix
ruff format .

# 类型检查
mypy src/

# 预提交钩子测试
pre-commit run --all-files
```

### 测试（优先级顺序）
```bash
# 快速单元测试（推荐日常开发）
pytest tests/unit/ -v --tb=short -m "not real and not slow"

# 完整单元测试（包含慢测试）
pytest tests/unit/ -v --tb=short -m "not real"

# 仅真实浏览器测试（需要凭证）
pytest tests/unit/ -v -m "real"

# 集成测试
pytest tests/integration/ -v --tb=short

# 特定测试文件
pytest tests/unit/test_login_state_machine.py -v

# 特定测试函数
pytest tests/unit/test_login_state_machine.py::TestLoginStateMachine::test_initial_state -v

# 属性测试（hypothesis）
pytest tests/ -v -m "property"

# 性能基准测试
pytest tests/ -v -m "performance"

# 带覆盖率
pytest tests/unit/ -v --cov=src --cov-report=html --cov-report=term

# 并行测试（4 worker）
pytest tests/unit/ -v -n 4

# 显示最后失败的测试
pytest --last-failed

# 失败重启测试
pytest --failed-first
```

### 运行应用
```bash
# 生产环境（20次搜索，启用调度器）
rscore

# 用户测试模式（3次搜索，稳定性验证）
rscore --user

# 开发模式（2次搜索，快速调试）
rscore --dev

# 无头模式（后台运行）
rscore --headless

# 组合使用
rscore --dev --headless
rscore --user --headless

# 仅桌面搜索
rscore --desktop-only

# 跳过搜索，仅测试任务系统
rscore --skip-search

# 跳过日常任务
rscore --skip-daily-tasks

# 模拟运行（不执行实际操作）
rscore --dry-run

# 测试通知功能
rscore --test-notification

# 使用特定浏览器
rscore --browser chrome
rscore --browser edge

# 指定配置文件
rscore --config custom_config.yaml

# 强制禁用诊断模式（默认 dev/user 启用）
rscore --dev --no-diagnose
```

### 日志查看

```bash
# 查看实时日志
tail -f logs/automator.log

# 查看诊断报告
ls logs/diagnosis/

# 查看主题状态
cat logs/theme_state.json
```

### 辅助操作
```bash
# 清理旧日志和截图（自动在程序结束时运行）
python -c "from infrastructure.log_rotation import LogRotation; LogRotation().cleanup_all()"

# 验证配置文件
python -c "from infrastructure.config_validator import ConfigValidator; from infrastructure.config_manager import ConfigManager; cm = ConfigManager('config.yaml'); v = ConfigValidator(cm.config); print(v.get_validation_report())"
```

## 代码风格规范

### 必须遵守
- **Python 3.10+**：使用现代 Python 特性（模式匹配、结构化模式等）
- **类型注解**：所有函数必须有类型注解（`py.typed` 已配置）
- **async/await**：异步函数必须使用 async/await，禁止使用 `@asyncio.coroutine`
- **line-length = 100**：行长度不超过 100 字符（ruff 配置）
- **双引号**：字符串使用双引号（ruff format 强制）
- **2个空格缩进**：统一使用空格缩进

### Lint 规则（ruff 配置）
项目使用 ruff，启用的规则集：
- **E, W**：pycodestyle 错误和警告（PEP 8）
- **F**：Pyflakes（未使用变量、导入等）
- **I**：isort（导入排序）
- **B**：flake8-bugbear（常见 bug 检测）
- **C4**：flake8-comprehensions（列表/字典推导式优化）
- **UP**：pyupgrade（升级到现代 Python 语法）

### 忽略规则
```toml
ignore = [
    "E501",      # 行长度（我们使用 100 而非 79）
    "B008",      # 函数调用中的可变参数（有时需要）
    "C901",      # 函数复杂度（暂时允许复杂函数）
]
```

### mypy 配置
- `python_version = 3.10`
- `warn_return_any = true`
- `warn_unused_configs = true`
- `ignore_missing_imports = true`（第三方库类型Optional）

## 架构概览

### 核心设计原则
1. **单一职责**：每个模块只做一件事
2. **依赖注入**：TaskCoordinator 通过构造函数和 set_* 方法接收依赖
3. **状态机模式**：登录流程使用状态机管理复杂步骤（15+ 状态）
4. **策略模式**：搜索词生成支持多种源（本地文件、DuckDuckGo、Wikipedia、Bing）
5. **门面模式**：MSRewardsApp 封装子系统交互，提供统一接口
6. **组合模式**：任务系统支持不同类型的任务处理器（URL、Quiz、Poll）
7. **观察者模式**：StatusManager 实时更新进度，UI 层可订阅
8. **异步优先**：全面使用 async/await
9. **容错设计**：优雅降级和诊断模式

### 模块层次（86 个源文件，64 个测试文件）

```
src/
├── cli.py                      # CLI 入口（argparse 解析 + 信号处理）
├── __init__.py
│
├── infrastructure/             # 基础设施层（13个文件）
│   ├── ms_rewards_app.py      # ★ 主控制器（门面模式，8步执行流程）
│   ├── task_coordinator.py    # ★ 任务协调器（依赖注入）
│   ├── system_initializer.py  # 组件初始化器
│   ├── config_manager.py      # 配置管理（环境变量覆盖）
│   ├── config_validator.py    # 配置验证与自动修复
│   ├── state_monitor.py       # 状态监控（积分追踪、报告生成）
│   ├── health_monitor.py      # 健康监控（性能指标、错误率）
│   ├── scheduler.py           # 任务调度（定时/随机执行）
│   ├── notificator.py         # 通知系统（Telegram/Server酱）
│   ├── logger.py              # 日志配置（轮替、结构化）
│   ├── error_handler.py       # 错误处理（重试、降级）
│   ├── log_rotation.py        # 日志轮替（自动清理）
│   ├── self_diagnosis.py      # 自诊断系统
│   ├── protocols.py           # 协议定义（Strategy、Monitor等）
│   └── models.py              # 数据模型
│
├── browser/                    # 浏览器层（7个文件）
│   ├── simulator.py           # 浏览器模拟器（桌面/移动上下文管理）
│   ├── anti_ban_module.py     # 反检测模块（特征隐藏、随机化）
│   ├── popup_handler.py       # 弹窗处理（自动关闭广告）
│   ├── page_utils.py          # 页面工具（临时���、等待策略）
│   ├── element_detector.py    # 元素检测（智能等待）
│   ├── state_manager.py       # 浏览器状态管理
│   └── anti_focus_scripts.py  # 反聚焦脚本
│
├── login/                      # 登录系统（13个文件）
│   ├── login_state_machine.py # ★ 状态机（15+ 状态转换）
│   ├── login_detector.py      # 登录页面检测
│   ├── human_behavior_simulator.py  # 拟人化行为（鼠标、键盘）
│   ├── edge_popup_handler.py  # Edge 特有弹窗处理
│   ├── state_handler.py       # 状态处理器基类
│   └── handlers/              # 具体处理器（10个文件）
│       ├── email_input_handler.py
│       ├── password_input_handler.py
│       ├── otp_code_entry_handler.py
│       ├── totp_2fa_handler.py
│       ├── get_a_code_handler.py
│       ├── recovery_email_handler.py
│       ├── passwordless_handler.py
│       ├── auth_blocked_handler.py
│       ├── logged_in_handler.py
│       └── stay_signed_in_handler.py
│
├── search/                     # 搜索系统（10+ 文件）
│   ├── search_engine.py       # ★ 搜索引擎（执行搜索、轮换标签）
│   ├── search_term_generator.py  # 搜索词生成器
│   ├── query_engine.py        # 查询引擎（多源聚合）
│   ├── bing_api_client.py     # Bing API 客户端
│   └── query_sources/         # 查询源（策略模式）
│       ├── query_source.py    # 基类
│       ├── local_file_source.py
│       ├── duckduckgo_source.py
│       ├── wikipedia_source.py
│       └── bing_suggestions_source.py
│
├── account/                    # 账户管理（2个文件）
│   ├── manager.py             # ★ 账户管理器（会话、登录状态）
│   └── points_detector.py     # 积分检测器（DOM 解析）
│
├── tasks/                      # 任务系统（7个文件）
│   ├── task_manager.py        # ★ 任务管理器（发现、执行、过滤）
│   ├── task_parser.py         # 任务解析器（DOM 分析）
│   ├── task_base.py           # 任务基类（ABC）
│   └── handlers/              # 任务处理器
│       ├── url_reward_task.py # URL 奖励任务
│       ├── quiz_task.py       # 问答任务
│       └── poll_task.py       # 投票任务
│
├── ui/                        # 用户界面（3个文件）
│   ├── real_time_status.py   # 实时状态管理器（进度条、徽章）
│   ├── tab_manager.py        # 标签页管理
│   └── cookie_handler.py     # Cookie 处理
│
├── diagnosis/                 # 诊断系统（5个文件）
│   ├── engine.py             # 诊断引擎（页面检查）
│   ├── inspector.py          # 页面检查器（DOM/JS/网络）
│   ├── reporter.py           # 诊断报告生成器
│   ├── rotation.py           # 诊断日志轮替
│   └── screenshot.py         # 智能截图
│
├── constants/                 # 常量定义（2个文件）
│   ├── urls.py               # ★ URL 常量集中管理（Bing、MS 账户等）
│   └── __init__.py
│
└── review/                    # PR 审查工作流（6个文件）
    ├── graphql_client.py     # GraphQL 客户端（GitHub API）
    ├── comment_manager.py    # 评论管理器（解析、回复）
    ├── parsers.py            # 评论解析器
    ├── resolver.py           # 评论解决器
    └── models.py             # 数据模型

tests/
├── conftest.py                # 全局 pytest 配置
├── fixtures/                  # 测试固件（Mock 数据）
├── unit/                      # 单元测试（推荐日常）
├── integration/               # 集成测试
└── manual/                    # 手动测试清单

tools/
├── check_environment.py       # 环境验证
└── search_terms.txt          # 搜索词库

docs/
├── guides/                   # 用户指南
├── reports/                  # 技术报告
└── reference/
    └── WORKFLOW.md           # 开发工作流（MCP + Skills）
```

### 核心组件协作关系

```
┌─────────────────────────────────────────────────────────────┐
│                     MSRewardsApp (主控制器)                  │
│                    Facade Pattern (门面)                    │
├─────────────────────────────────────────────────────────────┤
│ 执行流程（8步）：                                            │
│  1. 初始化组件      → SystemInitializer                     │
│  2. 创建浏览器      → BrowserSimulator                      │
│  3. 处理登录        → TaskCoordinator.handle_login()        │
│  4. 检查初始积分    → StateMonitor                          │
│  5. 执行桌面搜索    → SearchEngine.execute_desktop_searches │
│  6. 执行移动搜索    → SearchEngine.execute_mobile_searches  │
│  7. 执行日常任务    → TaskManager.execute_tasks()           │
│  8. 生成报告        → StateMonitor + Notificator            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ 依赖注入
┌─────────────────────────────────────────────────────────────┐
│              TaskCoordinator (任务协调器)                    │
│              Strategy Pattern (策略)                        │
├─────────────────────────────────────────────────────────────┤
│   AccountManager ────────┐                                  │
│   SearchEngine ──────────┤                                  │
│   StateMonitor ──────────┤                                  │
│   HealthMonitor ─────────┤   各组件通过 set_* 方法注入     │
│   BrowserSimulator ──────┘                                  │
│                                                              │
│   handle_login()                                            │
│   execute_desktop_search()                                  │
│   execute_mobile_search()                                   │
│   execute_daily_tasks()                                     │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ 登录系统       │  │ 搜索系统       │  │ 任务系统       │
│ State Machine │  │ Strategy       │  │ Composite     │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ 10+ 处理器     │  │ 4种查询源      │  │ 3种任务处理器  │
│ 状态检测       │  │ QueryEngine    │  │ TaskParser     │
└───────────────┘  └───────────────┘  └───────────────┘
```

### 核心组件职责

| 组件 | 职责 | 关键方法 | 依赖注入目标 |
|------|------|----------|-------------|
| **MSRewardsApp** | 主控制器，协调整个生命周期 | `run()`, `_init_components()`, `_cleanup()` | 无（顶层） |
| **TaskCoordinator** | 任务协调，登录+搜索+任务 | `handle_login()`, `execute_*_search()`, `execute_daily_tasks()` | 接收所有子系统 |
| **SystemInitializer** | 组件创建与配置 | `initialize_components()` | MSRewardsApp |
| **BrowserSimulator** | 浏览器生命周期管理 | `create_desktop_browser()`, `create_context()`, `close()` | TaskCoordinator |
| **SearchEngine** | 搜索执行引擎 | `execute_desktop_searches()`, `execute_mobile_searches()` | TaskCoordinator |
| **AccountManager** | 会话管理与登录状态 | `is_logged_in()`, `auto_login()`, `wait_for_manual_login()` | TaskCoordinator |
| **StateMonitor** | 积分追踪与报告 | `check_points_before_task()`, `save_daily_report()` | MSRewardsApp, SearchEngine |
| **HealthMonitor** | 性能监控与健康检查 | `start_monitoring()`, `get_health_summary()` | MSRewardsApp |
| **TaskManager** | 任务发现与执行 | `discover_tasks()`, `execute_tasks()` | TaskCoordinator |
| **Notificator** | 多通道通知 | `send_daily_report()` | MSRewardsApp |
| **LoginStateMachine** | 登录状态流控制 | `process()`, 状态转换逻辑 | AccountManager |

### 数据流向

```
ConfigManager (YAML + 环境变量)
    ├─ 读取 config.yaml
    ├─ 环境变量覆盖（MS_REWARDS_*）
    └─ 运行时参数（CLI args）

各组件通过 config.get("key.path") 读取配置

执行数据流：
StateMonitor 收集
  ├─ initial_points
  ├─ current_points
  ├─ desktop_searches (成功/失败计数)
  ├─ mobile_searches
  ├─ tasks_completed/failed
  └─ alerts (警告列表)

→ ExecutionReport
→ Notification payload
→ daily_report.json (持久化)
```

### 执行流程详解

#### MSRewardsApp.run() - 8步执行流程

```
[1/8] 初始化组件
  ├─ SystemInitializer.initialize_components()
  │   ├─ 应用 CLI 参数到配置
  │   ├─ 创建 AntiBanModule
  │   ├─ 创建 BrowserSimulator
  │   ├─ 创建 SearchTermGenerator
  │   ├─ 创建 PointsDetector
  │   ├─ 创建 AccountManager
  │   ├─ 创建 StateMonitor
  │   ├─ 创建 QueryEngine（可选）
  │   ├─ 创建 SearchEngine
  │   ├─ 创建 ErrorHandler
  │   ├─ 创建 Notificator
  │   └─ 创建 HealthMonitor
  └─ 注入 TaskCoordinator（链式调用 set_*）

[2/8] 创建浏览器
  └─ BrowserSimulator.create_desktop_browser()
     ├─ 启动 Playwright 浏览器实例
     ├─ 创建上下文（User-Agent、视口、代理等）
     └─ 注册到 HealthMonitor

[3/8] 检查登录状态
  ├─ AccountManager.session_exists()?
  │   ├─ 是 → AccountManager.is_logged_in(page)
  │   │         ├─ 是 → ✓ 已登录
  │   │         └─ 否 → _do_login()
  │   │                  ├─ auto_login（凭据+2FA自动）
  │   │                  └─ manual_login（用户手动）
  │   └─ 否 → _do_login()（同上）
  └─ AccountManager.save_session(context)

[4/8] 检查初始积分
  └─ StateMonitor.check_points_before_task(page)
     └─ 记录 initial_points，更新 StatusManager

[5/8] 执行桌面搜索 (desktop_count 次)
  └─ SearchEngine.execute_desktop_searches(page, count, health_monitor)
     ├─ 循环 count 次：
     │  ├─ SearchTermGenerator.generate() 获取搜索词
     │  ├─ page.goto(bing_search_url)
     │  │     └─ wait_until="domcontentloaded"
     │  ├─ AntiBanModule.random_delay() 随机等待
     │  ├─ PointsDetector.get_current_points() 检测积分变化
     │  └─ HealthMonitor 记录性能指标
     └─ 返回 success（全部成功才为 True）
  └─ StateMonitor.check_points_after_searches(page, "desktop")

[6/8] 执行移动搜索 (mobile_count 次)
  └─ TaskCoordinator.execute_mobile_search(page)
     ├─ 关闭桌面上下文
     ├─ 创建移动上下文（iPhone 设备模拟）
     ├─ 验证移动端登录状态
     ├─ SearchEngine.execute_mobile_searches()
     ├─ StateMonitor.check_points_after_searches(page, "mobile")
     └─ 关闭移动上下文，重建桌面上下文并返回

[7/8] 执行日常任务 (task_system.enabled)
  └─ TaskManager.execute_tasks(page)
     ├─ discover_tasks(page)  → 解析 DOM 识别任务
     ├─ 过滤已完成任务
     ├─ 获取任务前积分
     ├─ execute_tasks(page, tasks)
     │   ├─ 遍历任务（URLRewardTask/QuizTask/PollTask）
     │   ├─ 每个任务调用 handler.execute()
     │   └─ 生成 ExecutionReport
     ├─ 获取任务后积分
     ├─ 验证积分（报告值 vs 实际值）
     └─ 更新 StateMonitor.session_data

[8/8] 生成报告
  ├─ StateMonitor.save_daily_report()    → JSON 持久化
  ├─ Notificator.send_daily_report()    → 推送通知
  ├─ StateMonitor.get_account_state()
  ├─ _show_summary(state)               → 控制台摘要
  └─ LogRotation.cleanup_all()          → 清理旧日志
```

## 配置管理

### 配置文件
- **主配置文件**：`config.yaml`（从 `config.example.yaml` 复制）
- **环境变量支持**：敏感信息（密码、token）优先从环境变量读取
- **运行时覆盖**：CLI 参数（`--dev`, `--user`, `--headless`）会修改配置

### 配置优先级（从高到低）
1. CLI 参数（`--dev`, `--headless` 等）
2. 环境变量（`MS_REWARDS_EMAIL`, `MS_REWARDS_PASSWORD`, `MS_REWARDS_TOTP_SECRET`）
3. YAML 配置文件（`config.yaml`）
4. ConfigManager 默认值

### 关键配置项
```yaml
# 搜索配置
search:
  desktop_count: 20          # 桌面搜索次数
  mobile_count: 0            # 移动搜索次数（已禁用）
  wait_interval:
    min: 5
    max: 15

# 浏览器配置
browser:
  headless: false            # 首次运行建议 false
  type: "chromium"

# 登录配置
login:
  state_machine_enabled: true
  max_transitions: 20
  timeout_seconds: 300
  auto_login:
    enabled: false           # 自动登录开关
    email: ""                # 从环境变量读取更安全
    password: ""
    totp_secret: ""          # 2FA 密钥（可选）

# 调度器
scheduler:
  enabled: true
  mode: "scheduled"          # scheduled/random/fixed
  scheduled_hour: 17
  max_offset_minutes: 45

# 反检测配置
anti_detection:
  use_stealth: true
  human_behavior_level: "medium"

# 任务系统
task_system:
  enabled: false             # 默认禁用，需手动启用
  debug_mode: false          # 保存诊断数据

# 查询引擎（搜索词生成）
query_engine:
  enabled: true              # 启用多源查询引擎
  max_queries_per_source: 10 # 每个源最多生成10个查询

# 通知配置
notification:
  enabled: false
  telegram:
    enabled: false
    bot_token: ""
    chat_id: ""
  serverchan:
    enabled: false
    key: ""
```

### ConfigManager 特性
- 类型安全的配置访问：`config.get("search.desktop_count", default=20)`
- 自动应用 CLI 参数：首次运行无会话时自动 headless=false
- 环境变量覆盖：`MS_REWARDS_EMAIL` 等自动注入

## 开发工作流

### 验收流程（完整）
详见 `docs/reference/WORKFLOW.md`：

```
阶段 1: 静态检查（lint + format）
命令: ruff check . && ruff format --check .
通过: 无错误

阶段 2: 单元测试
命令: pytest tests/unit/ -v
通过: 全部通过

阶段 3: 集成测试
命令: pytest tests/integration/ -v
通过: 全部通过

阶段 4: Dev 无头验收
命令: rscore --dev --headless
通过: 退出码 0

阶段 5: User 无头验收
命令: rscore --user --headless
通过: 无严重问题
```

### MCP 工具集与 Skills 系统

#### Skills 架构
- **`review-workflow`**：PR 审查评论处理完整工作流（强制闭环）
- **`acceptance-workflow`**：代码验收完整工作流（含 E2E 测试）
- **`e2e-acceptance`**：内部 Skill，执行无头验收
- **`fetch-reviews`**：获取 AI 审查评论
- **`resolve-review-comment`**：解决单个评论

#### 工作流协调
```
用户请求："处理评论"
↓
review-workflow Skill
├── 阶段 1：获取评论（内部调用 fetch-reviews）
├── 阶段 2：分类评估
├── 阶段 3：修复代码
├── 阶段 4：验收（强制调用 acceptance-workflow）
│   └── acceptance-workflow Skill
│       ├── 前置检查：评论状态
│       ├── 阶段 1：静态检查
│       ├── 阶段 2：测试
│       ├── 阶段 3：审查评论检查
│       └── 阶段 4：E2E 验收（调用 e2e-acceptance）
├── 阶段 5：解决评论
└── 阶段 6：确认总览
```

**安全边界**：
- Agent 自主区：读取/写入文件、运行测试、浏览器操作、git add/commit/push
- 用户确认区：创建 PR、合并 PR、删除远程分支

### 工作区策略
- 使用 `/init` 进入工作区模式
- 子 Agent（dev-agent, test-agent, docs-agent）支持并行开发
- 所有变更通过 PR 流程合并

## 环境变量配置

（配置详情已在上文"配置管理"章节详述，此处仅补充环境变量）

### 环境变量参考

| 变量名 | 用途 | 优先级 |
|--------|------|--------|
| `MS_REWARDS_EMAIL` | 账户邮箱 | 高 |
| `MS_REWARDS_PASSWORD` | 账户密码 | 高 |
| `MS_REWARDS_TOTP_SECRET` | 2FA 密钥（Base32） | 高 |
| `MS_REWARDS_COUNTRY` | 账户所属国家（如 US, CN） | 中 |

推荐使用 `.env` 文件（通过 `python-dotenv` 支持）或系统环境变量。

## 重要实现细节

### 登录系统

#### 状态机架构（15+ 状态）
```python
LoginStateMachine
├─ Initial         → 初始状态
├─ CheckLogin      → 检查登录
├─ NavigateLogin   → 导航到登录页
├─ EmailInput      → 输入邮箱
├─ PasswordInput   → 输入密码
├─ TOTP2FA         → 2FA 验证
├─ GetACode        → 获取验证码（备用）
├─ RecoveryEmail   → 恢复邮箱
├─ Passwordless    → 无密码登录
├─ AuthBlocked     → 账户被锁
├─ StaySignedIn    → 保持登录
├─ LoggedIn        → 已登录（终态）
└─ Error           → 错误（终态）
```

- 每个状态对应一个 `Handler` 类（`handlers/` 目录）
- 自动检测页面元素，选择激活的 Handler
- 支持最大转换次数限制（防止无限循环）
- 会话持久化到 `storage_state.json`

#### 登录策略
1. **自动登录**：配置 `login.auto_login.enabled: true` + 凭据 + 2FA
2. **手动登录**：首次运行浏览器显示，用户手动登录后保存会话
3. **SSO 恢复**：支持通过 recovery email 恢复账户

**推荐流程**：
```bash
# 1. 首次运行（有头模式）
rscore --user
# 手动登录 → 会话保存

# 2. 后续运行（无头模式）
rscore --headless
# 自动恢复会话
```

### 反检测机制

#### 三层防护
1. **playwright-stealth**：隐藏 WebDriver 特征
   - navigator.webdriver = undefined
   - 插件列表、语言等指纹隐藏

2. **随机延迟**（AntiBanModule）
   - 搜索间隔：config.search.wait_interval.min/max（默认 5-15s）
   - 鼠标移动随机化
   - 滚动行为模拟

3. **拟人化行为**（HumanBehaviorSimulator）
   - 打字速度随机（30-100 WPM）
   - 鼠标移动轨迹（贝塞尔曲线）
   - 非精确点击（偏离目标 ±10px）

#### Headless 注意事项
- 首次登录必须使用有头模式（`headless: false`）
- 无头模式下反检测难度更高，建议先保存会话
- 使用 `--dev` 可禁用拟人行为加速调试

### 搜索词生成

#### 多源策略（QueryEngine）
1. **本地文件**：`tools/search_terms.txt`（每行一个词）
2. **DuckDuckGo**：热门建议 API（无认证）
3. **Wikipedia**：每日热门话题（需网络）
4. **Bing**：搜索建议 API（模拟用户输入）

#### 去重与过滤
- QueryEngine 自动去重
- 排除敏感词（通过配置）
- 限制每个源的最大查询数

### 任务系统

#### 任务类型
1. **URLRewardTask**：访问指定 URL 获得积分
   - 等待页面加载完成
   - 可能有多步导航

2. **QuizTask**：问答任务
   - 多步骤（通常 5-10 题）
   - 自动选择答案（基于文本匹配）
   - 需要正确完成才能获得积分

3. **PollTask**：投票任务
   - 单步操作
   - 选择任一选项提交

#### 任务发现
TaskParser 分析 DOM 结构：
- 查找任务卡片容器（`.task-card`, `.b_totalTaskCard` 等选择器）
- 提取任务标题、URL、状态（已完成/待完成）
- 过滤已完成任务（绿色勾选标识）

#### 错误恢复
- 单个任务失败不影响其他任务
- 记录失败原因到 `execution_report.json`
- 积分验证（实际积分 vs 报告积分）

### 状态监控与健康检查

#### StateMonitor
- 积分追踪：`points_detector.get_current_points()` 解析 DOM
- 报告生成：每日报告保存到 `logs/daily_reports/`
- 状态持久化：`state_monitor_state.json`

#### HealthMonitor
监控指标：
- 搜索成功率（成功/总次数）
- 平均响应时间（页面加载、搜索完成）
- 浏览器内存使用（通过 psutil）
- 错误率（异常发生次数）

自动告警：连续失败触发预警日志

## 日志和调试

### 日志位置
- **主日志**：`logs/automator.log`（滚动，最大 10MB × 5）
- **诊断报告**：`logs/diagnosis/`（每次运行生成子目录）
- **每日报告**：`logs/daily_reports/`（JSON 格式）
- **状态文件**：`logs/state_monitor_state.json`
- **主题状态**：`logs/theme_state.json`（Bing 主题偏好）

### 日志轮替
- 按大小轮替：10MB/文件，保留 5 个
- 按日期轮替：每日 00:00 自动归档
- 自动清理：30 天前的日志自动删除

### 调试模式

#### 启用诊断
```bash
# 自动启用：--dev 或 --user 模式
rscore --dev --diagnose
rscore --user --diagnose

# 强制启用/禁用
rscore --dev --diagnose      # 启用
rscore --dev --no-diagnose   # 禁用
```

#### 诊断数据
每次运行生成：
```
logs/diagnosis/YYYY-MM-DD_HH-MM-SS/
├── checkpoint_login.json      # 登录检查点
├── checkpoint_search_desktop.json
├── checkpoint_search_mobile.json
├── checkpoint_tasks.json
├── summary.json               # 总体摘要
├── screenshots/
│   ├── login_*.png
│   ├── search_*.png
│   └── tasks_*.png
└── console_logs/
    └── *.json
```

#### 调试技巧
```bash
# 实时跟踪日志
tail -f logs/automator.log

# 查看积分变化
grep -E "points|积分" logs/automator.log

# 筛选 DEBUG 级别
grep "DEBUG" logs/automator.log | tail -100

# 查看最新诊断报告
ls -lt logs/diagnosis/ | head -1
cat logs/diagnosis/*/summary.json
```

### 常见问题排查

#### 登录问题
- **症状**：反复要求登录，无积分增加
- **诊断**：
  - 检查 `storage_state.json` 是否存在、有效
  - 查看诊断截图中的页面 URL
  - 确认是否 2FA 导致登录失败
- **解决**：删除 `storage_state.json`，用 `--user` 有头模式重新登录

#### 搜索无积分
- **症状**：搜索完成但积分未增加
- **诊断**：
  - 检查积分检测器是否正常工作（`points_detector`）
  - Bing 界面是否有变化（选择器失效）
  - 验证搜索词是否有效（ Bing 搜索正常）
- **解决**：启用诊断模式，查看 screenshots

#### 任务未发现
- **症状**：显示 "未发现任何任务"
- **诊断**：
  - 是否已登录到正确页面（rewards.bing.com）
  - 任务卡片 DOM 结构是否变化
  - `task_system.enabled: true` 是否配置
- **解决**：更新 TaskParser 选择器，或检查账户资格

#### 浏览器崩溃
- **症状**：页面崩溃，上下文关闭
- **诊断**：
  - HealthMonitor 内存监控数据
  - 是否内存不足（检查系统资源）
  - 页面加载超时
- **解决**：`_recreate_page()` 自动重建，或减少并发

## 常见问题

### 环境问题
```bash
# rscore 命令不可用
pip install -e .

# playwright 失败
playwright install chromium
# 或
PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium

# 权限问题（Linux）
chmod -R 755 ~/.cache/ms-playwright

# Python 版本
python --version  # 需要 3.10+
```

### 测试失败
```bash
# 检查 pytest 配置
python -m pytest --version

# 查看测试标记
python -m pytest --markers

# 重置 pytest 缓存
rm -rf .pytest_cache

# 显示详细错误
pytest -vv --tb=long
```

### 配置问题
```bash
# 验证配置文件
rscore --dry-run

# 检查环境变量
echo $MS_REWARDS_EMAIL
echo $MS_REWARDS_PASSWORD

# 配置文件语法检查
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### 性能问题
- 搜索间隔太短：增加 `search.wait_interval.max`
- 内存占用高：减少并发，启用 `browser.headless: true`
- 执行时间过长：启用 `--dev` 模式减少搜索次数

## 测试结构

### 目录布局

```
tests/
├── conftest.py                # 全局 pytest 配置（asyncio、临时目录）
├── fixtures/
│   ├── conftest.py            # 测试固件定义
│   ├── mock_accounts.py       # Mock 账户数据
│   └── mock_dashboards.py     # Mock 状态数据
├── unit/                      # 单元测试（隔离测试，推荐日常）
│   ├── test_login_state_machine.py  # 状态机逻辑
│   ├── test_task_manager.py         # 任务管理器
│   ├── test_search_engine.py        # 搜索逻辑
│   ├── test_points_detector.py      # 积分检测
│   ├── test_config_manager.py       # 配置管理
│   ├── test_config_validator.py     # 配置验证
│   ├── test_health_monitor.py       # 健康监控
│   ├── test_review_parsers.py       # PR 审查解析器
│   ├── test_review_resolver.py      # PR 审查解决器
│   ├── test_query_sources.py        # 查询源测试
│   ├── test_online_query_sources.py # 在线查询源测试
│   └── ...
├── integration/               # 集成测试（多组件协作）
│   └── test_query_engine_integration.py
└── manual/                    # 手动测试清单
    └── 0-*.md                # 分阶段测试步骤（未自动化）
```

### 测试标记系统

```python
@pytest.mark.unit           # 单元测试（快速，隔离）
@pytest.mark.integration    # 集成测试（中速，多组件）
@pytest.mark.e2e           # 端到端测试（慢速，完整流程）
@pytest.mark.slow          # 慢速测试（跳过：-m "not slow"）
@pytest.mark.real          # 需要真实凭证（跳过：-m "not real"）
@pytest.mark.property      # Hypothesis 属性测试
@pytest.mark.performance   # 性能基准测试
@pytest.mark.reliability   # 可靠性测试（错误恢复）
@pytest.mark.security      # 安全与反检测测试
```

**默认过滤**：`pytest.ini` 中设置 `addopts = -m 'not real'`，自动跳过真实浏览器测试。

### 测试优先级（测试金字塔）

```
       /\
      /  \  E2E (10%) - 仅关键路径，使用 --real 标记
     /    \ Integration (20%) - 组件间协作
    /______\ Unit (70%) - 快速隔离测试（推荐）
```

推荐日常开发：**70% Unit, 20% Integration, 10% E2E**

### 测试最佳实践

1. **使用 pytest fixtures 进行依赖注入**
   ```python
   @pytest.fixture
   def mock_config():
       return MagicMock(spec=ConfigManager)

   @pytest.fixture
   def account_manager(mock_config):
       return AccountManager(mock_config)
   ```

2. **异步测试**
   ```python
   @pytest.mark.asyncio
   async def test_async_method():
       result = await some_async_func()
       assert result is not None
   ```

3. **属性测试（Hypothesis）**
   ```python
   from hypothesis import given, strategies as st

   @given(st.integers(min_value=1, max_value=100))
   def test_search_count(count):
       assert count > 0
   ```

4. **Mock Playwright 对象**
   ```python
   from pytest_mock import MockerFixture

   def test_page_navigation(mocker: MockerFixture):
       mock_page = MagicMock()
       mock_page.url = "https://www.bing.com"
       mocker.patch('account.manager.is_logged_in', return_value=True)
   ```

## 安全注意事项

**本项目仅供学习和研究使用**。使用自动化工具可能违反 Microsoft Rewards 服务条款。

### 推荐的安全使用方式
- **使用本地运行**：在家庭网络环境中运行，避免使用云服务器
- **禁用调度器**：在 config.yaml 中设置 `scheduler.enabled: false`
- **限制执行频率**：不要短时间内多次运行
- **监控日志**：定期检查执行日志，及时发现异常
- **使用环境变量**：敏感信息不要硬编码在配置文件中
- **保护存储文件**：`storage_state.json` 包含会话令牌，妥善保管

### 避免的危险行为
- **不要在云服务器上运行**：避免使用 AWS、Azure、GitHub Actions 等
- **不要频繁手动运行**：避免一天内多次执行
- **不要修改核心参数**：不要随意减少等待时间
- **不要同时运行多个实例**：避免资源竞争
- **不要提交敏感信息**：检查 `.gitignore`，确保 `.env`、`storage_state.json` 不被提交

### 安全配置建议
```yaml
# 推荐的安全配置
search:
  wait_interval:
    min: 15            # 较长的最小等待时间
    max: 30            # 较长的最大等待时间

scheduler:
  mode: "random"       # 必须使用随机模式
  random_start_hour: 8
  random_end_hour: 22  # 工作时间内随机执行

browser:
  headless: false      # 有头模式更安全（反检测更好）

notification:
  enabled: true       # 启用通知，及时发现问题
```

### 账号安全
- 使用专用账户（非主账户）
- 启用 2FA 保护
- 定期检查账户活动记录
- 设置账户恢复选项

详见 `README.md` 中的"风险提示与安全建议"章节。

## 重要文件与路径

### 配置文件
- `config.example.yaml` → 复制为 `config.yaml`
- 优先级：CLI args > 环境变量 > YAML > 默认值

### 数据文件
- `storage_state.json`：Playwright 会话状态（自动保存）
- `logs/automator.log`：主执行日志
- `logs/daily_reports/`：每日 JSON 报告
- `logs/theme_state.json`：Bing 主题偏好
- `logs/diagnosis/`：诊断数据（--diagnose）

### 辅助文件
- `tools/search_terms.txt`：本地搜索词库（每行一个）
- `.env`：环境变量（推荐使用，不提交）
- `pyproject.toml`：项目配置、依赖、工具设置

### 测试文件
- `tests/unit/`：单元测试
- `tests/integration/`：集成测试
- `tests/fixtures/`：Mock 数据

## 故障排查清单

### 首次运行失败
- [ ] `pip install -e ".[dev]"` 完成？
- [ ] `playwright install chromium` 完成？
- [ ] `config.yaml` 已复制并配置？
- [ ] 邮箱密码正确？
- [ ] 使用 `--user` 模式（非 `--headless`）？

### 登录问题
- [ ] 删除 `storage_state.json` 重新登录
- [ ] 使用有头模式（`headless: false`）
- [ ] 检查 2FA 配置（TOTP secret 正确？）
- [ ] 查看诊断截图：`logs/diagnosis/latest/`

### 搜索无积分
- [ ] 检查 `points_detector` 是否能识别积分元素
- [ ] Bing 页面是否正常显示？
- [ ] 搜索间隔是否过短（<5s）？
- [ ] 查看日志中的积分变化：`grep "积分" logs/automator.log`

### 任务未发现
- [ ] `task_system.enabled: true`？
- [ ] 登录到 rewards.bing.com？
- [ ] 查看任务卡片 DOM 结构（是否变化）
- [ ] 检查 `task_system.debug_mode: true` 保存诊断

### 性能问题
- [ ] 内存使用：`ps aux | grep python`
- [ ] 搜索间隔：`config.search.wait_interval`
- [ ] 浏览器类型：尝试 `--browser chromium`

## 扩展开发

### 添加新的查询源
1. 创建 `src/search/query_sources/your_source.py`
2. 继承 `QuerySource` 基类
3. 实现 `async def fetch_queries(self) -> List[str]`
4. 在 `query_engine.py` 注册

### 添加新任务类型
1. 创建 `src/tasks/handlers/your_task.py`
2. 继承 `TaskHandler` 基类
3. 实现 `can_handle(task)` 和 `async def execute()`
4. 在 `task_parser.py` 添加识别逻辑

### 添加新的通知渠道
1. 扩展 `Notificator` 类
2. 添加配置项（`notification.your_channel.enabled`）
3. 实现 `async def send_your_channel(self, data)`
4. 修改 `send_daily_report` 调用

## 性能优化建议

1. **减少搜索次数**：开发用 `--dev`（2次），测试用 `--user`（3次）
2. **启用 headless**：生产环境 `--headless` 减少资源占用
3. **调整等待间隔**：增加 `wait_interval.max` 降低服务器压力
4. **禁用不必要的组件**：如不需要任务系统，设置 `task_system.enabled: false`
5. **使用 QueryEngine 缓存**：搜索词缓存减少 API 调用

## 版本控制

### Git 工作流
- `main`：稳定版本
- `feature/*`：新功能开发
- `refactor/*`：代码重构
- `fix/*`：Bug 修复
- `test/*`：测试相关

### Commit 约定
遵循 Conventional Commits：
- `feat:` 新功能
- `fix:` Bug 修复
- `refactor:` 重构（无功能变化）
- `test:` 测试相关
- `docs:` 文档
- `chore:` 构建/工具变更

示例：`feat: 添加新的查询源支持 Wikipedia API`

### 预提交钩子
`.pre-commit-config.yaml` 配置：
- ruff check
- ruff format
- mypy（可选）
- pytest（快速单元测试）

运行：`pre-commit run --all-files`

## 贡献指南

### 代码要求
- 100% 类型注解
- 通过 ruff check 和 format
- 单元测试覆盖率 ≥ 80%（新代码）
- 异步函数使用 async/await
- 添加必要的日志（DEBUG/INFO/WARNING/ERROR）

### PR 流程
1. Fork 仓库，创建特性分支
2. 编写代码 + 测试
3. 运行完整验收流程（见上文）
4. 提交 PR，描述清晰
5. 等待 CI 检查
6. 根据反馈修改
7. 合并到 main（Squash and Merge）

### 报告问题
使用 GitHub Issues，提供：
- 问题描述
- 复现步骤
- 预期行为 vs 实际行为
- 日志文件（`logs/automator.log`）
- 诊断数据（如 `--diagnose`）
- 环境信息（OS、Python 版本、Playwright 版本）

## 参考资源

### 内部文档
- `README.md`：项目介绍、快速开始
- `docs/guides/用户指南.md`：完整使用说明
- `docs/reference/WORKFLOW.md`：开发工作流、MCP + Skills
- `docs/reports/技术参考.md`：技术细节、反检测策略

### 外部资源
- [Playwright 文档](https://playwright.dev/python/)
- [playwright-stealth](https://github.com/AtuboDad/playwright_stealth)
- [Microsoft Rewards](https://www.bing.com/rewards)
- [Pydantic](https://docs.pydantic.dev/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

---

**最后更新**：2026-03-06
**维护者**：RewardsCore 社区
**许可证**：MIT（详见 LICENSE 文件）
