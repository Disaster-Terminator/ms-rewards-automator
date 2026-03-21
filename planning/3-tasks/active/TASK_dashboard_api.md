# TASK: Dashboard API 集成

> 分支: `feature/dashboard-api`
> 并行组: 第一组
> 优先级: 🔴 最高
> 预计时间: 3-4 天
> 依赖: 无

***

## 一、目标

利用已验证可用的 Dashboard API，增强积分检测能力，替代现有的 HTML 解析方案。

***

## 二、背景

### 2.1 API 验证结果

| API | 状态 | HTTP 状态码 | 备注 |
|-----|------|-------------|------|
| Dashboard API | ✅ 可用 | 200 | 返回完整用户数据 |

### 2.2 API 端点

```
GET https://rewards.bing.com/api/getuserinfo?type=1
Headers:
  Cookie: {session_cookies}
  Referer: https://rewards.bing.com/
```

### 2.3 响应示例

```json
{
  "dashboard": {
    "userStatus": {
      "levelInfo": {
        "activeLevel": "newLevel3",
        "activeLevelName": "Gold Member",
        "progress": 1790,
        "progressMax": 750
      },
      "availablePoints": 12345,
      "counters": {
        "pcSearch": [...],
        "mobileSearch": [...]
      }
    },
    "dailySetPromotions": {...},
    "morePromotions": [...],
    "punchCards": [...]
  }
}
```

***

## 三、任务清单

### 3.1 数据结构定义

- [ ] 创建 `src/api/__init__.py`
- [ ] 创建 `src/api/models.py`
  - [ ] `DashboardData` dataclass
  - [ ] `UserStatus` dataclass
  - [ ] `LevelInfo` dataclass
  - [ ] `Counters` dataclass
  - [ ] `Promotion` dataclass
  - [ ] `PunchCard` dataclass

### 3.2 DashboardClient 实现

- [ ] 创建 `src/api/dashboard_client.py`
  - [ ] `get_dashboard_data()` - 获取完整 Dashboard 数据
  - [ ] `get_search_counters()` - 获取搜索计数器
  - [ ] `get_level_info()` - 获取会员等级信息
  - [ ] `get_promotions()` - 获取推广任务列表
  - [ ] `get_current_points()` - 获取当前积分

### 3.3 HTML Fallback 机制

- [ ] 实现 API 失败时的 HTML 解析 fallback
- [ ] 从页面脚本提取 `var dashboard = {...}`

### 3.4 集成与测试

- [ ] 更新 `PointsDetector` 使用新 API
- [ ] 创建 `tests/unit/test_dashboard_client.py`
- [ ] 验证积分检测准确性

***

## 四、参考资源

### 4.1 TS 项目参考

| 文件 | 路径 |
|------|------|
| Dashboard API 实现 | `Microsoft-Rewards-Script/src/browser/BrowserFunc.ts` |
| 数据结构定义 | `Microsoft-Rewards-Script/src/interface/DashboardData.ts` |

### 4.2 关键代码参考

```python
async def get_dashboard_data(self) -> DashboardData:
    try:
        response = await self._call_api()
        if response.data and response.data.get('dashboard'):
            return self._parse_dashboard(response.data['dashboard'])
    except Exception as e:
        self.logger.warn(f"API failed: {e}, trying HTML fallback")
        return await self._html_fallback()
    raise DashboardError("Failed to get dashboard data")
```

***

## 五、验收标准

- [ ] DashboardClient 可成功调用 API
- [ ] 返回完整的用户数据（积分、等级、任务）
- [ ] HTML fallback 机制正常工作
- [ ] 单元测试覆盖率 > 80%
- [ ] 无 mypy 类型错误

***

## 六、合并条件

- [ ] 所有测试通过
- [ ] Code Review 通过
- [ ] 文档更新完成
