"""
URL 常量模块

集中管理 Microsoft Rewards 自动化项目中的所有 URL 常量。

提供以下 URL 常量组:
- REWARDS_URLS: Microsoft Rewards 页面 URL
- BING_URLS: Bing 搜索相关 URL
- LOGIN_URLS: Microsoft 登录 URL
- API_ENDPOINTS: Dashboard 和 App API 端点
- API_PARAMS: API 查询参数
- OAUTH_URLS: OAuth 认证 URL
- OAUTH_CONFIG: OAuth 配置值
- QUERY_SOURCE_URLS: 搜索查询来源 URL
- NOTIFICATION_URLS: 通知服务 URL
- HEALTH_CHECK_URLS: 健康检查测试 URL
- GITHUB_URLS: GitHub API URL
"""

REWARDS_URLS = {
    "dashboard": "https://rewards.bing.com/",
    "earn": "https://rewards.bing.com/earn",
    "dashboard_explicit": "https://rewards.bing.com/dashboard",
    "rewards_home": "https://rewards.microsoft.com/",
}

BING_URLS = {
    "home": "https://www.bing.com",
    "search": "https://www.bing.com/search",
    "origin": "https://www.bing.com",
}

LOGIN_URLS = {
    "microsoft_login": "https://login.live.com",
    "microsoft_online": "https://login.microsoftonline.com",
}

API_ENDPOINTS = {
    "dashboard": "https://rewards.bing.com/api/getuserinfo",
    "report_activity": "https://rewards.bing.com/api/reportactivity",
    "quiz": "https://www.bing.com/bingqa/ReportActivity",
    "app_dashboard": "https://prod.rewardsplatform.microsoft.com/dapi/me",
    "app_activities": "https://prod.rewardsplatform.microsoft.com/dapi/me/activities",
}

API_PARAMS = {
    "dashboard_type": "?type=1",
}

OAUTH_URLS = {
    "auth": "https://login.live.com/oauth20_authorize.srf",
    "redirect": "https://login.live.com/oauth20_desktop.srf",
    "token": "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
}

OAUTH_CONFIG = {
    "client_id": "0000000040170455",
    "scope": "service::prod.rewardsplatform.microsoft.com::MBI_SSL",
}

QUERY_SOURCE_URLS = {
    "bing_suggestions": "https://api.bing.com/osjson.aspx",
    "duckduckgo": "https://duckduckgo.com/ac/",
    "wikipedia_summary": "https://en.wikipedia.org/api/rest_v1/page/summary/",
    "wikipedia_random": "https://en.wikipedia.org/api/rest_v1/page/random/summary",
    "wikipedia_top_views": "https://wikimedia.org/api/rest_v1/metrics/pageviews/top",
}

NOTIFICATION_URLS = {
    "telegram_api": "https://api.telegram.org/bot{token}/sendMessage",
    "serverchan": "https://sctapi.ftqq.com/{key}.send",
    "callmebot_whatsapp": "https://api.callmebot.com/whatsapp.php",
}

HEALTH_CHECK_URLS = {
    "bing": "https://www.bing.com",
    "rewards": "https://rewards.microsoft.com",
    "google": "https://www.google.com",
}

GITHUB_URLS = {
    "graphql": "https://api.github.com/graphql",
    "rest": "https://api.github.com",
}
