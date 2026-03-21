# TASK: 连胜系统

> 分支: `feature/streak-system`
> 并行组: 第二组
> 优先级: 🟢 低
> 预计时间: 2-3 天
> 依赖: `feature/dashboard-api`

***

## 一、目标

实现搜索/Edge/App 连胜积分获取和印章收集：

| 连胜类型 | 每日任务 | 周奖励 | 印章 |
|----------|----------|--------|------|
| 搜索连胜 | 搜索 3 次 | 100 分 | 1 个 |
| Edge 连胜 | 前台浏览 30 分钟 | 120 分 | 1 个 |
| App 连胜 | App 签到 | 50 分 | 1 个 |

**印章收集**：12 印章 → 1000 分奖励

***

## 二、背景

### 2.1 连胜类型

| 类型 | 每日任务 | 周奖励 | 印章 | 月积分（约） |
|------|----------|--------|------|-------------|
| 搜索连胜 | 搜索 3 次 | 100 分 + 1 印章 | 最多 4 个/月 | ~400 分 |
| Edge 连胜 | 前台浏览 30 分钟 | 120 分 + 1 印章 | 最多 4 个/月 | ~480 分 |
| App 连胜 | App 签到 | 50 分 + 1 印章 | 最多 4 个/月 | ~200 分 |
| **印章奖励** | - | - | 12 印章 | 1000 分 |

> **注**：印章收集需要 3 种连胜都参与才能快速收集。

### 2.2 数据来源

Dashboard API 提供以下数据：

- `streakPromotion` - 连胜推广数据
- `streakBonusPromotions` - 连胜奖励列表

***

## 三、任务清单

### 3.1 StreakTracker 实现

- [ ] 创建 `src/streaks/__init__.py`
- [ ] 创建 `src/streaks/tracker.py`
  - [ ] `get_streak_status()` - 获取连胜状态
  - [ ] `get_streak_bonus()` - 获取连胜奖励
  - [ ] `check_streak_risk()` - 检查连胜风险
  - [ ] `get_streak_reminder()` - 获取连胜提醒

### 3.2 数据结构

```python
@dataclass
class StreakStatus:
    current_streak: int
    max_streak: int
    last_activity_date: datetime | None
    is_at_risk: bool
    days_until_bonus: int
```

### 3.3 提醒机制

- [ ] 检测连胜是否即将中断
- [ ] 生成提醒消息
- [ ] 集成到通知系统

### 3.4 测试

- [ ] 创建 `tests/unit/test_streak_tracker.py`
- [ ] 测试连胜状态检测
- [ ] 测试风险检测逻辑

***

## 四、参考资源

### 4.1 Dashboard API 数据

```json
{
  "streakPromotion": {
    "attributes": {
      "activity_progress": "5",
      "lifetime_max": "30",
      "bonus_points": "150"
    }
  },
  "streakBonusPromotions": [...]
}
```

### 4.2 关键代码参考

```python
class StreakTracker:
    async def get_streak_status(self) -> StreakStatus:
        dashboard = await self.dashboard_client.get_dashboard_data()
        streak_data = dashboard.streak_promotion
        
        return StreakStatus(
            current_streak=int(streak_data.attributes.activity_progress),
            max_streak=int(streak_data.attributes.lifetime_max),
            is_at_risk=self._check_risk(streak_data)
        )
```

***

## 五、预期收益

| 来源 | 月积分（约） |
|------|-------------|
| 搜索连胜 | ~400 分 |
| Edge 连胜 | ~480 分 |
| App 连胜 | ~200 分 |
| 印章奖励（12 个） | 1000 分 |
| **合计** | **~2080 分** |

> **注**：实际收益取决于用户参与程度和连胜保持情况。

***

## 六、验收标准

- [ ] 可获取连胜状态
- [ ] 可检测连胜风险
- [ ] 可生成提醒消息
- [ ] 单元测试覆盖率 > 80%

***

## 六、合并条件

- [ ] 所有测试通过
- [ ] Code Review 通过
- [ ] 依赖分支 `feature/dashboard-api` 已合并
