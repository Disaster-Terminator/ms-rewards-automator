# 调度器模块文档

## 一、功能概述

调度器模块提供定时任务执行功能，支持：

- **时区选择** - 支持 IANA 时区格式
- **定时+随机偏移** - 用户选择整点时间，脚本在偏移范围内随机执行
- **启动执行一次** - 程序启动时立即执行任务，然后进入调度模式

---

## 二、配置说明

### 2.1 基础配置

```yaml
scheduler:
  enabled: true                    # 默认启用
  timezone: "Asia/Shanghai"        # 时区设置
  mode: "scheduled"                # 调度模式
  run_once_on_start: true          # 启动时先执行一次
  scheduled_hour: 17               # 基准执行时间
  max_offset_minutes: 45           # 随机偏移范围
```

### 2.2 默认值说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `enabled` | `true` | 调度器默认启用 |
| `scheduled_hour` | `17` | 北京时间 17:00（积分重置后） |
| `max_offset_minutes` | `45` | 执行时间范围 16:15-17:45 |

### 2.3 调度模式

| 模式 | 配置值 | 说明 |
|------|--------|------|
| **定时+随机偏移** | `scheduled` | 整点时间 ± 偏移量随机执行（推荐） |
| **随机范围** | `random` | 在时间范围内随机选择 |
| **固定时间** | `fixed` | 每天固定时间执行 |

---

## 三、调度器行为

### 3.1 默认行为

```
python main.py 执行流程：
┌─────────────────────────────────────────┐
│ 1. 执行一次任务（登录+搜索）              │
│ 2. 计算下次执行时间                      │
│ 3. 等待到执行时间                        │
│ 4. 执行任务                              │
│ 5. 循环步骤 2-4                         │
└─────────────────────────────────────────┘
```

### 3.2 禁用调度器

**方式一：配置文件**

```yaml
scheduler:
  enabled: false
```

**方式二：使用 --dev 或 --user 参数**

```bash
python main.py --dev   # 调度器自动禁用
python main.py --user  # 调度器自动禁用
```

### 3.3 为什么默认启用

- 用户期望程序自动执行，无需手动干预
- 通过配置禁用比通过命令行启用更直观
- 微软积分每日重置，自动调度确保不错过

---

## 四、时区设置

### 4.1 支持的时区格式

使用 IANA 时区数据库格式：

| 时区字符串 | 说明 |
|------------|------|
| `Asia/Shanghai` | 中国标准时间 (UTC+8) |
| `Asia/Tokyo` | 日本标准时间 (UTC+9) |
| `America/New_York` | 美国东部时间 |
| `Europe/London` | 英国时间 |
| `UTC` | 协调世界时 |

---

## 五、执行时间计算

### 5.1 定时+随机偏移模式（推荐）

```yaml
scheduler:
  mode: "scheduled"
  scheduled_hour: 17           # 基准时间 17:00
  max_offset_minutes: 45       # 偏移 ±45 分钟
```

**执行时间范围**：16:15 - 17:45（北京时间）

### 5.2 为什么选择 17:00

| 因素 | 分析 |
|------|------|
| 积分重置 | 北京时间 15:00-16:00 重置，17:00 执行确保从零开始 |
| 服务器负载 | 美国凌晨时段，服务器最空闲 |
| 用户习惯 | 傍晚时段，用户更可能在线检查 |

---

## 六、测试模式

用于验收测试，设置延迟秒数后快速执行：

```yaml
scheduler:
  test_delay_seconds: 30    # 30秒后执行
```

---

## 七、完整配置示例

```yaml
scheduler:
  enabled: true
  timezone: "Asia/Shanghai"
  mode: "scheduled"
  run_once_on_start: true
  scheduled_hour: 17
  max_offset_minutes: 45
  
  # 随机范围模式（mode: random）
  random_start_hour: 8
  random_end_hour: 22
  
  # 固定模式（mode: fixed）
  fixed_hour: 10
  fixed_minute: 0
  
  # 测试模式
  test_delay_seconds: 0
```

---

## 八、常见问题

### Q: 如何禁用调度器？

A: 在配置文件中设置 `scheduler.enabled: false`，或使用 `--dev`/`--user` 参数。

### Q: 为什么需要随机偏移？

A: 避免每天固定时间执行被检测为自动化行为，增加随机性更接近真实用户。

### Q: 时区设置有什么作用？

A: 如果服务器在国外，但希望按中国时间执行，设置 `timezone: "Asia/Shanghai"` 即可。
