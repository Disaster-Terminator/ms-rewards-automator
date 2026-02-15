# 调度器模块文档

## 一、功能概述

调度器模块提供定时任务执行功能，支持：

- **时区选择** - 支持 IANA 时区格式
- **定时+随机偏移** - 用户选择整点时间，脚本在偏移范围内随机执行
- **启动执行一次** - 程序启动时立即执行任务，然后进入调度模式
- **命令行参数控制** - 灵活控制调度行为

---

## 二、配置说明

### 2.1 基础配置

```yaml
scheduler:
  enabled: true                    # 是否启用调度器
  timezone: "Asia/Shanghai"        # 时区设置
  mode: "scheduled"                # 调度模式
  run_once_on_start: true          # 启动时先执行一次
```

### 2.2 调度模式

| 模式 | 配置值 | 说明 | 适用场景 |
|------|--------|------|----------|
| **定时+随机偏移** | `scheduled` | 整点时间 ± 偏移量随机执行 | **推荐**：每天固定时段随机执行 |
| **随机范围** | `random` | 在时间范围内随机选择 | 需要更大随机范围 |
| **固定时间** | `fixed` | 每天固定时间执行 | 需要精确控制时间 |

### 2.3 各模式配置

#### 定时+随机偏移模式（推荐）

```yaml
scheduler:
  mode: "scheduled"
  scheduled_hour: 10           # 基准整点时间（如 10 表示 10:00）
  max_offset_minutes: 30       # 最大偏移量（分钟）
```

**执行时间范围**：`scheduled_hour - max_offset_minutes` 到 `scheduled_hour + max_offset_minutes`

示例：`scheduled_hour: 10, max_offset_minutes: 30` → 执行时间在 9:30 ~ 10:30 之间随机

#### 随机范围模式

```yaml
scheduler:
  mode: "random"
  random_start_hour: 8         # 随机时间范围起始
  random_end_hour: 22          # 随机时间范围结束
```

**执行时间范围**：`random_start_hour:00` 到 `random_end_hour:59`

#### 固定时间模式

```yaml
scheduler:
  mode: "fixed"
  fixed_hour: 10               # 固定小时
  fixed_minute: 0              # 固定分钟
```

---

## 三、时区设置

### 3.1 支持的时区格式

使用 IANA 时区数据库格式：

| 时区字符串 | 说明 |
|------------|------|
| `Asia/Shanghai` | 中国标准时间 (UTC+8) |
| `Asia/Tokyo` | 日本标准时间 (UTC+9) |
| `Asia/Hong_Kong` | 香港时间 (UTC+8) |
| `Asia/Singapore` | 新加坡时间 (UTC+8) |
| `America/New_York` | 美国东部时间 |
| `America/Los_Angeles` | 美国太平洋时间 |
| `Europe/London` | 英国时间 |
| `Europe/Paris` | 欧洲中部时间 |
| `UTC` | 协调世界时 |

### 3.2 时区工作原理

```python
from zoneinfo import ZoneInfo
from datetime import datetime

# 获取指定时区的当前时间
now = datetime.now(ZoneInfo("Asia/Shanghai"))
# 结果: 2026-02-15 22:30:00+08:00
```

---

## 四、命令行参数

| 参数 | 说明 |
|------|------|
| `python main.py` | 执行一次 + 进入调度（当 `scheduler.enabled: true`） |
| `python main.py --no-schedule` | 仅执行一次，不进入调度（覆盖配置） |
| `python main.py --schedule-only` | 跳过首次执行，直接进入调度模式 |

---

## 五、执行流程

```
程序启动
    │
    ▼
┌─────────────────────────────────────┐
│ 检查 scheduler.enabled 配置          │
│ 检查 --no-schedule 参数              │
└─────────────────────────────────────┘
    │
    ├── enabled=false 或 --no-schedule
    │       │
    │       ▼
    │   ┌─────────────┐
    │   │ 执行一次任务 │
    │   └─────────────┘
    │
    └── enabled=true
            │
            ▼
        ┌─────────────────────────────────────┐
        │ 检查 --schedule-only 参数            │
        └─────────────────────────────────────┘
            │
            ├── 无参数（默认）
            │       │
            │       ▼
            │   ┌─────────────────┐
            │   │ 执行一次任务     │
            │   │ (run_once_on_start) │
            │   └─────────────────┘
            │
            └── --schedule-only
                    │
                    ▼
                跳过首次执行
                    │
                    ▼
        ┌─────────────────────────────────────┐
        │ 计算下次执行时间                     │
        │ (根据 mode 和时区)                   │
        └─────────────────────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────────┐
        │ 等待到执行时间                       │
        └─────────────────────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────────┐
        │ 执行任务                             │
        └─────────────────────────────────────┘
                    │
                    ▼
                循环等待
```

---

## 六、测试模式

用于验收测试，设置延迟秒数后快速执行：

```yaml
scheduler:
  test_delay_seconds: 30    # 30秒后执行（验收完成后改回0）
```

---

## 七、完整配置示例

```yaml
scheduler:
  # 基础配置
  enabled: true
  timezone: "Asia/Shanghai"
  mode: "scheduled"
  run_once_on_start: true
  
  # 定时+随机偏移模式（mode: scheduled）
  scheduled_hour: 10
  max_offset_minutes: 30
  
  # 随机范围模式（mode: random）
  random_start_hour: 8
  random_end_hour: 22
  
  # 固定时间模式（mode: fixed）
  fixed_hour: 10
  fixed_minute: 0
  
  # 测试模式
  test_delay_seconds: 0
```

---

## 八、常见问题

### Q: 为什么需要随机偏移？

A: 避免每天固定时间执行被检测为自动化行为，增加随机性更接近真实用户。

### Q: 时区设置有什么作用？

A: 如果服务器在国外，但希望按中国时间执行，设置 `timezone: "Asia/Shanghai"` 即可。

### Q: 如何禁用调度器？

A: 设置 `scheduler.enabled: false` 或使用 `--no-schedule` 参数。

### Q: 如何只执行一次不进入调度？

A: 使用 `python main.py --no-schedule` 参数。
