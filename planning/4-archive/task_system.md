# Microsoft Rewards 任务系统开发文档

## 页面结构详解

earn页面 (`https://rewards.bing.com/earn`) HTML结构：

```
<main>
├── section#quests (任务/Quest板块)
│   ├── 积分统计: <span class="font-semibold">50</span><span class="text-neutralFg3">/50</span>
│   └── <a href="/earn/quest/..."> 月度任务卡片 (4/4 个任务) </a>
│
├── section#moreactivities (继续赚取板块)
│   ├── 积分统计: <span class="font-semibold">40</span><span class="text-neutralFg3">/40</span>
│   └── grid容器 (lg:grid-cols-2 2xl:grid-cols-3)
│       ├── <a href="rewards.bing.com/referandearn/"> 推荐好友 (跳过) </a>
│       ├── <a href="rewards.bing.com/redeem/..."> 抽奖 (跳过) </a>
│       ├── <a href="microsoft-edge://..."> Edge搜索栏 (跳过) </a>
│       ├── <a href="bing.com/search?q=..."> 搜索任务 +15 </a>
│       ├── <a href="bing.com/search?q=...quiz"> Quiz +5 </a>
│       └── <a href="bing.com/spotlight/imagepuzzle"> 拼图 +5 </a>
│
└── section#microsoft (底部链接)
    └── <a href="bing.com, xbox.com, edge..."> (跳过)
```

### 板块积分统计

每个板块右上角有独立积分统计：

| 板块 | 积分元素 | 说明 |
|------|----------|------|
| 月度任务 | 50/50 | Quest卡片内的子任务总积分 |
| 继续赚取 | 40/40 | URL任务总积分 |

## 任务卡片HTML结构

```html
<a class="outline-0 cursor-pointer group" href="...">
  <!-- 标题区域 -->
  <div>壶铃锻炼</div>
  <div>用这种新型锻炼方式提升你的健康水平</div>

  <!-- 积分圆圈 -->
  <div class="flex rounded-full border border-neutralStroke1">
    <p class="text-caption1Stronger">+15</p>
  </div>
</a>
```

## 完成状态判断

### 方法1：圆圈CSS类名

| 状态 | circleClass特征 | 示例 |
|------|-----------------|------|
| 已完成 | `bg-statusSuccessBg3` + SVG勾选图标 | 月度任务 4/4 |
| 未完成 | `border border-neutralStroke1` | 搜索任务、Quiz、拼图 |
| 无积分 | 无circle元素 | 推荐好友、抽奖、Edge |

### 方法2：右上角总分（验证用）

```html
<span class="font-semibold">40</span><span class="text-neutralFg3">/40</span>
```

- **分子**：已获得积分
- **分母**：总可获得积分
- 用于验证任务完成情况

### 已完成示例

```html
<div class="... rounded-full ... bg-statusSuccessBg3 ...">50</div>
```

### 未完成示例

```html
<div class="... rounded-full ... border border-neutralStroke1">+15</div>
```

## 任务分类

### 可执行任务 (访问URL即可)

| 类型 | URL特征 | 积分 | 示例 |
|------|---------|------|------|
| 搜索任务 | `bing.com/search?q=...` | +15 | 壶铃锻炼、云朵解码 |
| Quiz | `bing.com/search?q=...quiz` | +5 | Bing Homepage quiz |
| 拼图 | `bing.com/spotlight/imagepuzzle` | +5 | 完成此拼图 |

### 应跳过的链接

| 类型 | URL特征 | 原因 |
|------|---------|------|
| Quest卡片 | `/earn/quest/...` | 包含多个子任务，需单独处理 |
| 推荐好友 | `/referandearn` | 非自动化任务 |
| 抽奖 | `/redeem/...` + 含"抽奖" | 需要手动参与 |
| Edge相关 | `microsoft-edge://` | 协议链接，无法访问 |
| Xbox | `xbox.com/Rewards` | 外部链接 |
| 关于页面 | `/about` | 静态页面 |
| 空文本链接 | text="" | 图标链接 |

## 代码实现要点

### 积分提取

```javascript
const pointsEl = el.querySelector('.text-caption1Stronger');
const num = pointsEl.innerText.trim().match(/\d+/);
```

### 完成状态检测

```javascript
const circleEl = el.querySelector('[class*="rounded-full"]');
if (circleEl.className.includes('bg-statusSuccessBg3')) return true;
if (circleEl.className.includes('border-neutralStroke1')) return false;
```

### 标题提取

```javascript
const lines = text.split('\n').filter(l => l.length > 2);
// 跳过: 纯数字、日期、进度(4/4)、积分(+15)
```

## 开发计划

### Phase 1 (当前)

- [x] 解析"继续赚取"板块URL任务
- [x] 完成状态检测
- [x] 单元测试通过 (22个测试)
- [x] 实战验证

### Phase 2

- [ ] Quest卡片子任务解析
- [ ] 连胜板块
- [ ] 升级活动板块

## 测试脚本

### 自动化测试

```bash
python tools/diagnose.py
```

- 自动加载会话或等待登录
- 解析任务并报告结果
- 保存结果到 `logs/diagnostics/`

### 任务识别测试

```bash
python tools/test_task_recognition.py
```

- 测试task_parser解析功能
- 显示任务详情和完成状态

### 页面结构诊断

```bash
python tools/diagnose_earn_page.py
```

- 分析页面HTML结构
- 保存诊断数据到 `logs/diagnostics/`

## 更新日志

### 2026-02-17

- 完成页面结构分析
- 确认任务卡片HTML结构
- 实现完成状态检测
- 更新task_parser.py
