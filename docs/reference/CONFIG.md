# 配置文件参考

> 最后更新: 2026-02-24

## 一、执行模式配置

```yaml
execution:
  mode: "normal"  # fast(快速), normal(默认), slow(安全)
```

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `mode` | normal | 执行速度模式 |

**执行模式预设**：

| 模式 | wait_interval | slow_mo | 说明 |
|------|---------------|---------|------|
| `fast` | 2-5秒 | 50ms | 快速模式，适合测试环境 |
| `normal` | 5-15秒 | 100ms | 默认模式，速度与安全平衡 |
| `slow` | 15-30秒 | 200ms | 安全模式，更接近人工操作 |

---

## 二、搜索配置

```yaml
search:
  desktop_count: 20              # 桌面端搜索次数
  mobile_count: 0                # 移动端搜索次数（已禁用）
  wait_interval:
    min: 5                       # 最小等待时间（秒）
    max: 15                      # 最大等待时间（秒）
  search_terms_file: "tools/search_terms.txt"
```

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `desktop_count` | 20 | 桌面搜索次数 |
| `mobile_count` | 0 | 移动搜索次数（已禁用） |
| `wait_interval.min` | 5 | 最小等待时间 |
| `wait_interval.max` | 15 | 最大等待时间 |

---

## 三、浏览器配置

```yaml
browser:
  headless: false                # 是否无头模式
  type: "chromium"               # 浏览器类型
  prevent_focus: "basic"         # 防焦点模式
  slow_mo: 100                   # 操作延迟（毫秒）
  timeout: 30000                 # 页面加载超时（毫秒）
```

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `headless` | false | 无头模式（后台运行） |
| `type` | chromium | 浏览器类型：chromium/edge/chrome |
| `prevent_focus` | basic | 防焦点模式：basic/enhanced/none |
| `slow_mo` | 100 | 操作延迟（毫秒） |
| `timeout` | 30000 | 页面加载超时（毫秒） |

---

## 四、登录配置

```yaml
login:
  state_machine_enabled: true    # 启用状态机登录流程
  max_transitions: 20            # 最大状态转换次数
  timeout_seconds: 300           # 登录超时（秒）
  stay_signed_in: true           # 保持登录状态
  manual_intervention_timeout: 120  # 手动干预等待时间（秒）

  auto_login:
    enabled: false               # 是否启用自动登录
    email: ""                    # Microsoft 账号
    password: ""                 # 密码
    totp_secret: ""              # 2FA 密钥
```

**推荐**：使用手动登录（首次运行时浏览器打开，手动登录后保存会话）。

---

## 五、调度器配置

```yaml
scheduler:
  enabled: true                  # 默认启用
  timezone: "Asia/Shanghai"
  mode: "scheduled"
  scheduled_hour: 17             # 基准执行时间
  max_offset_minutes: 45         # 随机偏移范围
```

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `enabled` | true | 是否启用调度器 |
| `timezone` | Asia/Shanghai | 时区 |
| `mode` | scheduled | 调度模式 |
| `scheduled_hour` | 17 | 基准执行时间 |
| `max_offset_minutes` | 45 | 随机偏移范围 |

**禁用调度器**：设置 `enabled: false`，程序执行一次后退出。

详细说明参见 [调度器文档](SCHEDULER.md)。

---

## 六、通知配置

```yaml
notification:
  enabled: false
  telegram:
    enabled: false
    bot_token: ""
    chat_id: ""
  serverchan:
    enabled: false
    key: ""
  whatsapp:
    enabled: false
    phone: ""
    apikey: ""
```

| 配置项 | 说明 |
|--------|------|
| `telegram.bot_token` | Telegram Bot Token |
| `telegram.chat_id` | Telegram Chat ID |
| `serverchan.key` | Server酱 SendKey |
| `whatsapp.phone` | WhatsApp 手机号 |
| `whatsapp.apikey` | WhatsApp API Key |

---

## 七、任务系统配置

```yaml
task_system:
  enabled: false                 # 是否启用每日任务
  min_delay: 2                   # 任务间最小延迟（秒）
  max_delay: 5                   # 任务间最大延迟（秒）
  skip_completed: true           # 跳过已完成任务
  debug_mode: false
  task_types:
    url_reward: true             # URL奖励任务
    quiz: false                  # 问答任务
    poll: false                  # 投票任务
```

---

## 八、查询引擎配置

```yaml
query_engine:
  enabled: true                  # 启用在线查询源
  cache_ttl: 3600                # 缓存有效期（秒）
  sources:
    local_file:
      enabled: true              # 本地搜索词文件
    bing_suggestions:
      enabled: true              # Bing 建议API
  bing_api:
    rate_limit: 10               # 请求速率限制
    max_retries: 3               # 最大重试次数
    timeout: 15                  # 超时（秒）
```

---

## 九、Bing 主题配置

```yaml
bing_theme:
  enabled: true                  # 启用主题管理
  theme: "dark"                  # 主题类型: dark 或 light
  force_theme: true              # 强制应用主题
  persistence_enabled: true      # 启用会话间主题持久化
  theme_state_file: "logs/theme_state.json"  # 主题状态文件路径
```

---

## 十、监控配置

```yaml
monitoring:
  enabled: true                  # 启用监控
  check_interval: 5              # 检查间隔（秒）
  check_points_before_task: true # 任务前检查积分
  alert_on_no_increase: true     # 积分不增长时告警
  max_no_increase_count: 3       # 最大不增长次数
  real_time_display: true        # 实时显示
  health_check:
    enabled: true                # 启用健康检查
    interval: 30                 # 检查间隔（秒）
    save_reports: true           # 保存报告
```

---

## 十一、错误处理配置

```yaml
error_handling:
  max_retries: 3                 # 最大重试次数
  retry_delay: 5                 # 重试延迟（秒）
  exponential_backoff: true      # 指数退避
```

---

## 十二、日志配置

```yaml
logging:
  level: "INFO"                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "logs/automator.log"
  console: true
```

---

## 十三、完整配置示例

```yaml
search:
  desktop_count: 20
  mobile_count: 0
  wait_interval:
    min: 5
    max: 15

browser:
  headless: false
  type: "chromium"
  prevent_focus: "basic"
  slow_mo: 100
  timeout: 30000

account:
  storage_state_path: "storage_state.json"
  login_url: "https://rewards.microsoft.com/"

login:
  state_machine_enabled: true
  max_transitions: 20
  timeout_seconds: 300
  stay_signed_in: true
  manual_intervention_timeout: 120
  auto_login:
    enabled: false

query_engine:
  enabled: true
  cache_ttl: 3600

task_system:
  enabled: false
  min_delay: 2
  max_delay: 5
  skip_completed: true

bing_theme:
  enabled: true
  theme: "dark"
  force_theme: true
  persistence_enabled: true

monitoring:
  enabled: true
  check_interval: 5
  check_points_before_task: true
  alert_on_no_increase: true
  max_no_increase_count: 3
  real_time_display: true
  health_check:
    enabled: true
    interval: 30
    save_reports: true

notification:
  enabled: false
  telegram:
    enabled: false
    bot_token: ""
    chat_id: ""

scheduler:
  enabled: true
  timezone: "Asia/Shanghai"
  mode: "scheduled"
  scheduled_hour: 17
  max_offset_minutes: 45

error_handling:
  max_retries: 3
  retry_delay: 5
  exponential_backoff: true

logging:
  level: "INFO"
  file: "logs/automator.log"
  console: true
```
