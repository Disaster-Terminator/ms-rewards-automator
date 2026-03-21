# API 端点验证报告

> 验证时间: 2026-02-26T00:22:43.422916

## 验证结果汇总

| API | 状态 | HTTP 状态码 | 耗时 | 备注 |
|-----|------|-------------|------|------|
| Dashboard API | ✅ success | 200 | 2406ms | - |
| App Dashboard | 🔒 unauthorized | 401 | 329ms | 需要认证或 cookies 无效 |
| Bing Suggestions | ✅ success | 200 | 890ms | - |
| Wikipedia Top Views | ✅ success | 200 | 19594ms | - |
| Reddit Popular | ❌ failed | 403 | 563ms | HTTP 403 |
| Google Trends | ✅ success | 400 | 1672ms | API 端点存在（需要有效参数） |
| Bing Quiz API | ✅ success | 200 | 453ms | - |
| Rewards Report Activity | ✅ success | 400 | 781ms | API 端点存在（需要有效参数） |

## 详细结果

### Dashboard API

- **URL**: `https://rewards.bing.com/api/getuserinfo?type=1`
- **描述**: 获取用户 Dashboard 数据（积分、任务等）
- **需要认证**: 是
- **状态**: success
- **HTTP 状态码**: 200
- **耗时**: 2406ms

**响应示例**:

```json
{
  "dashboard": {
    "userStatus": {
      "levelInfo": {
        "isNewLevelsFeatureAvailable": true,
        "lastMonthLevel": "newLevel1",
        "activeLevel": "newLevel3",
        "activeLevelName": "Gold Member",
        "progress": 1790,
        "progressMax": 750,
        "levels": [
          {
            "key": "newLevel1",
            "active": false,
            "name": "Member",
            "tasks": [
              {
                "text": "Earn at least 500 points each month to reach Silver Member (see https://aka.ms/3L)",
                "url": null
              }
            ],
            "privileges": [
              {
                "text": "5 points per Bing Search, up to 25 points per day",
                "url": "//www.bing.com/?FORM=MA1368"
              },
              {
                "text": "1 point per $1 spent in Microsoft Store, plus earn bonus points on select purchases",
                "url": "//www.microsoftstore.com"
              },
        
```

### App Dashboard

- **URL**: `https://prod.rewardsplatform.microsoft.com/dapi/me?channel=SAIOS&options=613`
- **描述**: 获取 App Dashboard 数据（签到、阅读赚等）
- **需要认证**: 是
- **状态**: unauthorized
- **HTTP 状态码**: 401
- **耗时**: 329ms

- **错误信息**: 需要认证或 cookies 无效

### Bing Suggestions

- **URL**: `https://api.bing.com/osjson.aspx?query=test`
- **描述**: 获取 Bing 搜索建议（无需认证）
- **需要认证**: 否
- **状态**: success
- **HTTP 状态码**: 200
- **耗时**: 890ms

**响应示例**:

```json
{
  "raw_response": "['test', ['testwise', 'test ipv6', 'testament', 'test internet speed', 'testosterone', 'test typing', 'testflight', 'test speed', 'testimony', 'testdisk', 'testwise/platform/code'], [], [], {'google:suggestrelevance': [1300, 1299, 1298, 1297, 1296, 1295, 1294, 1293, 1292, 1291, 1290]}]"
}
```

### Wikipedia Top Views

- **URL**: `https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/2026/02/01`
- **描述**: 获取 Wikipedia 热门文章（无需认证）
- **需要认证**: 否
- **状态**: success
- **HTTP 状态码**: 200
- **耗时**: 19594ms

**响应示例**:

```json
{
  "items": [
    {
      "project": "en.wikipedia",
      "access": "all-access",
      "year": "2026",
      "month": "02",
      "day": "01",
      "articles": [
        {
          "article": "Main_Page",
          "views": 7246434,
          "rank": 1
        },
        {
          "article": "Special:Search",
          "views": 907420,
          "rank": 2
        },
        {
          "article": "Carlos_Alcaraz",
          "views": 692939,
          "rank": 3
        },
        {
          "article": "Catherine_O'Hara",
          "views": 585973,
          "rank": 4
        },
        {
          "article": "Jeffrey_Epstein",
          "views": 570171,
          "rank": 5
        },
        {
          "article": "Royal_Rumble_(2026)",
          "views": 416429,
          "rank": 6
        },
        {
          "article": "Epstein_files",
          "views": 386025,
          "rank": 7
        },
        {
          "article": "Novak_Djokovic",
          "views": 342305,
      
```

### Reddit Popular

- **URL**: `https://www.reddit.com/r/popular.json?limit=10`
- **描述**: 获取 Reddit 热门帖子（无需认证）
- **需要认证**: 否
- **状态**: failed
- **HTTP 状态码**: 403
- **耗时**: 563ms

- **错误信息**: HTTP 403

### Google Trends

- **URL**: `https://trends.google.com/_/TrendsUi/data/batchexecute`
- **描述**: 获取 Google 热门趋势（复杂 API）
- **需要认证**: 否
- **状态**: success
- **HTTP 状态码**: 400
- **耗时**: 1672ms

- **错误信息**: API 端点存在（需要有效参数）

### Bing Quiz API

- **URL**: `https://www.bing.com/bingqa/ReportActivity?ajaxreq=1`
- **描述**: Bing Quiz 活动上报 API
- **需要认证**: 是
- **状态**: success
- **HTTP 状态码**: 200
- **耗时**: 453ms

**响应示例**:

```json
{
  "raw_response": ""
}
```

### Rewards Report Activity

- **URL**: `https://rewards.bing.com/api/reportactivity`
- **描述**: Rewards 活动上报 API
- **需要认证**: 是
- **状态**: success
- **HTTP 状态码**: 400
- **耗时**: 781ms

- **错误信息**: API 端点存在（需要有效参数）

## 结论

⚠️ **部分 API 可用**，建议：

- App Dashboard: 需要认证或 cookies 无效
- Reddit Popular: HTTP 403

建议保留 HTML 解析作为 fallback 方案。