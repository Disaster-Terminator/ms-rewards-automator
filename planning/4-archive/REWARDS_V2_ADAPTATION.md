# RewardsCore 开发备忘录

> 创建时间：2025-02-18
> 最后更新：2026-02-25
> 状态：开发中

## 〇、最新进展

### 已合并 PR

- **#9** `feat: 重构诊断系统与 PR 审查工作流，引入 MCP 驱动的多智能体框架` - 已合并 ✅
- **#8** `fix: 调整搜索次数默认值并重命名项目为 RewardsCore` - 已合并 ✅
- **#7** `feat: 搜索功能改进和拟人化行为集成` - 已合并 ✅
- **#6** `feat(tasks): 实现earn页面任务系统，支持URL任务自动执行` - 已合并 ✅
- **#5** `refactor: 参数精简与调度器整改` - 已合并 ✅

### 当前分支状态（2026-02-25 更新）

| 分支 | 状态 | 提交 | 说明 |
|------|------|------|------|
| `main` | 🟢 up to date | 771ad45 | 诊断系统已集成 |
| `feature/frontend-ui` | ⏸️ 暂缓 | 85f5997 | 工作树保留，暂不合并 |
| `feature/notifications` | 📋 待开发 | - | 通知系统新式改造 |
| `refactor/diagnosis-integration` | ✅ 已合并 (#9) | - | 工作树已清理 |
| `fix/search-count-rename` | ✅ 已合并 (#8) | - | 工作树已清理 |
| `feature/daily-tasks` | ✅ 已合并 (#6) | - | 工作树已清理 |
| `feature/search-improvement` | ✅ 已合并 (#7) | - | 工作树已清理 |
| `fix/config-consistency` | ✅ 已合并 (#5) | - | 工作树已清理 |

### 工作树状态

```
C:/Users/Disas/.../RewardsCore           771ad45 [main]
C:/Users/Disas/.../RewardsCore-frontend  85f5997 [feature/frontend-ui] ⏸️ 暂缓
```

### 最近提交历史

```
771ad45 feat: 重构诊断系统与 PR 审查工作流，引入 MCP 驱动的多智能体框架 (#9)
e10d3a0 fix: 调整搜索次数默认值并重命名项目为 RewardsCore (#8) 
4752f72 feat(tasks): 实现earn页面任务系统，支持URL任务自动执行 (#6)
cb48ce8 feat: 搜索功能改进和拟人化行为集成 (#7)
5780b7b refactor: 参数精简与调度器整改 (#5)
```

---

## 一、改版背景

2025年1月底，微软 Rewards 进行大改版，积分获取机制发生重大变化。

### 改版前后对比

| 项目 | 改版前 | 改版后 | 变化 |
|------|--------|--------|------|
| 搜索积分 | 150/天 (PC 90 + 移动 60) | 60/天 (统一，每次+3分) | -60% |
| 搜索次数 | PC 30次 + 移动 20次 | 20次 (统一) | - |
| 会员等级 | 1级/2级 | 会员/银牌/金牌 | 新增金牌 |
| 福利领取 | 无 | 月初5天领取 | 新功能 |
| 连胜系统 | 无 | 搜索/Edge/App 连胜 | 新功能 |

### 会员等级权益

> **注**：用户连续使用脚本搜索7天即可升级银牌，两周后自动升级金牌，升级活动无需特殊处理。

| 权益 | 会员 | 银牌 | 金牌 |
|------|------|------|------|
| 每日搜索积分上限（每次+3分） | 15 (5次) | 30 (10次) | 60 (20次) |
| 每月级别奖励 | 60 | 180 | 420 |
| 默认搜索奖励（每月） | 30 | 90 | 210 |
| 必应 Star 奖励（每月最多） | 300 | 900 | 2100 |
| 专属收益优惠 | — | ✓ | ✓ |
| 兑换折扣优惠券(点数) | — | 100 | 200 |

> **关键信息**：每月奖励需在月初5天内领取，有效期通常为30天。

## 二、任务板块分工

### 已实现（`feature/daily-tasks` 分支）

| 板块 | 功能 | 状态 |
|------|------|------|
| 任务板块 | 月度任务卡片 URL 任务解析 | ✅ |
| 继续赚取板块 | 搜索/Quiz/Poll/拼图任务 | ✅ |
| 完成状态检测 | CSS 类判断 | ✅ |
| 页面导航 | Dashboard → Earn 页面 | ✅ |

### 待开发

| 板块 | 功能描述 | 复杂度 |
|------|----------|--------|
| 连胜板块 | 搜索连胜 / Edge 连胜 / App 连胜 / 印章收集 | 🟡 中 |
| 升级活动板块 | 金牌会员升级任务（2选1） | 🟢 低 |
| 福利板块 | 月初5天领取（Star奖励/升级奖励/默认搜索奖励） | 🔴 高 |

## 三、分支规划

| 分支 | 负责内容 | 状态 | 优先级 |
|------|----------|------|--------|
| `feature/search-improvement` | 搜索功能改进 | ✅ 已合并 (#7) | - |
| `feature/daily-tasks` | 任务系统实现 | ✅ 已合并 (#6) | - |
| `refactor/diagnosis-integration` | 诊断系统重构 + PR 审查工作流 | ✅ 已合并 (#9) | - |
| `fix/search-count-rename` | 搜索次数调整 + 项目重命名 | ✅ 已合并 (#8) | - |
| `fix/config-consistency` | 配置一致性修复 | ✅ 已合并 (#5) | - |
| `feature/frontend-ui` | 前端界面 + 新规则适配 | ⏸️ 暂缓 | 🟡 |
| `feature/benefits-collection` | 福利板块（月初领取） | 📋 待创建 | 🔴 高（时间敏感） |
| `feature/notifications` | 通知系统新式改造 | 📋 待开发 | 🟢 |
| `feature/task-system-refactor` | 任务系统优化 | 📋 待创建 | 🟡 |

### 开发顺序建议

```
第一批（已完成）
├── refactor/diagnosis-integration  ✅ 已完成 - 诊断系统已集成到 --dev/--user
├── fix/search-count-rename         ✅ 已完成 - 搜索次数调整，项目重命名
└── fix/config-consistency          ✅ 已完成

第二批（功能开发，优先）
├── feature/benefits-collection     ← 时间敏感（月初领取）
└── feature/frontend-ui             ⏸️ 暂缓（保留工作树，暂不合并）

第三批（测试补充，与功能并行）
├── test/login-handlers
├── test/task-handlers
└── test/account-module

第四批（后续功能）
├── feature/task-system-refactor
└── feature/notifications
```

## 四、技术适配点

### 4.1 搜索模块（✅ 已完成 #7）

- **已完成**：
  - 新增查询源：DuckDuckGo, Wikipedia
  - `search_engine.py` 大幅重构
  - 拟人化行为集成
  - 新增测试覆盖

### 4.2 积分检测器

- **需更新**：CSS 选择器适配新版页面
- **需新增**：会员等级检测、福利板块检测、连胜系统检测

### 4.3 任务系统

- **已有基础**：`task_parser.py` 支持 `streaks` section
- **需扩展**：福利领取任务类型

## 五、冲突分析

### 高风险文件

| 文件 | 涉及分支 | 建议 |
|------|----------|------|
| `config_manager.py` | daily-tasks, frontend-ui | 已合并 search-improvement |
| `task_coordinator.py` | daily-tasks, frontend-ui | 协调修改 |

### 低风险区域

| 模块 | 说明 |
|------|------|
| `src/search/query_sources/` | ✅ 已合并 (#7) |
| `src/rewards_v2/` | 新建目录，无冲突 |

## 六、开发流程改进

### 问题记录

| 问题 | 说明 | 状态 |
|------|------|------|
| Agent 不自动执行 lint/format | 通常不会自己执行 `ruff` 和 `ruff format` | 待解决 |
| Agent 不运行实战测试 | 只跑 pytest 自动化测试，不跑 --dev/--user 实战测试 | 待解决 |
| 自动化测试无法发现深层问题 | Mock 测试只能排查浅层问题，无法直击复杂逻辑谬误 | 已知限制 |
| ~~自主测试框架未集成~~ | ~~应该集成到 --dev/--user，当前是无效的独立参数~~ | ✅ 已解决 (#9) |

### 测试流程问题深度分析

#### 测试概念区分

| 类型 | 命令 | 特点 | 能力 |
|------|------|------|------|
| **自动化测试** | `pytest tests/` | Mock 测试，不涉及真实浏览器 | 只能排查浅层问题（语法、类型、简单逻辑） |
| **诊断系统** | `--dev` / `--user` (已集成) | 真实浏览器、真实场景、诊断报告 | 发现复杂逻辑谬误，生成诊断报告 |
| **实战测试** | `--dev` / `--user` | 真实浏览器、真实场景 | 验证真实用户场景 |

**关键结论**：

- 自动化测试 = Mock 测试，无法模拟真实场景
- ✅ 诊断系统已集成到 `--dev`/`--user` 中（#9）
- 无效参数 `--autonomous-test`、`--quick-test` 已移除

#### 测试层次与 Agent 执行现状

| 测试层次 | 命令 | Agent 执行情况 | 问题 |
|----------|------|----------------|------|
| Lint/Format | `ruff check/format` | ❌ 不执行 | 需要强制要求 |
| 自动化测试 | `pytest tests/` | ✅ 自动执行 | 只能排查浅层问题 |
| 快速实战测试 | `--dev` | ❌ 不执行 | 应该在自动化测试后执行 |
| 稳定性实战测试 | `--user` | ❌ 不执行 | 应该在 dev 通过后执行 |

```

## 七、架构优化建议（待处理）

### 问题1：登录轮询和URL导航逻辑重复

**位置**：

- `tools/diagnose.py`（`diagnose_task_discovery` 函数）
- `src/tasks/task_parser.py`

**问题描述**：这两个文件中都包含类似的"等待登录并导航到earn/dashboard"的逻辑。代码重复会导致：

1. 维护困难 - 修改一处需要同步修改其他位置
2. 潜在的漂移风险 - 各处逻辑可能逐渐不一致
3. 增加测试负担

**建议方案**：提取一个共享helper函数

```python
# src/utils/navigation_helper.py
async def wait_for_login_and_navigate(page, target="earn", timeout=60):
    """等待用户登录并导航到目标页面"""
    pass
```

### 问题2：earn/dashboard URLs硬编码在多处

**位置**：

- `src/tasks/task_parser.py` - `EARN_URL` 常量
- `tools/diagnose.py` - 直接使用URL字符串

**问题描述**：Microsoft Rewards的URL可能随时间变化（如最近的平台改版）。URL分散在多个文件中：

1. 修改时容易遗漏
2. 增加出错风险
3. 不利于快速适应平台变化

**建议方案**：集中到配置或常量模块

```python
# src/constants.py 或 config.yaml
REWARDS_URLS = {
    "earn": "https://rewards.bing.com/earn",
    "dashboard": "https://rewards.microsoft.com/dashboard",
    "rewards_home": "https://rewards.microsoft.com/",
}
```

**优先级**：低（非阻塞，不影响当前功能正确性）
**建议处理时机**：可作为后续重构任务，在功能稳定后统一处理

### 问题3：待补充测试（功能测试）

**拟人化行为测试**：

- 打字延迟范围验证（正态分布参数）
- 10%概率思考停顿触发验证
- 鼠标移动 Bezier 曲线验证

**状态显示测试**：

- 预计剩余时间计算准确性
- 实时状态更新无闪烁（需要 UI 集成测试）

**优先级**：低
**建议处理时机**：创建单独的测试任务处理，不在当前分支范围

### 问题4：单元测试缺失（feature/daily-tasks 审查发现）

> 来源：Copilot 审查 + 代码审查反馈，2026-02-19

**P1 - URL任务异常处理**：

- 位置：`src/tasks/handlers/url_reward_task.py`
- 问题：各类型任务(搜索/测验/拼图/通用)的异常处理返回值已改为 `False`，缺少测试
- 建议：`tests/unit/test_url_reward_task.py` - 验证各任务类型异常时返回False

**P1 - 登录页面重定向**：

- 位置：`src/tasks/task_parser.py` 第 176-185 行
- 问题：登录/OAuth 页面检测和重定向逻辑无单元测试
- 建议：`tests/unit/test_task_parser.py` - 验证重定向行为

**P1 - 临时页面积分检测**：

- 位置：`src/infrastructure/task_coordinator.py` 中 `temp_page` 逻辑
- 问题：无 mock 单元测试覆盖，集成测试不够精细
- 建议：`tests/unit/test_task_coordinator.py` - 验证积分检测使用临时页面

**P1 - URL过滤规则**：

- 位置：`src/tasks/task_parser.py` skipHrefs 逻辑
- 问题：skipHrefs 改用 `includes()` 匹配，缺少针对各种 URL 格式的过滤行为测试
- 建议：`tests/unit/test_task_parser.py` - 验证带查询参数/锚点的URL过滤行为

**P2 - 任务系统禁用隔离测试**：

- 位置：无明确测试
- 问题：`task_system.enabled: False` 时需验证其他功能不受影响
- 建议：`tests/unit/test_task_manager.py`

**P3 - diagnose.py 单元测试**：

- 位置：`tools/diagnose.py`
- 问题：诊断工具无单元测试覆盖，headless 模式切换逻辑需要验证
- 建议：`tests/unit/test_diagnose.py`

### 问题4.5：测试改进备忘（feature/daily-tasks 分支）

> 来源：分支开发过程中的测试分析，2026-02-20

**测试场景分析**：

| 测试场景 | 复杂度 | 建议 |
|----------|--------|------|
| 页面资源管理 | 高（需mock Playwright） | 备忘 |
| 上下文管理器 | 中（单元测试） | 备忘 |
| 配置验证 | 低（单元测试） | 备忘 |
| 积分检测 | 高（集成测试） | 现有测试已覆盖 |
| 错误回调 | 中（单元测试） | 备忘 |

**页面资源管理测试**：

```python
# tests/unit/test_page_utils.py
async def test_temp_page_closes_on_exception():
    """验证临时页面在异常情况下也能正确关闭"""

async def test_temp_page_no_memory_leak():
    """验证无内存泄漏"""
```

**上下文管理器测试**：

```python
async def test_temp_page_propagates_exception():
    """temp_page应该向上传播异常"""

async def test_safe_temp_page_suppresses_exception():
    """safe_temp_page应该抑制异常并返回None"""
```

**配置验证测试**：

```python
# tests/unit/test_task_parser_validation.py
def test_validate_string_list_sanitizes_dangerous_chars():
    """危险字符应被清理"""

def test_validate_fallback_to_default():
    """验证失败应回退到默认值"""

def test_validate_empty_result_uses_default():
    """清理后为空应使用默认值"""
```

**错误回调测试**：

```python
async def test_safe_temp_page_calls_on_error():
    """验证on_error回调正确触发"""
```

**优先级**：低
**备注**：当前分支核心功能已有380个测试覆盖，安全修复已验证通过

### 问题5：安全漏洞（待修复）

**P2 - 命令注入风险**：

- 位置：`tools/run_tests.py` 第 17-24 行
- 问题：`subprocess.run(..., shell=True)` 存在命令注入风险
- 影响：攻击者可执行任意 OS 命令
- 修复方案：使用 `shlex.split(cmd)` + `shell=False`
- 备注：项目处于开发阶段，可在其他分支中顺便修复，无需单独开分支

### 问题6：任务系统待优化问题（feature/daily-tasks 发现）

> 来源：分支开发过程中的问题记录，2026-02-20

| 问题 | 描述 | 优先级 |
|------|------|--------|
| 任务积分报告不准确 | 页面显示的积分可能是板块总积分，非单个任务积分 | 高 |
| 任务发现遗漏 | 继续赚取显示 20/25 但只发现 6 个任务 | 高 |
| 积分来源混淆 | URL 任务触发搜索，积分来源不明确 | 中 |

**建议后续分支规划**：

- 当前分支合并后，创建 `feature/task-system-refactor` 分支
- 重新分析 earn 页面 HTML 结构
- 改进积分提取逻辑（区分板块积分 vs 任务积分）
- 完善任务发现覆盖率

## 八、后续行动

### 待清理

- [x] ~~推送 main 分支到远程~~ ✅ 已完成
- [x] ~~清理 `feature/daily-tasks` 工作树~~ ✅ 已完成

### 待开发

- [ ] 创建 `feature/benefits-collection` 分支（福利领取功能）
- [ ] 创建 `feature/task-system-refactor` 分支（任务系统优化）
- [ ] `feature/frontend-ui` 暂缓合并，工作树保留

---

## 九、全盘扫描报告（2026-02-25 更新）

### 9.1 代码结构概览

```
src/
├── account/          # 账户管理（2 文件）
├── browser/          # 浏览器层（7 文件）
├── diagnosis/        # 诊断系统（5 文件）✅ 新增
├── infrastructure/   # 基础设施（16 文件）
├── login/            # 登录模块（6 文件 + 9 handlers）
├── review/           # PR 审查系统（6 文件）✅ 新增
├── search/           # 搜索模块（5 文件 + 5 query_sources）
├── tasks/            # 任务系统（3 文件 + 3 handlers）
└── ui/               # UI 组件（4 文件）

tests/
├── unit/             # 单元测试（21 文件）
├── integration/      # 集成测试（2 文件）
└── fixtures/         # 测试 Fixtures（4 文件）
```

**核心架构**：

- **门面模式**：`MSRewardsApp` 封装子系统交互
- **状态机模式**：`LoginStateMachine` 处理多步骤登录
- **策略模式**：多种查询源可插拔切换
- **依赖注入**：`Container` 管理组件生命周期
- **诊断系统**：集成到 `--dev`/`--user`，提供实时诊断报告
- **PR 审查工作流**：MCP 驱动的多智能体框架

### 9.2 测试覆盖分析

| 测试类型 | 文件数 | 覆盖模块 |
|----------|--------|----------|
| 单元测试 | 21 | config, login, search, tasks, browser, review |
| 集成测试 | 2 | query_engine, P0 模块 |

#### 测试覆盖缺口（P0 紧急）

| 模块 | 文件数 | 风险等级 |
|------|--------|----------|
| `login/handlers/` | 9 | **高** - 完全无测试 |
| `tasks/handlers/` | 3 | **高** - 完全无测试 |
| `account/` | 2 | **高** - 完全无测试 |
| `search/search_engine.py` | 1 | **高** - 核心模块无测试 |
| `infrastructure/error_handler.py` | 1 | **高** - 关键模块无测试 |

#### 测试覆盖缺口（P1 重要）

| 模块 | 说明 |
|------|------|
| `browser/anti_ban_module.py` | 反检测核心，无测试 |
| `infrastructure/task_coordinator.py` | 任务协调，集成测试不足 |
| `login/login_detector.py` | 登录检测，无测试 |

### 9.3 依赖管理问题

#### 中等问题

| 问题 | 说明 |
|------|------|
| pyproject.toml 缺少依赖声明 | 未声明 dependencies 和 optional-dependencies |
| 依赖分类不清晰 | 运行/测试/可视化依赖混合在 requirements.txt |

### 9.4 建议改进优先级

#### P0 - 紧急（阻塞开发）

1. **补充关键模块测试**：
   - `login/handlers/` - 9 个 handler 单元测试
   - `tasks/handlers/` - 3 个 handler 单元测试
   - `account/manager.py` + `points_detector.py`
   - `search/search_engine.py`

#### P1 - 重要（影响质量）

1. **完善 pyproject.toml**：
   - 添加 `dependencies` 和 `optional-dependencies`
   - 使其成为单一真实来源

2. **补充集成测试**：
   - 登录流程集成测试
   - 搜索执行集成测试
   - 任务执行集成测试

#### P2 - 一般（技术债务）

1. **分离依赖文件**：
   - `requirements-dev.txt` 或 `optional-dependencies`

2. **补充 browser 模块测试**
