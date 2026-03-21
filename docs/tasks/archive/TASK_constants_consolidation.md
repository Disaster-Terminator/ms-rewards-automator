# TASK: URL 常量集中

> 分支: `refactor/constants-consolidation`
> 并行组: 第一组
> 优先级: 🟢 低
> 预计时间: 1 天
> 依赖: 无

***

## 一、目标

解决 URL 硬编码问题，集中管理所有 URL 常量。

***

## 二、背景

### 2.1 当前问题

项目中存在多处 URL 硬编码：

- `src/account/points_detector.py`
- `src/tasks/task_parser.py`
- `src/search/search_engine.py`
- 其他模块

### 2.2 目标

创建统一的常量模块，便于维护和更新。

***

## 三、任务清单

### 3.1 创建常量模块

- [ ] 创建 `src/constants/__init__.py`
- [ ] 创建 `src/constants/urls.py`

### 3.2 URL 常量定义

```python
REWARDS_URLS = {
    "earn": "https://rewards.bing.com/earn",
    "dashboard": "https://rewards.microsoft.com/dashboard",
    "rewards_home": "https://rewards.microsoft.com/",
    "bing": "https://www.bing.com",
    "bing_search": "https://www.bing.com/search",
}

API_ENDPOINTS = {
    "dashboard": "https://rewards.bing.com/api/getuserinfo?type=1",
    "report_activity": "https://rewards.bing.com/api/reportactivity",
    "quiz": "https://www.bing.com/bingqa/ReportActivity",
    "app_dashboard": "https://prod.rewardsplatform.microsoft.com/dapi/me",
    "app_activities": "https://prod.rewardsplatform.microsoft.com/dapi/me/activities",
}

OAUTH_CONFIG = {
    "client_id": "0000000040170455",
    "auth_url": "https://login.live.com/oauth20_authorize.srf",
    "redirect_url": "https://login.live.com/oauth20_desktop.srf",
    "token_url": "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    "scope": "service::prod.rewardsplatform.microsoft.com::MBI_SSL",
}

QUERY_SOURCE_URLS = {
    "bing_suggestions": "https://api.bing.com/osjson.aspx",
    "duckduckgo": "https://duckduckgo.com/ac/",
    "wikipedia_top_views": "https://wikimedia.org/api/rest_v1/metrics/pageviews/top",
    "wikipedia_random": "https://en.wikipedia.org/api/rest_v1/page/random/summary",
}
```

### 3.3 更新引用

- [ ] 更新 `src/account/points_detector.py`
- [ ] 更新 `src/tasks/task_parser.py`
- [ ] 更新 `src/search/search_engine.py`
- [ ] 更新其他使用硬编码 URL 的文件

### 3.4 测试

- [ ] 确保所有现有测试通过
- [ ] 验证 URL 引用正确

***

## 四、验收标准

- [ ] 所有 URL 常量集中到 `src/constants/urls.py`
- [ ] 无硬编码 URL 残留
- [ ] 所有测试通过
- [ ] 无 mypy 类型错误

***

## 五、合并条件

- [ ] 所有测试通过
- [ ] Code Review 通过
- [ ] 无功能回归
