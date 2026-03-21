# RewardsCore 规划文档

> 最后更新：2026-02-28
> 维护者：Master Agent (main 分支)

---

## 文档导航

| 类型 | 目录 | 说明 |
|------|------|------|
| 📋 规划 | [1-plans/](./1-plans/) | 核心规划、开发路线图 |
| 📖 参考 | [2-reference/](./2-reference/) | API 文档、技术分析 |
| ✅ 任务 | [3-tasks/](./3-tasks/) | 分支任务文档 |
| 📦 归档 | [4-archive/](./4-archive/) | 历史文档 |

---

## 当前重点

### 核心文档

| 文档 | 说明 |
|------|------|
| [核心规划](./1-plans/PLAN.md) | 分支状态、开发阶段、待处理问题 |
| [API 完整文档](./2-reference/API完整文档.md) | Dashboard、App、Quiz、URL Reward API |

### 进行中任务

| 任务 | 分支 | 状态 |
|------|------|------|
| [Dashboard API 集成](./3-tasks/active/TASK_dashboard_api.md) | feature/dashboard-api | 🔄 开发中 |
| [查询源扩展](./3-tasks/active/TASK_query_sources.md) | feature/query-sources | 🔄 开发中 |
| [App API 集成](./3-tasks/active/TASK_app_api.md) | feature/app-api | 🔄 开发中 |

### 等待中任务

| 任务 | 分支 | 依赖 |
|------|------|------|
| [福利领取系统](./3-tasks/pending/TASK_benefits_collection.md) | feature/benefits-collection | dashboard-api |
| [连胜系统](./3-tasks/pending/TASK_streak_system.md) | feature/streak-system | dashboard-api |

---

## API 状态

| API | 状态 | 认证 |
|-----|------|------|
| Dashboard API | ✅ 可用 | Cookie |
| Bing Quiz API | ✅ 可用 | Cookie |
| URL Reward API | ✅ 可用 | Cookie + CSRF |
| App Dashboard | ✅ 可用 | Bearer Token |
| 福利领取 API | 🔶 待验证 | Cookie + CSRF（推测使用 URL Reward API） |
| 连胜奖励 API | 🔶 待验证 | Cookie + CSRF（推测使用 URL Reward API） |
| 连胜保护 API | 🔶 待研究 | - |

---

## 技术参考

| 文档 | 说明 |
|------|------|
| [API完整文档.md](./2-reference/API完整文档.md) | API 端点汇总、请求/响应结构 |
| [TS项目分析.md](./2-reference/TS项目分析.md) | TypeScript 项目全盘分析 |
| [架构优化分析.md](./2-reference/架构优化分析.md) | URL/Quiz 任务迁移分析 |
