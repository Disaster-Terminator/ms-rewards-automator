# Microsoft-Rewards-Script 项目全盘分析

## 项目概述

| 属性 | 值 |
|------|-----|
| 名称 | microsoft-rewards-script |
| 版本 | 3.1.2 |
| 语言 | TypeScript |
| 运行时 | Node.js >= 24.0.0 |
| 浏览器自动化 | Patchright (Playwright Fork) |
| 核心功能 | 自动化完成 Microsoft Rewards 任务获取积分 |

---

## 一、项目架构

### 1.1 目录结构

```
src/
├── index.ts                    # 主入口，Bot 类定义
├── browser/                    # 浏览器相关
│   ├── Browser.ts              # 浏览器创建与配置
│   ├── BrowserFunc.ts          # 浏览器功能函数（API调用）
│   ├── BrowserUtils.ts         # 浏览器工具函数
│   ├── UserAgent.ts            # UA 管理
│   └── auth/                   # 登录认证模块
│       ├── Login.ts            # 登录主控制器（状态机）
│       └── methods/            # 各种登录方式实现
├── functions/                  # 核心功能模块
│   ├── Workers.ts              # 任务调度器
│   ├── Activities.ts           # 活动执行器（门面模式）
│   ├── SearchManager.ts        # 搜索任务管理
│   ├── QueryEngine.ts          # 搜索词获取引擎
│   └── activities/             # 具体活动实现
│       ├── api/                # API 调用类活动
│       ├── app/                # App 类活动
│       └── browser/            # 浏览器类活动
├── interface/                  # TypeScript 接口定义
├── logging/                    # 日志系统
│   ├── Logger.ts               # 日志核心
│   ├── Discord.ts              # Discord Webhook
│   └── Ntfy.ts                 # Ntfy 推送
└── util/                       # 工具类
    ├── Axios.ts                # HTTP 客户端
    ├── Utils.ts                # 通用工具
    ├── Load.ts                 # 配置/会话加载
    └── Validator.ts            # 数据验证
```

### 1.2 核心依赖

| 依赖 | 用途 |
|------|------|
| `patchright` | Playwright 的反检测分支，用于浏览器自动化 |
| `fingerprint-generator` | 生成浏览器指纹 |
| `fingerprint-injector` | 注入指纹到浏览器 |
| `ghost-cursor-playwright-port` | 模拟人类鼠标移动轨迹 |
| `axios` + `axios-retry` | HTTP 请求与重试 |
| `cheerio` | HTML 解析（服务端 jQuery） |
| `otpauth` | TOTP 2FA 验证码生成 |
| `chalk` | 终端彩色输出 |
| `zod` | 数据验证 |
| `p-queue` | 并发控制 |

---

## 二、核心执行流程

### 2.1 主流程图

```
main()
  │
  ├── checkNodeVersion()              # 版本检查
  ├── new MicrosoftRewardsBot()       # 实例化
  ├── initialize()                    # 加载账户
  │
  └── run()                           # 启动运行
        │
        ├── [clusters > 1] ──────────┬── runMaster()     # 多进程主进程
        │                            └── runWorker()     # 多进程工作进程
        │
        └── [clusters == 1] ──────────→ runTasks()       # 单进程直接执行
                                            │
                                            └── Main()   # 单账户主流程
```

### 2.2 单账户主流程 (Main)

```typescript
async Main(account: Account): Promise<{ initialPoints, collectedPoints }> {
    // 1. 创建移动端浏览器会话
    mobileSession = await this.browserFactory.createBrowser(account)
    
    // 2. 登录
    await this.login.login(this.mainMobilePage, account)
    
    // 3. 获取 Access Token（用于 App API）
    this.accessToken = await this.login.getAppAccessToken(page, email)
    
    // 4. 获取 Dashboard 数据
    const data = await this.browser.func.getDashboardData()
    const appData = await this.browser.func.getAppDashboardData()
    
    // 5. 执行各种任务（Workers）
    await this.workers.doAppPromotions(appData)      // App 推广
    await this.workers.doDailySet(data, page)        // 每日任务集
    await this.workers.doSpecialPromotions(data)     // 特殊推广
    await this.workers.doMorePromotions(data, page)  // 更多推广
    await this.workers.doDailyCheckIn()              // 每日签到
    await this.workers.doReadToEarn()                // 阅读赚积分
    await this.workers.doPunchCards(data, page)      // 打卡任务
    
    // 6. 执行搜索任务
    await this.searchManager.doSearches(...)
    
    // 7. 返回积分统计
    return { initialPoints, collectedPoints }
}
```

---

## 三、核心模块详解

### 3.1 浏览器模块 (Browser.ts)

**功能**：创建反检测浏览器实例

**关键技术**：
- **Fingerprint 注入**：使用 `fingerprint-generator` 生成随机指纹，`fingerprint-injector` 注入
- **WebAuthn 禁用**：通过 `addInitScript` 禁用 Passkey/FIDO2
- **Session 持久化**：保存 Cookies 和 Fingerprint 到本地

```typescript
// 核心代码片段
async createBrowser(account: Account): Promise<BrowserCreationResult> {
    // 1. 启动 Chromium
    browser = await rebrowser.chromium.launch({
        headless: this.bot.config.headless,
        proxy: proxyConfig,
        args: [...Browser.BROWSER_ARGS]  // 反检测参数
    })
    
    // 2. 注入指纹
    const context = await newInjectedContext(browser, {
        fingerprint,
        newContextOptions: { permissions: [], ignoreHTTPSErrors: true }
    })
    
    // 3. 禁用 WebAuthn
    await context.addInitScript(() => {
        Object.defineProperty(navigator, 'credentials', {
            value: {
                create: () => Promise.reject(new Error('WebAuthn disabled')),
                get: () => Promise.reject(new Error('WebAuthn disabled'))
            }
        })
    })
    
    // 4. 加载已有 Cookies
    await context.addCookies(sessionData.cookies)
    
    return { context, fingerprint }
}
```

### 3.2 登录模块 (Login.ts)

**设计模式**：状态机模式

**状态定义**：
```typescript
type LoginState =
    | 'EMAIL_INPUT'           // 邮箱输入页
    | 'PASSWORD_INPUT'        // 密码输入页
    | 'SIGN_IN_ANOTHER_WAY'   // 选择其他登录方式
    | 'KMSI_PROMPT'           // "保持登录" 提示
    | 'LOGGED_IN'             // 已登录
    | 'RECOVERY_EMAIL_INPUT'  // 恢复邮箱验证
    | 'ACCOUNT_LOCKED'        // 账户锁定
    | '2FA_TOTP'              // TOTP 双因素认证
    | 'LOGIN_PASSWORDLESS'    // 无密码登录
    | 'GET_A_CODE'            // 获取验证码
    | 'PASSKEY_ERROR'         // Passkey 错误
    | ...
```

**核心流程**：
```typescript
async login(page: Page, account: Account) {
    await page.goto('https://www.bing.com/rewards/dashboard')
    
    while (iteration < maxIterations) {
        // 1. 检测当前状态
        const state = await this.detectCurrentState(page, account)
        
        // 2. 处理状态
        const shouldContinue = await this.handleState(state, page, account)
        
        // 3. 状态转换直到登录成功
        if (state === 'LOGGED_IN') break
    }
    
    // 4. 最终化登录（保存 Session）
    await this.finalizeLogin(page, account.email)
}
```

**支持的登录方式**：
- 邮箱+密码登录
- TOTP 2FA 自动输入
- 无密码登录（手机验证码）
- 恢复邮箱验证
- Passkey 跳过

### 3.3 任务调度器 (Workers.ts)

**功能**：根据配置调度执行各类任务

**任务类型**：
| Worker | 功能 | 数据来源 |
|--------|------|----------|
| `doDailySet` | 每日任务集 | `dailySetPromotions[日期]` |
| `doMorePromotions` | 更多推广任务 | `morePromotions` |
| `doSpecialPromotions` | 特殊推广 | `promotionalItems` |
| `doPunchCards` | 打卡任务 | `punchCards` |
| `doAppPromotions` | App 推广 | App Dashboard API |

**任务分发逻辑**：
```typescript
private async solveActivities(activities: BasePromotion[], page: Page) {
    for (const activity of activities) {
        const type = activity.promotionType?.toLowerCase()
        
        switch (type) {
            case 'quiz':
                await this.bot.activities.doQuiz(activity)
                break
            case 'urlreward':
                if (name.includes('exploreonbing')) {
                    await this.bot.activities.doSearchOnBing(activity, page)
                } else {
                    await this.bot.activities.doUrlReward(activity)
                }
                break
            case 'findclippy':
                await this.bot.activities.doFindClippy(activity)
                break
        }
        
        await this.bot.utils.wait(randomDelay(5000, 15000))
    }
}
```

### 3.4 搜索管理器 (SearchManager.ts)

**功能**：管理桌面端和移动端搜索任务

**搜索模式**：
- **并行模式** (`parallelSearching: true`)：同时创建两个浏览器会话
- **顺序模式**：先完成移动端，再完成桌面端

**搜索流程**：
```typescript
async doSearch(data, page, isMobile): Promise<number> {
    // 1. 获取缺失积分
    const missingPoints = this.bot.browser.func.missingSearchPoints(counters, isMobile)
    
    // 2. 获取搜索词
    const queries = await queryCore.queryManager({
        shuffle: true,
        related: true,
        langCode,
        geoLocale
    })
    
    // 3. 执行搜索循环
    for (const query of queries) {
        await this.bingSearch(page, query, isMobile)
        
        // 检测积分变化
        const newCounters = await this.bot.browser.func.getSearchPoints()
        const gained = missingPoints - newMissingPoints
        
        // 积分为0时停止
        if (newMissingPoints === 0) break
        
        // 连续无积分时重新生成搜索词
        if (stagnantLoop > maxStagnant) {
            queries = await regenerateQueries()
        }
    }
}
```

### 3.5 查询引擎 (QueryEngine.ts)

**功能**：从多个来源获取搜索词

**数据源**：
| 来源 | API | 说明 |
|------|-----|------|
| Google Trends | `trends.google.com/batchexecute` | 热门趋势 |
| Wikipedia | `wikimedia.org/api/rest_v1/metrics/pageviews/top` | 热门文章 |
| Reddit | `reddit.com/r/popular.json` | 热门帖子 |
| Local | `search-queries.json` | 本地词库 |
| Bing Suggestions | `bingapis.com/api/v7/suggestions` | 搜索建议 |
| Bing Related | `api.bing.com/osjson.aspx` | 相关搜索 |

**查询聚类**：
```typescript
async buildRelatedClusters(baseTopics: string[], langCode: string) {
    for (const topic of baseTopics.slice(0, 50)) {
        const suggestions = await this.getBingSuggestions(topic, langCode)
        const relatedTerms = await this.getBingRelatedTerms(topic)
        
        // 聚类：[主题, 建议1-6, 相关词1-3]
        clusters.push([topic, ...suggestions.slice(0, 6), ...relatedTerms.slice(0, 3)])
    }
    return clusters
}
```

---

## 四、活动类型实现

### 4.1 API 类活动

#### Quiz.ts - 问答任务
```typescript
async doQuiz(promotion: BasePromotion) {
    // 通过 API 直接提交答案
    for (let i = 0; i < maxAttempts; i++) {
        const request = {
            url: 'https://www.bing.com/bingqa/ReportActivity?ajaxreq=1',
            method: 'POST',
            data: JSON.stringify({
                UserId: null,
                TimeZoneOffset: -60,
                OfferId: offerId,
                ActivityCount: 1,
                QuestionIndex: '-1'  // 自动答题
            })
        }
        
        const response = await this.bot.axios.request(request)
        const newBalance = await this.bot.browser.func.getCurrentPoints()
        
        if (gainedPoints <= 0) break
    }
}
```

#### UrlReward.ts - URL 奖励
```typescript
async doUrlReward(promotion: BasePromotion) {
    const formData = new URLSearchParams({
        id: offerId,
        hash: promotion.hash,
        timeZone: '60',
        activityAmount: '1',
        __RequestVerificationToken: this.bot.requestToken
    })
    
    await this.bot.axios.request({
        url: 'https://rewards.bing.com/api/reportactivity',
        method: 'POST',
        data: formData
    })
}
```

### 4.2 App 类活动

#### DailyCheckIn.ts - 每日签到
```typescript
async doDailyCheckIn() {
    const jsonData = {
        id: randomUUID(),
        amount: 1,
        type: 101,  // 或 103（美国区）
        attributes: { offerid: 'Gamification_Sapphire_DailyCheckIn' },
        country: this.bot.userData.geoLocale
    }
    
    await this.bot.axios.request({
        url: 'https://prod.rewardsplatform.microsoft.com/dapi/me/activities',
        method: 'POST',
        headers: {
            Authorization: `Bearer ${this.bot.accessToken}`,
            'User-Agent': 'Bing/32.5.431027001 (com.microsoft.bing; ...)',
            'X-Rewards-Country': geoLocale,
            'X-Rewards-ismobile': 'true'
        },
        data: JSON.stringify(jsonData)
    })
}
```

#### ReadToEarn.ts - 阅读赚积分
```typescript
async doReadToEarn() {
    for (let i = 0; i < 10; i++) {
        const jsonData = {
            amount: 1,
            id: randomBytes(64).toString('hex'),
            type: 101,
            attributes: { offerid: 'ENUS_readarticle3_30points' },
            country: geoLocale
        }
        
        // 提交阅读记录
        const response = await this.bot.axios.request(...)
        
        if (gainedPoints <= 0) break
        
        await this.bot.utils.wait(randomDelay(delayMin, delayMax))
    }
}
```

### 4.3 浏览器类活动

#### Search.ts - Bing 搜索
```typescript
private async bingSearch(page: Page, query: string, isMobile: boolean) {
    // 1. 定位搜索框
    const searchBox = page.locator('#sb_form_q')
    
    // 2. 清空并输入
    await searchBox.click({ clickCount: 3 })
    await searchBox.fill('')
    await page.keyboard.type(query, { delay: 50 })
    await page.keyboard.press('Enter')
    
    // 3. 可选：随机滚动
    if (scrollRandomResults) {
        await this.randomScroll(page, isMobile)
    }
    
    // 4. 可选：随机点击结果
    if (clickRandomResults) {
        await this.clickRandomLink(page, isMobile)
    }
    
    // 5. 等待积分更新
    await this.bot.utils.wait(randomDelay(searchDelay.min, searchDelay.max))
    
    return await this.bot.browser.func.getSearchPoints()
}
```

---

## 五、数据接口

### 5.1 Dashboard API

**获取用户 Dashboard 数据**：
```typescript
async getDashboardData(): Promise<DashboardData> {
    const request = {
        url: 'https://rewards.bing.com/api/getuserinfo?type=1',
        method: 'GET',
        headers: {
            Cookie: this.buildCookieHeader(cookies, ['bing.com', 'live.com', 'microsoftonline.com'])
        }
    }
    return response.data.dashboard
}
```

**Dashboard 数据结构**：
```typescript
interface DashboardData {
    userStatus: {
        availablePoints: number      // 当前积分
        lifetimePoints: number       // 累计积分
        counters: {
            pcSearch: [{ pointProgress, pointProgressMax }]      // 桌面搜索
            mobileSearch: [{ pointProgress, pointProgressMax }]  // 移动搜索
        }
    }
    dailySetPromotions: { [date: string]: PromotionalItem[] }  // 每日任务
    morePromotions: MorePromotion[]                            // 更多推广
    punchCards: PunchCard[]                                    // 打卡任务
    promotionalItems: PurplePromotionalItem[]                  // 特殊推广
    userProfile: { attributes: { country } }                   // 用户信息
}
```

### 5.2 App API

**获取 App Access Token**：
```typescript
async getAppAccessToken(page: Page, email: string) {
    // 通过 MobileAccessLogin 获取
    // 用于调用 prod.rewardsplatform.microsoft.com API
}
```

**App Dashboard 数据**：
```typescript
interface AppDashboardData {
    response: {
        promotions: [{
            attributes: {
                offerid: string
                type: string      // 'sapphire', 'msnreadearn', 'checkin'
                complete: string
                pointmax: string
                pointprogress: string
            }
        }]
    }
}
```

---

## 六、反检测技术

### 6.1 浏览器指纹

```typescript
// 生成指纹
const fingerprint = new FingerprintGenerator().getFingerprint({
    devices: isMobile ? ['mobile'] : ['desktop'],
    operatingSystems: isMobile ? ['android', 'ios'] : ['windows', 'linux'],
    browsers: [{ name: 'edge' }]
})

// 注入指纹
await newInjectedContext(browser, { fingerprint })
```

### 6.2 鼠标轨迹模拟

```typescript
// 使用 ghost-cursor 模拟人类鼠标移动
import { createCursor } from 'ghost-cursor-playwright-port'

async ghostClick(page: Page, selector: string): Promise<boolean> {
    const cursor = createCursor(page)
    await cursor.click(selector)  // 自动生成贝塞尔曲线轨迹
    return true
}
```

### 6.3 浏览器启动参数

```typescript
private static readonly BROWSER_ARGS = [
    '--no-sandbox',
    '--mute-audio',
    '--disable-setuid-sandbox',
    '--ignore-certificate-errors',
    '--disable-blink-features=Attestation',
    '--disable-features=WebAuthentication,PasswordManager,...',
    '--disable-save-password-bubble'
]
```

### 6.4 WebAuthn 禁用

```typescript
await context.addInitScript(() => {
    Object.defineProperty(navigator, 'credentials', {
        value: {
            create: () => Promise.reject(new Error('WebAuthn disabled')),
            get: () => Promise.reject(new Error('WebAuthn disabled'))
        }
    })
})
```

---

## 七、多进程架构

### 7.1 Cluster 模式

```typescript
// 主进程
private async runMaster(runStartTime: number) {
    const accountChunks = this.utils.chunkArray(this.accounts, this.config.clusters)
    
    for (const chunk of accountChunks) {
        const worker = cluster.fork()
        worker.send({ chunk, runStartTime })
        
        worker.on('message', (msg) => {
            if (msg.__ipcLog) {
                // 处理日志消息
                sendDiscord(webhook.discord.url, msg.__ipcLog.content, msg.__ipcLog.level)
            }
            if (msg.__stats) {
                // 收集统计数据
                allAccountStats.push(...msg.__stats)
            }
        })
    }
}

// 工作进程
private runWorker(runStartTime: number) {
    process.on('message', async ({ chunk }) => {
        const stats = await this.runTasks(chunk, runStartTime)
        process.send({ __stats: stats })
        process.exit(0)
    })
}
```

### 7.2 AsyncLocalStorage 上下文传递

```typescript
interface ExecutionContext {
    isMobile: boolean
    account: Account
}

const executionContext = new AsyncLocalStorage<ExecutionContext>()

// 使用
await executionContext.run({ isMobile: true, account }, async () => {
    // 在此作用域内，getCurrentContext() 可获取上下文
    const { isMobile } = getCurrentContext()
})
```

---

## 八、配置系统

### 8.1 配置结构

```typescript
interface Config {
    baseURL: string
    sessionPath: string
    headless: boolean
    clusters: number
    errorDiagnostics: boolean
    workers: ConfigWorkers
    searchSettings: ConfigSearchSettings
    debugLogs: boolean
    proxy: ConfigProxy
    webhook: ConfigWebhook
}
```

### 8.2 账户结构

```typescript
interface Account {
    email: string
    password: string
    totpSecret?: string           // TOTP 密钥
    recoveryEmail: string         // 恢复邮箱
    geoLocale: 'auto' | string    // 地区
    langCode: 'en' | string       // 语言
    proxy: AccountProxy           // 代理配置
    saveFingerprint: {            // 指纹保存
        mobile: boolean
        desktop: boolean
    }
}
```

---

## 九、日志系统

### 9.1 日志级别

```typescript
type LogLevel = 'info' | 'warn' | 'error' | 'debug'

// 使用
this.bot.logger.info(isMobile, 'TITLE', 'message', 'green')
this.bot.logger.error(isMobile, 'TITLE', new Error('error'))
this.bot.logger.debug(isMobile, 'TITLE', 'debug message')
```

### 9.2 日志过滤

```typescript
interface LogFilter {
    enabled: boolean
    mode: 'whitelist' | 'blacklist'
    levels?: Array<'debug' | 'info' | 'warn' | 'error'>
    keywords?: string[]
    regexPatterns?: string[]
}
```

### 9.3 Webhook 推送

- **Discord**：通过 Webhook URL 发送
- **Ntfy**：通过 Ntfy 服务推送通知

---

## 十、关键实现要点

### 10.1 积分追踪

```typescript
// 实时追踪积分变化
const initialPoints = data.userStatus.availablePoints
this.bot.userData.currentPoints = initialPoints

// 每次活动后更新
const newBalance = await this.bot.browser.func.getCurrentPoints()
const gainedPoints = newBalance - oldBalance
this.bot.userData.gainedPoints += gainedPoints
this.bot.userData.currentPoints = newBalance
```

### 10.2 搜索词去重与聚类

```typescript
private normalizeAndDedupe(queries: string[]): string[] {
    const seen = new Set<string>()
    return queries.filter(q => {
        const norm = q.trim().replace(/\s+/g, ' ').toLowerCase()
        if (seen.has(norm)) return false
        seen.add(norm)
        return true
    })
}
```

### 10.3 错误处理与重试

```typescript
// Axios 自动重试
axiosRetry(this.instance, {
    retries: 5,
    retryDelay: axiosRetry.exponentialDelay,
    shouldResetTimeout: true,
    retryCondition: error => {
        if (axiosRetry.isNetworkError(error)) return true
        const status = error.response?.status
        return status === 429 || (status >= 500 && status <= 599)
    }
})
```

### 10.4 Session 持久化

```typescript
// 保存
await saveSessionData(sessionPath, cookies, email, isMobile)
await saveFingerprintData(sessionPath, email, isMobile, fingerprint)

// 加载
const { cookies, fingerprint } = await loadSessionData(sessionPath, email, saveFingerprint, isMobile)
```

---

## 十一、与 Python 项目对比建议

### 11.1 架构参考

| TypeScript 实现 | Python 对应 |
|----------------|-------------|
| `MicrosoftRewardsBot` 类 | 主 Bot 类 |
| `Workers.ts` | 任务调度器 |
| `Activities.ts` | 活动执行器（门面模式） |
| `Login.ts` 状态机 | 登录状态处理 |
| `QueryEngine.ts` | 搜索词获取 |
| `AsyncLocalStorage` | `contextvars.ContextVar` |

### 11.2 关键技术迁移

| 技术 | TypeScript | Python |
|------|------------|--------|
| 浏览器自动化 | Patchright/Playwright | Playwright-Python / Selenium |
| 指纹注入 | fingerprint-injector | 需自行实现或使用 undetected-chromedriver |
| 鼠标模拟 | ghost-cursor | 需自行实现贝塞尔曲线 |
| HTTP 客户端 | axios + axios-retry | httpx + tenacity |
| HTML 解析 | cheerio | BeautifulSoup4 / lxml |
| TOTP | otpauth | pyotp |
| 配置验证 | zod | pydantic |
| 多进程 | cluster | multiprocessing |
| 异步上下文 | AsyncLocalStorage | contextvars |

### 11.3 API 端点汇总

```
# Dashboard
GET  https://rewards.bing.com/api/getuserinfo?type=1

# 活动上报
POST https://rewards.bing.com/api/reportactivity

# Quiz
POST https://www.bing.com/bingqa/ReportActivity?ajaxreq=1

# App API
GET  https://prod.rewardsplatform.microsoft.com/dapi/me?channel=SAIOS&options=613
POST https://prod.rewardsplatform.microsoft.com/dapi/me/activities

# 搜索词
POST https://trends.google.com/_/TrendsUi/data/batchexecute
GET  https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{lang}.wikipedia/all-access/{yyyy}/{mm}/{dd}
GET  https://www.reddit.com/r/popular.json?limit=50
GET  https://www.bingapis.com/api/v7/suggestions?q={query}&appid=...
GET  https://api.bing.com/osjson.aspx?query={query}
```

---

## 十二、注意事项

1. **V3.x 不支持新版 Bing Rewards 界面**：项目 README 明确警告
2. **Session 持久化**：删除 sessions 文件夹可解决大部分登录问题
3. **代理配置**：支持 HTTP/HTTPS/SOCKS4/SOCKS5
4. **地区适配**：geoLocale 影响可用任务和 API 响应
5. **速率限制**：搜索间隔、活动间隔需合理配置避免封号
