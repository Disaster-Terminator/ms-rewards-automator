# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Microsoft Rewards 自动化工具，基于 Playwright 实现浏览器自动化，完成每日搜索和任务以获取积分。

**核心技术**：Python 3.10+, async/await, Playwright, playwright-stealth

## 常用命令

### 开发环境设置
```bash
# 安装依赖（开发环境）
pip install -e ".[dev]"

# 安装浏览器
playwright install chromium

# 验证安装
python tools/check_environment.py
```

### 代码质量
```bash
# Lint 检查
ruff check .

# 格式化代码
ruff format .

# 类型检查
mypy src/
```

### 测试
```bash
# 单元测试（推荐）
python -m pytest tests/unit/ -v --tb=short --timeout=60 -m "not real"

# 集成测试
python -m pytest tests/integration/ -v --tb=short --timeout=60

# 快速测试（跳过标记为 slow 的测试）
python -m pytest tests/unit/ -v -m "not real and not slow"

# 运行单个测试文件
python -m pytest tests/unit/test_login_state_machine.py -v

# 运行特定测试函数
python -m pytest tests/unit/test_login_state_machine.py::TestLoginStateMachine::test_initial_state -v
```

### 运行应用
```bash
# 生产环境（20次搜索，启用调度器）
rscore

# 用户测试模式（3次搜索，无调度器）
rscore --user

# 开发模式（2次搜索，快速调试）
rscore --dev

# 无头模式（后台运行）
rscore --headless

# 组合使用
rscore --dev --headless
```

## 代码风格规范

### 必须遵守
- **Python 3.10+**：使用现代 Python 特性
- **类型注解**：所有函数必须有类型注解
- **async/await**：异步函数必须使用 async/await
- **line-length = 100**：行长度不超过 100 字符

### Lint 规则
项目使用 ruff，启用的规则集：
- E, W: pycodestyle 错误和警告
- F: Pyflakes
- I: isort
- B: flake8-bugbear
- C4: flake8-comprehensions
- UP: pyupgrade

## 项目架构

### 核心模块（src/）

```
src/
├── account/          # 账户管理（积分检测、会话状态）
├── browser/          # 浏览器控制（模拟器、反检测、弹窗处理）
├── constants/        # 常量定义（URL、配置常量）
├── diagnosis/        # 诊断系统（错误报告、截图）
├── infrastructure/   # 基础设施（配置、日志、调度、监控）
├── login/            # 登录系统（状态机、各种登录处理器）
├── review/           # PR 审查工作流（GraphQL 客户端、评论解析）
├── search/           # 搜索模块（搜索引擎、查询生成、多源查询）
├── tasks/            # 任务系统（任务解析、任务处理器）
└── ui/               # 用户界面（主题管理、状态显示）
```

### 核心组件协作关系

```
MSRewardsApp (主控制器)
    ├── SystemInitializer (初始化组件)
    ├── TaskCoordinator (任务协调器)
    │   ├── BrowserSimulator (浏览器模拟)
    │   ├── AccountManager (账户管理)
    │   ├── SearchEngine (搜索引擎)
    │   ├── StateMonitor (状态监控)
    │   └── HealthMonitor (健康监控)
    └── Notificator (通知系统)
```

### 关键设计模式

1. **依赖注入**：TaskCoordinator 通过构造函数接收依赖项，提高可测试性
2. **状态机模式**：登录流程使用状态机管理复杂的登录步骤
3. **策略模式**：搜索词生成支持多种源（本地文件、DuckDuckGo、Wikipedia）
4. **门面模式**：MSRewardsApp 封装子系统交互，提供统一接口

## 配置管理

### 配置文件
- **主配置文件**：`config.yaml`（从 `config.example.yaml` 复制）
- **环境变量支持**：敏感信息（密码、token）优先从环境变量读取

### 关键配置项
```yaml
# 搜索配置
search:
  desktop_count: 20          # 桌面搜索次数
  mobile_count: 0             # 移动搜索次数
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
```

## 开发工作流

### 验收流程
项目采用严格的验收流程，详见 `docs/reference/WORKFLOW.md`：

1. **静态检查**：`ruff check . && ruff format --check .`
2. **单元测试**：`pytest tests/unit/ -v`
3. **集成测试**：`pytest tests/integration/ -v`
4. **Dev 无头验收**：`rscore --dev --headless`
5. **User 无头验收**：`rscore --user --headless`

### Skills 系统
项目集成了 MCP 驱动的 Skills 系统：
- `review-workflow`: PR 审查评论处理完整工作流
- `acceptance-workflow`: 代码验收完整工作流

详见 `.trae/skills/` 目录。

## 测试结构

```
tests/
├── fixtures/        # 测试固件（mock 对象、测试数据）
├── integration/     # 集成测试（多组件协作）
├── manual/          # 手动测试清单
└── unit/            # 单元测试（隔离组件测试）
```

### 测试标记
```python
@pytest.mark.unit          # 单元测试
@pytest.mark.integration   # 集成测试
@pytest.mark.e2e           # 端到端测试
@pytest.mark.slow          # 慢速测试
@pytest.mark.real          # 真实浏览器测试（需要凭证）
```

## 重要实现细节

### 登录系统
- **状态机驱动**：`LoginStateMachine` 管理登录流程状态转换
- **多步骤处理**：支持邮箱输入、密码输入、2FA、恢复邮箱等
- **会话持久化**：登录状态保存在 `storage_state.json`

### 反检测机制
- **playwright-stealth**：隐藏自动化特征
- **随机延迟**：搜索间隔随机化（配置 min/max）
- **拟人化行为**：鼠标移动、滚动、打字延迟

### 搜索词生成
支持多源查询：
1. 本地文件（`tools/search_terms.txt`）
2. DuckDuckGo 建议 API
3. Wikipedia 热门话题
4. Bing 建议 API

### 任务系统
自动发现并执行奖励任务：
- URL 奖励任务
- 问答任务（Quiz）
- 投票任务（Poll）

## 日志和调试

### 日志位置
- **主日志**：`logs/automator.log`
- **诊断报告**：`logs/diagnosis/` 目录
- **主题状态**：`logs/theme_state.json`

### 调试技巧
```bash
# 查看详细日志
tail -f logs/automator.log

# 启用诊断模式
# 在代码中设置 diagnose=True

# 查看积分变化
grep "points" logs/automator.log
```

## 常见问题

### 环境问题
```bash
# 如果 rscore 命令不可用
pip install -e .

# 如果 playwright 失败
playwright install chromium
```

### 测试失败
```bash
# 检查 pytest 配置
python -m pytest --version

# 查看测试标记
python -m pytest --markers
```

### 登录问题
- 删除 `storage_state.json` 重新登录
- 首次运行使用非无头模式（`headless: false`）
- 检查 `logs/diagnosis/` 目录中的截图

## 安全注意事项

**本项目仅供学习和研究使用**。使用自动化工具可能违反 Microsoft Rewards 服务条款。

推荐的安全使用方式：
- 在本地家庭网络运行，避免云服务器
- 禁用调度器或限制执行频率
- 监控日志，及时发现异常
- 不要同时运行多个实例

详见 `README.md` 中的"风险提示与安全建议"章节。