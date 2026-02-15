# 🎯 MS Rewards Automator

自动化完成 Microsoft Rewards 任务，轻松赚取积分。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40+-green.svg)](https://playwright.dev/)
[![Maintained](https://img.shields.io/badge/Maintained-Yes-brightgreen.svg)](https://github.com/yourusername/ms-rewards-automator)
[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-orange.svg)](LICENSE)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ⚠️ 免责声明

**本项目仅供学习和研究使用。使用自动化工具可能违反 Microsoft Rewards 服务条款，可能导致账号被限制或封禁。使用本工具造成的任何后果由使用者自行承担，作者不承担任何责任。**

## ✨ 核心功能

### 🔍 智能搜索系统

- **桌面端搜索**: 自动完成30次桌面搜索任务
- **移动端搜索**: 自动完成20次移动搜索任务
- **智能适配**: 自动检测登录状态，首次显示浏览器，后续后台运行
- **反检测机制**: 集成 playwright-stealth，模拟真实用户行为

### 📊 数据监控

- **实时积分监控**: 智能检测积分变化，实时监控任务完成情况
- **会话持久化**: 一次登录，长期使用，自动保存加密的登录状态
- **健康监控**: 内置性能监控，记录执行成功率、响应时间等指标

### 🚀 智能调度

- **定时执行**: 支持每天固定时间自动执行
- **随机调度**: 避开高峰时段，随机时间执行（更安全）
- **批量任务**: 桌面+移动双重任务，最大化收益

### 📈 任务扩展

- **日常任务**: 自动发现并完成奖励任务（问答、调查、URL任务等）
- **任务过滤**: 智能过滤无效任务，只执行有效积分任务
- **错误恢复**: 失败任务自动跳过，继续执行其他任务

### 🔔 通知系统

- **多渠道通知**: 支持 Telegram、微信（Server酱）、WhatsApp 推送
- **实时反馈**: 任务完成情况、积分增长、异常提醒
- **配置灵活**: 可同时启用多种通知方式

## 🛠️ 系统架构

采用模块化设计，核心组件包括：

- **MSRewardsApp**: 主控制器，协调整个系统
- **TaskCoordinator**: 任务协调器，管理执行流程
- **BrowserSimulator**: 浏览器管理器，处理自动化
- **AccountManager**: 账户管理器，处理登录状态
- **SearchEngine**: 搜索引擎，执行搜索任务

各组件松耦合设计，支持独立测试和维护。

- 处理浏览器会话状态
- 集成反检测模块

#### 4. StateMonitor (状态监控器)

- **职责**: 监控和记录系统状态
- **功能**:
  - 积分变化检测
  - 任务完成状态跟踪
  - 生成每日报告

#### 5. AccountManager (账户管理器)

- **职责**: 管理账户登录和会话
- **功能**:
  - 自动和手动登录支持
  - 会话持久化
  - 登录状态验证

### 执行流程

#### 完整执行流程

```
1. 系统初始化
   ├─ 加载配置文件
   ├─ 初始化所有组件
   └─ 启动健康监控

2. 浏览器管理
   ├─ 检查登录状态
   ├─ 需要登录时显示浏览器
   └─ 保存登录会话状态

3. 搜索任务执行
   ├─ 桌面端搜索 (30次)
   │  └─ 使用搜索词库+随机延迟
   │
   ├─ 浏览器切换
   │  └─ 保存桌面会话→创建移动浏览器
   │
   └─ 移动端搜索 (20次)
      └─ 使用搜索词库+随机延迟

4. 日常任务执行
   ├─ 发现可用任务
   ├─ 过滤无效任务
   └─ 执行剩余任务

5. 生成报告
   ├─ 保存执行数据
   ├─ 发送通知
   └─ 清理资源
```

### 关键技术特性

#### 🔄 会话管理策略

- **智能检测**: 自动检测已有会话，避免重复登录
- **会话持久化**: 加密保存登录状态，长期有效
- **会话恢复**: 意外退出后可从上次位置恢复

#### 🎭 反检测机制

- **playwright-stealth**: 隐藏自动化特征
- **随机延迟**: 搜索间隔随机化，模拟真实用户
- **加权调度**: 避开高峰时段，分散执行时间

#### 📊 数据收集

- **实时监控**: 监控每次搜索后的积分变化
- **智能分析**: 识别积分异常，及时告警
- **持久化存储**: 日志和报告长期保存

## 🚀 快速开始

### 1. 环境准备

#### Windows 用户（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/ms-rewards-automator.git
cd ms-rewards-automator

# 使用 Conda 环境（推荐）
conda env create -f environment.yml
conda activate ms-rewards-bot

# 验证安装
python tools/check_environment.py
```

#### Linux/macOS 用户

```bash
# 克隆仓库
git clone https://github.com/Disaster-Terminator/ms-rewards-automator.git
cd ms-rewards-automator

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装浏览器
playwright install chromium
```

### 2. 首次使用

```bash
# 开发模式（快速测试，2+2搜索）
python main.py --dev

# 用户模式（完整测试，3+3搜索，拟人行为）
python main.py --usermode
```

**运行模式说明**：

| 模式 | 桌面搜索 | 移动搜索 | 拟人行为 | 防检测 | 用途 |
|------|----------|----------|----------|--------|------|
| `--dev` | 2 | 2 | ❌ | ❌ | 快速迭代调试 |
| `--usermode` | 3 | 3 | ✅ | ✅ | 鲁棒性测试 |
| 默认 | 30 | 20 | ✅ | ✅ | 生产环境 |

**智能模式说明**：

- **首次运行**: 自动打开浏览器，需要手动登录 Microsoft 账号
- **后续运行**: 自动保存会话，使用无头模式（后台运行）
- **重新登录**: 删除 `storage_state.json` 文件后重新运行

### 3. 常用命令

#### 基本使用

```bash
# 生产环境（完整搜索）
python main.py

# 用户模式（测试真实使用场景）
python main.py --usermode

# 开发模式（快速迭代）
python main.py --dev

# 显示浏览器（调试模式）
python main.py --headless=false

# 慢速模式（更安全）
python main.py --mode slow

# 启动调度器（每天自动执行）
python main.py --schedule

# 仅执行桌面搜索
python main.py --desktop-only

# 仅执行移动搜索
python main.py --mobile-only
```

#### 调试和测试

```bash
# 模拟执行（不执行真实搜索）
python main.py --dry-run

# 详细日志输出
python main.py --verbose

# 跳过日常任务
python main.py --skip-daily-tasks
```

### 4. 查看执行结果

#### 启动数据面板

```bash
streamlit run tools/dashboard.py
```

数据面板显示：

- 今天的任务完成情况
- 积分获得详情
- 7天积分增长趋势
- 执行状态和错误信息

## 🎯 实际使用场景

### 场景1：日常自动化任务

- **目标**: 每天自动完成所有任务，获得最大积分
- **配置**: 启用调度器，设置随机时间执行
- **流程**: 早上随机时间自动启动 → 完成所有任务 → 发送结果通知

### 场景2：手动调试模式

- **目标**: 查看浏览器执行过程，调试问题
- **配置**: `--headless=false` 强制显示浏览器
- **流程**: 启动 → 手动登录 → 观察执行过程 → 查看错误

### 场景3：快速测试模式

- **目标**: 快速验证配置是否正确
- **配置**: `--dev` 开发模式（2+2搜索，最小等待）
- **流程**: 快速完成登录和搜索验证

### 场景4：仅执行移动搜索

- **目标**: 只完成移动端搜索任务
- **配置**: `--mobile-only`
- **流程**: 桌面登录 → 创建移动上下文 → 完成移动搜索

## 详细文档

### 用户文档

- **[用户指南](docs/guides/用户指南.md)** - 完整的使用说明、配置详解和故障排除

### 技术文档

- **[技术参考](docs/reports/技术参考.md)** - 防检测策略和技术实现细节

### 配置文件说明

```yaml
# 基础配置
search:
  desktop_count: 30      # 桌面搜索次数
  mobile_count: 20       # 移动搜索次数
  wait_interval:
    min: 8              # 最小等待时间（秒）
    max: 20             # 最大等待时间（秒）

# 调度配置
scheduler:
  enabled: true         # 启用调度器
  mode: "random"        # 随机时间模式
  random_start_hour: 8  # 开始时间
  random_end_hour: 22   # 结束时间

# 通知配置
notification:
  enabled: true
  telegram:
    enabled: true
    bot_token: "你的Bot Token"
    chat_id: "你的Chat ID"
  serverchan:
    enabled: true
    key: "你的SendKey"
```

## ⚠️ 风险提示与安全建议

### ⚠️ 重要声明

本项目仅供学习和研究使用。使用自动化工具可能违反 Microsoft Rewards 服务条款，可能导致账号被限制或封禁。使用本工具造成的任何后果由使用者自行承担。

### ✅ 推荐的安全使用方式

- **使用本地运行**: 在家庭网络环境中运行，避免使用云服务器
- **启用慢速模式**: `python main.py --mode slow`
- **启用随机调度**: `python main.py --schedule`
- **限制执行频率**: 不要短时间内多次运行
- **监控日志**: 定期检查执行日志，及时发现异常

### ❌ 避免的危险行为

- **不要在云服务器上运行**: 避免使用 AWS、Azure、GitHub Actions 等
- **不要频繁手动运行**: 避免一天内多次执行
- **不要修改核心参数**: 不要随意减少等待时间
- **不要同时运行多个实例**: 避免资源竞争

### 📊 安全配置建议

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

notification:
  enabled: true       # 启用通知，及时发现问题
```

## 📁 项目结构

```
ms-rewards-automator/
├── src/                    # 源代码目录
│   ├── account/           # 账户管理
│   ├── browser/           # 浏览器控制
│   ├── infrastructure/    # 基础设施
│   ├── login/             # 登录模块
│   ├── search/            # 搜索模块
│   ├── tasks/             # 任务系统
│   └── ui/                # 用户界面
├── tests/                  # 测试目录
│   ├── autonomous/        # 自动化测试
│   ├── integration/       # 集成测试
│   └── unit/              # 单元测试
├── tools/                  # 辅助工具
│   ├── check_environment.py
│   ├── dashboard.py
│   └── search_terms.txt
├── docs/                   # 文档目录
│   ├── guides/            # 用户指南
│   └── reports/           # 技术报告
├── logs/                   # 日志文件
├── main.py                 # 主程序入口
├── config.yaml             # 配置文件
└── requirements.txt        # Python 依赖
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Playwright](https://playwright.dev/) - 浏览器自动化框架
- [playwright-stealth](https://github.com/AtuboDad/playwright_stealth) - 反检测插件
- [Streamlit](https://streamlit.io/) - 数据可视化框架

---

**如果觉得有用，请给个 ⭐ Star！**
