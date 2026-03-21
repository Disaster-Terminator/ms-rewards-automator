# Microsoft Rewards API 完整文档

> 研究时间：2026-02-28
> 来源：microsoft-rewards-script (TypeScript 项目)

---

## 一、Dashboard API

### 1.1 获取用户数据

```http
GET https://rewards.bing.com/api/getuserinfo?type=1
```

**请求头**：
```http
Cookie: <cookies>
Referer: https://rewards.bing.com/
Origin: https://rewards.bing.com
<fingerprint-headers>
```

**响应数据结构**：
```typescript
interface DashboardData {
    userStatus: UserStatus
    userWarnings: unknown[]
    promotionalItem: PromotionalItem
    promotionalItems: PurplePromotionalItem[]
    dailySetPromotions: { [key: string]: PromotionalItem[] }
    streakPromotion: StreakPromotion
    streakBonusPromotions: StreakBonusPromotion[]
    punchCards: PunchCard[]
    morePromotions: MorePromotion[]
    // ... 其他字段
}
```

### 1.2 福利相关字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `monthlyLevelBonusProgress` | number | 月度等级奖励进度 |
| `monthlyLevelBonusMaximum` | number | 月度等级奖励最大值 |
| `monthlyLevelBonusState` | string | 月度等级奖励状态 |
| `bingStarMonthlyBonusProgress` | number | Bing Star 月度奖励进度 |
| `bingStarMonthlyBonusMaximum` | number | Bing Star 月度奖励最大值 |
| `bingStarBonusWeeklyProgress` | number | Bing Star 周度奖励进度 |
| `bingStarBonusWeeklyState` | string | Bing Star 周度奖励状态 |
| `defaultSearchEngineMonthlyBonusProgress` | number | 默认搜索引擎月度奖励进度 |
| `defaultSearchEngineMonthlyBonusMaximum` | number | 默认搜索引擎月度奖励最大值 |
| `defaultSearchEngineMonthlyBonusState` | string | 默认搜索引擎月度奖励状态 |

### 1.3 连胜相关字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `streakPromotion` | `StreakPromotion` | 连胜推广 |
| `streakBonusPromotions` | `StreakBonusPromotion[]` | 连胜奖励列表 |
| `streakProtectionPromo` | `StreakProtectionPromo` | 连胜保护机制 |

#### 连胜奖励数据结构

```typescript
interface StreakPromotionAttributes {
    hidden: GiveEligible
    type: string
    title: string
    image: string
    activity_progress: string
    last_updated: Date
    break_image: string
    lifetime_max: string
    bonus_points: string
    give_eligible: GiveEligible
    destination: string
}

type StreakPromotion = BasePromotion<StreakPromotionAttributes> & {
    lastUpdatedDate: Date
    breakImageUrl: string
    lifetimeMaxValue: number
    bonusPointsEarned: number
}
```

#### 连胜保护数据结构

```typescript
interface StreakProtectionPromo {
    type: string
    offerid: string
    isStreakProtectionOnEligible: GiveEligible
    streakProtectionStatus: GiveEligible
    remainingDays: string
    isFirstTime: GiveEligible
    streakCount: string
    isTodayStreakComplete: GiveEligible
    autoTurnOn: GiveEligible
    give_eligible: GiveEligible
    destination: string
}
```

---

## 二、App Dashboard API

### 2.1 获取 App Dashboard 数据

```http
GET https://prod.rewardsplatform.microsoft.com/dapi/me?channel=SAIOS&options=613
```

**请求头**：
```http
Authorization: Bearer ${accessToken}
User-Agent: Bing/32.5.431027001 (com.microsoft.bing; build:431027001; iOS 17.6.1) Alamofire/5.10.2
```

**响应数据结构**：
```typescript
interface AppDashboardData {
    response: {
        promotions: [{
            attributes: {
                offerid: string
                type: string
                complete: string
                pointmax: string
                pointprogress: string
            }
        }]
    }
}
```

---

## 三、Quiz API

### 3.1 提交 Quiz 答案

```http
POST https://www.bing.com/bingqa/ReportActivity?ajaxreq=1
```

**请求头**：
```http
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Cookie: <cookies>
<fingerprint-headers>
```

**请求体**：
```json
{
    UserId: null,
    TimeZoneOffset: -60,
    OfferId: <offerId>,
    ActivityCount: 1,
    QuestionIndex: '-1'
}
```

---

## 四、URL Reward API

### 4.1 提交 URL 奖励

```http
POST https://rewards.bing.com/api/reportactivity?X-Requested-With=XMLHttpRequest
```

**请求头**：
```http
Cookie: <cookies>
Referer: https://rewards.bing.com/
Origin: https://rewards.bing.com
<fingerprint-headers>
```

**请求体**：
```http
id: <offerId>
hash: <hash>
timeZone: '60'
activityAmount: '1'
dbs: '0'
form: ''
type: ''
__RequestVerificationToken: <token>
```

### 4.2 RequestVerificationToken 获取

**从 rewards home 页面提取**：
```javascript
const token = $(this.selectors.requestToken).attr('value') ??
             $(this.selectors.requestTokenMeta).attr('content') ??
             null

// 选择器
requestToken: 'input[name="__RequestVerificationToken"]'
requestTokenMeta: 'meta[name="__RequestVerificationToken"]'
```

---

## 五、App Activities API

### 5.1 提交活动

```http
POST https://prod.rewardsplatform.microsoft.com/dapi/me/activities
```

**请求头**：
```http
Authorization: Bearer ${accessToken}
User-Agent: Bing/32.5.431027001 (com.microsoft.bing; build:431027001; iOS 17.6.1) Alamofire/5.10.2
Content-Type: application/json
X-Rewards-Country: <geoLocale>
X-Rewards-Language: en
X-Rewards-ismobile: true
```

**请求体**：
```json
{
    id: <uuid>,
    amount: 1,
    type: 101 | 103,
    attributes: {
        offerid: 'Gamification_Sapphire_DailyCheckIn' | 'ENUS_readarticle3_30points'
    },
    country: <geoLocale>
}
```

**活动类型**：
| type | 说明 | offerid |
|------|------|--------|
| 101 | 每日签到 | Gamification_Sapphire_DailyCheckIn |
| 103 | 每日签到（美国区） | Gamification_Sapphire_DailyCheckIn |
| 101 | 阅读赚积分 | ENUS_readarticle3_30points |

---

## 六、App Access Token 获取

### 6.1 Mobile Access Login

```typescript
await new MobileAccessLogin(this.bot, page).get(email)
```

---

## 七、API 状态总结

| API | 状态 | 认证方式 | 说明 |
|-----|------|----------|------|
| Dashboard API | ✅ 可用 | Cookie | 获取用户数据、福利字段、连胜字段 |
| App Dashboard | ✅ 可用 | Bearer Token | 获取 App 推广数据 |
| Quiz API | ✅ 可用 | Cookie | 提交 Quiz 答案 |
| URL Reward API | ✅ 可用 | Cookie + CSRF Token | 提交 URL 奖励 |
| App Activities API | ✅ 可用 | Bearer Token | 提交签到、阅读赚积分 |

---

## 八、福利领取 API（重大发现）

### 8.1 核心发现

**福利领取可能使用与 URL Reward 相同的 API 端点！**

```http
POST https://rewards.bing.com/api/reportactivity?X-Requested-With=XMLHttpRequest
```

### 8.2 关键证据

`BasePromotion` 接口包含领取所需的所有字段：

```typescript
interface BasePromotion {
    offerId: string        // ✅ 领取所需
    hash: string           // ✅ 领取所需
    complete: boolean      // 状态标识
    pointProgressMax: number
    pointProgress: number
    promotionType: string
    // ... 其他字段
}
```

### 8.3 福利类型与字段

| 福利类型 | 进度字段 | 最大值字段 | 状态字段 |
|----------|----------|------------|----------|
| 月度等级奖励 | `monthlyLevelBonusProgress` | `monthlyLevelBonusMaximum` | `monthlyLevelBonusState` |
| Bing Star 月度 | `bingStarMonthlyBonusProgress` | `bingStarMonthlyBonusMaximum` | - |
| Bing Star 周度 | `bingStarBonusWeeklyProgress` | - | `bingStarBonusWeeklyState` |
| 默认搜索引擎 | `defaultSearchEngineMonthlyBonusProgress` | `defaultSearchEngineMonthlyBonusMaximum` | `defaultSearchEngineMonthlyBonusState` |

### 8.4 领取逻辑（推测）

```python
async def claim_monthly_bonus(self, promotion: BasePromotion):
    if promotion.monthlyLevelBonusState == 'Complete':
        return  # 已领取
    
    if promotion.monthlyLevelBonusProgress >= promotion.monthlyLevelBonusMaximum:
        # 使用 URL Reward API 领取
        await self.report_activity(
            offer_id=promotion.offerId,
            hash=promotion.hash,
            activity_type='monthlybonus'  # 待验证
        )
```

### 8.5 待验证事项

| 事项 | 验证方法 |
|------|----------|
| API 端点是否正确 | 浏览器抓包验证 |
| `activityType` 参数值 | 检查实际请求 |
| 福利对象位置 | Dashboard 响应中查找含 `offerId` 和 `hash` 的对象 |

---

## 九、连胜系统 API（重大发现）

### 9.1 数据结构

**`streakBonusPromotions` 继承自 `BasePromotion`**：

```typescript
interface StreakBonusPromotion extends BasePromotion<StreakBonusPromotionAttributes> {
    // 继承 offerId 和 hash 字段！
    attributes: {
        activity_max: string
        activity_progress: string
        bonus_earned?: string
        title: string
        type: string
        destination: string
        give_eligible: GiveEligible
    }
}
```

### 9.2 领取逻辑（推测）

```python
async def claim_streak_bonus(self, streak_bonus: StreakBonusPromotion):
    if streak_bonus.complete:
        return  # 已领取
    
    # 使用 URL Reward API 领取
    await self.report_activity(
        offer_id=streak_bonus.offerId,
        hash=streak_bonus.hash,
        activity_type=streak_bonus.attributes.type
    )
```

### 9.3 连胜保护

```typescript
interface StreakProtectionPromo {
    type: string
    offerid: string           // ✅ 有 offerid
    streakProtectionStatus: GiveEligible
    remainingDays: string
    streakCount: string
    isTodayStreakComplete: GiveEligible
    destination: string       // ✅ 可能有 API 端点
}
```

**注意**：`StreakProtectionPromo` 没有 `hash` 字段，可能需要不同的 API。

### 9.4 待验证事项

| 事项 | 验证方法 |
|------|----------|
| 连胜奖励领取 API | 抓包分析 `streakBonusPromotions` 领取请求 |
| 连胜保护激活 API | 抓包分析连胜保护开关请求 |
| `destination` 字段用途 | 检查是否包含 API 端点 |

---

## 十、API 状态总结（更新）

| API | 状态 | 认证方式 | 说明 |
|-----|------|----------|------|
| Dashboard API | ✅ 可用 | Cookie | 获取用户数据、福利字段、连胜字段 |
| App Dashboard | ✅ 可用 | Bearer Token | 获取 App 推广数据 |
| Quiz API | ✅ 可用 | Cookie | 提交 Quiz 答案 |
| URL Reward API | ✅ 可用 | Cookie + CSRF Token | **通用领取端点** |
| App Activities API | ✅ 可用 | Bearer Token | 提交签到、阅读赚积分 |
| 福利领取 API | 🔶 待验证 | Cookie + CSRF Token | **推测使用 URL Reward API** |
| 连胜奖励 API | 🔶 待验证 | Cookie + CSRF Token | **推测使用 URL Reward API** |
| 连胜保护 API | 🔶 待验证 | Cookie | **需独立研究** |

---

## 十一、下一步行动

### 优先级排序

| 优先级 | 任务 | 方法 |
|--------|------|------|
| 🔴 高 | 验证福利领取 API | 浏览器开发者工具抓包 |
| 🔴 高 | 验证连胜奖励 API | 浏览器开发者工具抓包 |
| 🟡 中 | 研究连胜保护 API | 检查 `destination` 字段 |

### 抓包验证步骤

1. 登录 Microsoft Rewards 网站
2. 打开开发者工具 → Network 标签
3. 过滤 `rewards.bing.com/api` 请求
4. 手动点击领取福利/连胜奖励
5. 分析请求参数和响应
