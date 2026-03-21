# TASK: 福利领取系统

> 分支: `feature/benefits-collection`
> 并行组: 第二组
> 优先级: 🟡 高
> 预计时间: 3-4 天
> 依赖: `feature/dashboard-api`

***

## 一、目标

实现月初 5 天内的福利自动领取功能。

***

## 二、背景

### 2.1 福利类型

| 类型 | 说明 | 会员 | 银牌 | 金牌 |
|------|------|------|------|------|
| Star 奖励 | 每月领取（最高） | 300 | 900 | 2100 |
| 升级奖励 | 每月领取 | 60 | 180 | 420 |
| 默认搜索奖励 | 每月领取 | 30 | 90 | 210 |
| **合计** | - | **390** | **1170** | **2730** |

> **注**：Star 奖励需要真实使用必应才能获得更多积分，"打卡"用户可能只能获得少量积分。

### 2.2 数据来源

Dashboard API 提供以下数据：

**升级奖励**：

- `monthlyLevelBonusProgress` - 月度福利进度
- `monthlyLevelBonusMaximum` - 月度福利最大值
- `monthlyLevelBonusState` - 月度福利状态

**Star 奖励**：

- `bingStarMonthlyBonusProgress` - Star 奖励进度
- `bingStarMonthlyBonusMaximum` - Star 奖励最大值

**默认搜索奖励**：

- `defaultSearchEngineMonthlyBonusProgress` - 默认搜索奖励进度
- `defaultSearchEngineMonthlyBonusMaximum` - 默认搜索奖励最大值
- `defaultSearchEngineMonthlyBonusState` - 默认搜索奖励状态

***

## 三、任务清单

### 3.1 BenefitsCollector 实现

- [ ] 创建 `src/benefits/__init__.py`
- [ ] 创建 `src/benefits/collector.py`
  - [ ] `check_eligibility()` - 检查是否有可领取福利
  - [ ] `collect_monthly_bonus()` - 领取月度福利
  - [ ] `collect_level_up_bonus()` - 领取升级福利
  - [ ] `collect_default_search_bonus()` - 领取默认搜索引擎奖励

### 3.2 日期检测

- [ ] 检测当前日期是否在月初 5 天内
- [ ] 检测是否有未领取的福利

### 3.3 领取逻辑

- [ ] 使用 Dashboard API 获取福利数据
- [ ] 解析福利板块 HTML 结构（fallback）
- [ ] 执行领取操作

### 3.4 测试

- [ ] 创建 `tests/unit/test_benefits_collector.py`
- [ ] 测试日期检测逻辑
- [ ] 测试领取逻辑

***

## 四、参考资源

### 4.1 Dashboard API 数据

```json
{
  "userStatus": {
    "levelInfo": {
      "monthlyLevelBonusProgress": 0,
      "monthlyLevelBonusMaximum": 420,
      "monthlyLevelBonusState": "incomplete"
    }
  }
}
```

### 4.2 关键代码参考

```python
class BenefitsCollector:
    async def collect_monthly_bonus(self) -> int:
        if not self._is_early_month():
            return 0
        
        dashboard = await self.dashboard_client.get_dashboard_data()
        bonus_data = dashboard.user_status.level_info
        
        if bonus_data.monthly_level_bonus_progress < bonus_data.monthly_level_bonus_maximum:
            return await self._execute_collection()
        
        return 0
```

***

## 五、预期收益

| 奖励类型 | 会员 | 银牌 | 金牌 |
|----------|------|------|------|
| Star 奖励（最高） | 300 | 900 | 2100 |
| 升级奖励 | 60 | 180 | 420 |
| 默认搜索奖励 | 30 | 90 | 210 |
| **合计** | **390** | **1170** | **2730** |

> **重要**：Star 奖励需要真实使用必应搜索才能获得更多积分。纯"打卡"用户可能只能获得少量积分。

***

## 六、验收标准

- [ ] 可检测是否有可领取福利
- [ ] 可成功领取月度福利
- [ ] 日期检测逻辑正确
- [ ] 单元测试覆盖率 > 80%

***

## 七、合并条件

- [ ] 所有测试通过
- [ ] Code Review 通过
- [ ] 依赖分支 `feature/dashboard-api` 已合并
