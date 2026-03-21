# RewardsCore 开发规划

> 最后更新：2026-02-26
> 维护者：Master Agent (main 分支)

---

## 快速导航

| 章节 | 内容 |
|------|------|
| [一、分支并行开发](#一分支并行开发) | **当前重点**：Worktree 配置、依赖关系 |
| [二、开发阶段](#二开发阶段) | Phase 1-3 任务清单 |
| [三、待处理问题](#三待处理问题) | 按优先级排列 |
| [四、技术升级](#四技术升级) | 观察评估阶段：Patchright vs 自实现 |
| [五、文档导航](#五文档导航) | 详细文档链接 |

---

## 一、分支并行开发

### 当前 Worktree 状态

```
Worktree 路径                    分支                    状态
─────────────────────────────────────────────────────────────
RewardsCore/                    main                    🏠 基准（规划）
RewardsCore-dashboard/          feature/dashboard-api   🔄 开发中
RewardsCore-query/              feature/query-sources    🔄 开发中
RewardsCore-app/                feature/app-api         🔄 开发中
RewardsCore-benefits/          feature/benefits-collection  ⏳ 等待
RewardsCore-streak/             feature/streak-system   ⏳ 等待
```

### 分支依赖关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                        main (基准分支)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ dashboard-api │   │ query-sources │   │   app-api    │
│   (最高优先)  │   │   (高优先)    │   │   (中优先)    │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                  │                  │
        │ 合并后 ──────────┼──────────────────┘
        ▼                  ▼
┌───────────────┐   ┌───────────────┐
│ benefits-     │   │ streak-      │
│ collection    │   │ system        │
│ (依赖API数据) │   │ (依赖API数据) │
└───────────────┘   └───────────────┘
```

### 启动条件

| 分支 | 启动条件 | 当前状态 |
|------|----------|----------|
| `feature/dashboard-api` | 独立分支 | 🔄 开发中 |
| `feature/query-sources` | 独立分支 | 🔄 开发中 |
| `feature/app-api` | 独立分支 | 🔄 开发中 |
| `feature/benefits-collection` | dashboard-api 合并后 | ⏳ 等待 |
| `feature/streak-system` | dashboard-api 合并后 | ⏳ 等待 |

### 创建 Worktree 命令

```powershell
# 开发中分支
git worktree add ../RewardsCore-dashboard feature/dashboard-api
git worktree add ../RewardsCore-query feature/query-sources
git worktree add ../RewardsCore-app feature/app-api

# 等待中分支（dashboard-api 合并后执行）
git worktree add ../RewardsCore-benefits feature/benefits-collection
git worktree add ../RewardsCore-streak feature/streak-system

# 清理已合并分支
git worktree remove ../RewardsCore-constants
```

---

## 二、开发阶段

### Phase 1：基础设施（进行中）

| 任务 | 分支 | 优先级 | 状态 |
|------|------|--------|------|
| URL 常量集中 | constants-consolidation | 🟢 低 | ✅ #11 |
| Dashboard API 集成 | dashboard-api | 🔴 最高 | 🔄 开发中 |
| 查询源扩展 | query-sources | 🟡 高 | 🔄 开发中 |
| App API 集成 | app-api | 🟢 中 | 🔄 开发中 |

### Phase 2：功能扩展（等待 Phase 1）

| 任务 | 分支 | 依赖 | 状态 |
|------|------|------|------|
| 福利领取系统 | benefits-collection | dashboard-api | ⏳ |
| 连胜系统 | streak-system | dashboard-api | ⏳ |

### Phase 3：技术优化（观察评估阶段）

| 任务 | 说明 | 状态 |
|------|------|------|
| Patchright 评估 | 观察 Patchright Python 版成熟度 | 🟡 评估中 |
| task-api-migration | URL/Quiz 任务迁移到 API | � 评估中 |

---

## 三、待处理问题

### 🔴 高优先级

| # | 问题 | 行动 |
|---|------|------|
| 1 | dashboard-api 缺失 `monthly_level_bonus` 字段 | 通知分支补充 |
| 2 | 技术栈评估：Playwright vs Patchright | 持续观察，暂不执行 |

### 🟡 中优先级

| # | 问题 | 行动 |
|---|------|------|
| 3 | URL Reward API Token 获取方式 | ✅ 已解决（从页面提取 `__RequestVerificationToken`） |
| 4 | 福利领取 API 端点 | 🔶 待验证（推测使用 URL Reward API） |
| 5 | 连胜系统 API 端点 | 🔶 待验证（推测使用 URL Reward API） |
| 6 | 连胜保护 API 端点 | 🔶 待研究 |

---

## 四、技术升级（观察评估阶段）

> ⚠️ **当前立场**：暂不执行迁移，持续观察评估

### 评估方案

| 组件 | 当前方案 | 评估结论 | 状态 |
|------|----------|----------|------|
| 浏览器自动化 | Playwright | 暂保持，满足需求 | 🟢 稳定 |
| 反检测 | 自实现 anti_ban_module | 已覆盖主要场景 (~420行) | 🟢 稳定 |
| 鼠标模拟 | 自实现贝塞尔曲线 | 已完善 (~320行) | 🟢 稳定 |

### 何时考虑迁移？

- 自实现反检测被大规模检测到
- Playwright 官方停止维护
- Patchright Python 版生态成熟

---

## 五、文档导航

### 快速导航

| 章节 | 内容 |
|------|------|
| [一、分支并行开发](#一分支并行开发) | **当前重点**：Worktree 配置、依赖关系 |
| [二、开发阶段](#二开发阶段) | Phase 1-3 任务清单 |
| [三、待处理问题](#三待处理问题) | 按优先级排列 |
| [四、技术升级](#四技术升级) | 观察评估阶段：Patchright vs 自实现 |
| [六、预期收益](#六预期收益) | 福利领取、连胜系统 |

### 任务文档

| 状态 | 目录 | 内容 |
|------|------|------|
| 🔄 进行中 | `3-tasks/active/` | dashboard-api, query-sources, app-api |
| ⏳ 等待中 | `3-tasks/pending/` | benefits-collection, streak-system |
| ✅ 已完成 | `3-tasks/archive/` | constants-consolidation |

### 技术参考

| 文档 | 说明 |
|------|------|
| `2-reference/API完整文档.md` | API 端点汇总（Dashboard、App、Quiz、URL Reward、App Activities） |
| `2-reference/TS项目分析.md` | TypeScript 项目全盘分析 |
| `2-reference/架构优化分析.md` | URL/Quiz 任务迁移分析 |

### 文档入口

- **README.md**：[文档导航入口](../README.md)

---

## 六、预期收益

### 福利领取（月初 5 天内）

| 奖励类型 | 会员 | 银牌 | 金牌 |
|----------|------|------|------|
| Star 奖励 | 300 | 900 | 2100 |
| 升级奖励 | 60 | 180 | 420 |
| 默认搜索奖励 | 30 | 90 | 210 |
| **合计** | **390** | **1170** | **2730** |

### 连胜系统

| 类型 | 周奖励 | 月积分 |
|------|--------|--------|
| 搜索连胜 | 100 分 | ~480 |
| Edge 连胜 | 120 分 | ~480 |
| App 连胜 | 50 分 | ~200 |
| 印章奖励 | 1000 分 | - |

---

## 七、月度福利领取机制（2026-03-05 新增）

> **观察来源**：手动操作 Dashboard 页面分析

### 领取规则

| 规则 | 说明 |
|------|------|
| 领取时间 | 每月领取**上个月**的福利积分 |
| 有效期 | 领取后**整整 1 个月**内有效 |
| 操作方式 | 手动点击领取 |

### 页面元素定位

**步骤 1：点击"领取"入口**

```html
<div class="items-center justify-center bg-rewardsBgAlpha1 py-2 text-center font-semibold -mx-4 mt-2 -mb-3 mai:hidden">领取</div>
```

**步骤 2：点击"领取积分"按钮**

```html
<button class="inline-flex items-center justify-center transition-colors cursor-pointer group border outline-0 outline-neutralStrokeFocus2 forced-color-adjust-none bg-brandBg1 border-transparent text-neutralFgOnBrand outline-offset-1 px-4 py-2 gap-2 text-subtitle2 rounded-full" type="button">领取积分</button>
```

### 信息读取元素

**到期时间**

```html
<p class="text-caption1 mai:text-metadata text-neutralFg2 mai:text-fgCtrlNeutralSecondaryRest">到期日期 1个月后</p>
```

**积分数量**

```html
<div class="py-3 wrap-anywhere justify-self-end not-mai:text-neutralFg2 not-mai:text-body1Strong">420</div>
```

### 自动化实现要点

1. **定位策略**：使用 class 组合 + 文本内容双重定位
2. **时序**：每月初 5 天内执行
3. **验证**：领取后检查到期时间是否正确更新
4. **错误处理**：如果已领取，跳过并记录

### 待实现分支

- `feature/benefits-collection` — 依赖 `dashboard-api` 合并后启动
