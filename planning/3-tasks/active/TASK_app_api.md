# TASK: App API 集成

> 分支: `feature/app-api`
> 并行组: 第一组
> 优先级: 🟢 中
> 预计时间: 5-8 天
> 依赖: 无

***

## 一、目标

实现 DailyCheckIn 和 ReadToEarn 功能，获取每日签到积分和阅读赚积分。

***

## 二、背景

### 2.1 API 验证结果

| API | 状态 | 备注 |
|-----|------|------|
| App Dashboard | ❌ 需要 OAuth | 需要 Bearer Token |
| App Activities | ❌ 需要 OAuth | 需要 Bearer Token |

### 2.2 认证流程

App API 需要完整的 OAuth 流程获取 Access Token：

1. 构造 OAuth 授权 URL
2. 浏览器导航到授权页面
3. 利用已有 Cookie 自动授权
4. 获取授权码 (code)
5. 用授权码换取 Access Token

### 2.3 OAuth 配置

```python
CLIENT_ID = '0000000040170455'
AUTH_URL = 'https://login.live.com/oauth20_authorize.srf'
REDIRECT_URL = 'https://login.live.com/oauth20_desktop.srf'
TOKEN_URL = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
SCOPE = 'service::prod.rewardsplatform.microsoft.com::MBI_SSL'
```

### 2.4 架构设计

```
src/
├── login/
│   ├── mobile_access_login.py    # OAuth 流程（独立于 handlers）
│   └── handlers/                  # 现有登录状态处理器（不修改）
├── app/                           # 新增目录
│   ├── __init__.py
│   ├── app_client.py              # App API 客户端
│   └── models.py                  # 数据模型
└── infrastructure/
    └── ms_rewards_app.py          # 集成 MobileAccessLogin
```

> **设计理由**：
>
> - `MobileAccessLogin` 不是 `StateHandler`，是 OAuth 流程执行器，职责不同
> - 项目无 `src/api/` 目录，App 功能独立，新建 `src/app/` 模块

***

## 三、任务清单

### 3.1 MobileAccessLogin 实现

- [x] 创建 `src/login/mobile_access_login.py`（独立于 handlers，因为不是 StateHandler）
  - [x] `get_access_token()` - 获取 Access Token
  - [x] `_build_auth_url()` - 构造授权 URL
  - [x] `_wait_for_code()` - 等待授权码
  - [x] `_exchange_token()` - 用授权码换 Token
  - [x] `_handle_passkey_prompt()` - 处理 Passkey 提示

### 3.2 AppClient 实现

- [x] 创建 `src/app/__init__.py`
- [x] 创建 `src/app/app_client.py`
- [x] 创建 `src/app/models.py`（数据模型）
  - [x] `get_app_dashboard()` - 获取 App Dashboard
  - [x] `do_daily_check_in()` - 每日签到
  - [x] `do_read_to_earn()` - 阅读赚积分

### 3.3 API 端点

```
GET  https://prod.rewardsplatform.microsoft.com/dapi/me?channel=SAIOS&options=613
POST https://prod.rewardsplatform.microsoft.com/dapi/me/activities
```

### 3.4 请求示例

**每日签到**:

```json
{
  "id": "{uuid}",
  "amount": 1,
  "type": 101,
  "attributes": { "offerid": "Gamification_Sapphire_DailyCheckIn" },
  "country": "{geo_locale}"
}
```

**阅读赚积分**:

```json
{
  "amount": 1,
  "id": "{random_hex}",
  "type": 101,
  "attributes": { "offerid": "ENUS_readarticle3_30points" },
  "country": "{geo_locale}"
}
```

### 3.5 测试

- [x] 创建 `tests/unit/test_app_client.py`（17 测试用例）
- [x] 创建 `tests/unit/test_mobile_access_login.py`（16 测试用例）
- [x] 单元测试覆盖率 > 80%（当前：86%）
- [ ] 集成测试（需要真实账户 + `login.auto_login.email` 配置）

***

## 四、参考资源

### 4.1 TS 项目参考

| 文件 | 路径 |
|------|------|
| OAuth 流程 | `Microsoft-Rewards-Script/src/browser/auth/methods/MobileAccessLogin.ts` |
| 每日签到 | `Microsoft-Rewards-Script/src/functions/activities/app/DailyCheckIn.ts` |
| 阅读赚积分 | `Microsoft-Rewards-Script/src/functions/activities/app/ReadToEarn.ts` |

> ⚠️ **重要说明**：TS 项目 README 明确声明 "V3.x does not support the new Bing Rewards interface"
>
> 福利领取和连胜系统在 TS 项目中只有数据结构定义，**没有实现代码**。
>
> App API 相关功能在 TS 项目中有实现，可以参考。

### 4.2 关键代码参考

```python
async def get_access_token(self, email: str) -> str:
    auth_url = self._build_auth_url(email)
    await self.page.goto(auth_url)
    
    code = await self._wait_for_code()
    if not code:
        raise AuthError("Failed to get OAuth code")
    
    token = await self._exchange_token(code)
    return token
```

***

## 五、预期收益

| 功能 | 积分 |
|------|------|
| 每日签到 | 3-30 分/天 |
| 阅读赚积分 | 最多 30 分/天 |

***

## 六、验收标准

### 6.1 单元测试验收（已完成）

- [x] OAuth 流程可成功获取 Access Token（Mock 测试通过）
- [x] 每日签到功能正常工作（Mock 测试通过）
- [x] 阅读赚积分功能正常工作（Mock 测试通过）
- [x] 单元测试覆盖率 > 80%（当前：86%）

### 6.2 集成测试验收（需要真实账户）

> **前置条件**：
>
> - 配置 `login.auto_login.email` 指向已保存会话的账户
> - 确保 `storage_state.json` 包含有效的登录状态

- [ ] OAuth 流程可成功获取真实 Access Token
- [ ] 每日签到功能在真实环境正常工作
- [ ] 阅读赚积分功能在真实环境正常工作

***

## 七、合并条件

- [x] 所有单元测试通过（33/33）
- [ ] Code Review 通过（需创建 PR）
- [ ] 集成测试通过（需要真实账户）
