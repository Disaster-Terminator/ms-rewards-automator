# MS-Rewards-Automator-search 修复任务清单

## 确认的设计决策

| 决策项 | 确认结果 |
|--------|----------|
| 拟人化行为强度 | 可配置 + 智能混合，默认 `medium` |
| 在线搜索词源优先级 | DuckDuckGo > Wikipedia > Google Trends > Reddit |
| 单元测试 | 必须编写 |

---

## ✅ 已完成任务

### 一、核心问题修复 [P0]

#### 1. ✅ 拟人化行为集成到搜索功能

**修复内容**：

- [x] 在 `SearchEngine` 中集成 `HumanBehaviorSimulator`
- [x] 添加配置项 `anti_detection.human_behavior_level`: `light` / `medium` / `heavy`
- [x] 实现三个等级的行为
- [x] 添加 `_human_input_search_term()` 方法
- [x] 添加 `_human_submit_search()` 方法

**涉及文件**：

- `src/search/search_engine.py`
- `src/infrastructure/config_manager.py`

---

#### 2. ✅ 健康检测器浏览器注册

**修复内容**：

- [x] 在 `MSRewardsApp._create_browser()` 中调用 `health_monitor.register_browser()`

**涉及文件**：

- `src/infrastructure/ms_rewards_app.py`

---

#### 3. ✅ 搜索进度显示时机修复

**修复内容**：

- [x] 将进度更新移到搜索成功后
- [x] 使用依赖注入的 `status_manager` 替代动态导入

**涉及文件**：

- `src/search/search_engine.py`

---

### 二、功能优化 [P1]

#### 4. ✅ 动态导入改为依赖注入

**修复内容**：

- [x] 在 `SearchEngine.__init__` 中注入 `status_manager`
- [x] 移除循环内的动态导入
- [x] 移除空的 `except Exception: pass`

**涉及文件**：

- `src/search/search_engine.py`

---

#### 5. ✅ 搜索间隔随机化改进

**修复内容**：

- [x] 改用正态分布（均值居中，标准差合理）
- [x] 添加 10% 概率的"长停顿"（模拟思考）

**涉及文件**：

- `src/browser/anti_ban_module.py`

---

#### 6. ✅ 搜索结果验证增强

**修复内容**：

- [x] 检查搜索结果数量是否 > 0
- [x] 验证搜索词是否出现在页面标题
- [x] 添加 `_verify_search_result()` 方法

**涉及文件**：

- `src/search/search_engine.py`

---

### 三、新功能开发 [P2]

#### 7. ✅ 在线获取搜索词功能

**开发内容**：

- [x] 创建 `DuckDuckGoSource` 类
- [x] 创建 `WikipediaSource` 类
- [x] 更新 `QueryEngine` 支持多源合并
- [x] 添加配置项控制在线源开关

**涉及文件**：

- `src/search/query_sources/duckduckgo_source.py`（新建）
- `src/search/query_sources/wikipedia_source.py`（新建）
- `src/search/query_engine.py`
- `src/infrastructure/config_manager.py`

---

#### 8. ✅ 显示闪烁修复

**修复内容**：

- [x] 使用 ANSI 转义序列 `\033[2J\033[H` 替代 `os.system()`

**涉及文件**：

- `src/ui/real_time_status.py`

---

## 测试结果

```
tests/unit/test_health_monitor.py: 21 passed
tests/unit/test_query_sources.py: 8 passed
tests/unit/test_query_engine_core.py: 5 passed
tests/unit/test_query_cache.py: 4 passed
tests/unit/test_config_manager.py: 10 passed
tests/unit/test_config_validator.py: 24 passed

Total: 72 passed
```

---

## 配置项变更

### 新增配置项

```yaml
anti_detection:
  human_behavior_level: "medium"  # light / medium / heavy
  mouse_movement:
    enabled: true
    micro_movement_probability: 0.3
  typing:
    use_gaussian_delay: true
    avg_delay_ms: 120
    std_delay_ms: 30
    pause_probability: 0.1

query_engine:
  sources:
    duckduckgo:
      enabled: true
    wikipedia:
      enabled: true
```

---

## 代码质量检查

```
ruff check: All checks passed!
```
