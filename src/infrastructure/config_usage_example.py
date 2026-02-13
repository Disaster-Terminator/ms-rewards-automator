"""
配置使用示例

展示类型化配置的使用方式。

旧式调用:
    config.get("browser.headless")
    config.get("search.desktop_count")
    config.get("login.auto_login.enabled")

新式调用:
    config.app.browser.headless
    config.app.search.desktop_count
    config.app.login.auto_login.enabled
"""

# ============================================================
# 1. 基本访问示例
# ============================================================

# 旧式 (字典访问)
headless = config.get("browser.headless", False)
desktop_count = config.get("search.desktop_count", 30)

# 新式 (属性访问)
headless = config.app.browser.headless
desktop_count = config.app.search.desktop_count


# ============================================================
# 2. 嵌套配置访问
# ============================================================

# 旧式
auto_login_enabled = config.get("login.auto_login.enabled", False)
email = config.get("login.auto_login.email", "")

# 新式
auto_login_enabled = config.app.login.auto_login.enabled
email = config.app.login.auto_login.email


# ============================================================
# 3. 配置修改示例
# ============================================================

# 旧式 (修改字典)
config.config["browser"]["headless"] = True
config.config["search"]["wait_interval"]["min"] = 2

# 新式 (修改属性)
config.app.browser.headless = True
config.app.search.wait_interval_min = 2


# ============================================================
# 4. 完整示例：命令行参数应用
# ============================================================

def apply_cli_args(config, args):
    """应用命令行参数到配置"""

    # 旧式
    if args.headless:
        config.config["browser"]["headless"] = True

    if args.mode == "fast":
        config.config["search"]["wait_interval"]["min"] = 2
        config.config["search"]["wait_interval"]["max"] = 5
        config.config["browser"]["slow_mo"] = 50
    elif args.mode == "slow":
        config.config["search"]["wait_interval"]["min"] = 15
        config.config["search"]["wait_interval"]["max"] = 30
        config.config["browser"]["slow_mo"] = 200

    # 新式
    if args.headless:
        config.app.browser.headless = True

    if args.mode == "fast":
        config.app.search.wait_interval_min = 2
        config.app.search.wait_interval_max = 5
        config.app.browser.slow_mo = 50
    elif args.mode == "slow":
        config.app.search.wait_interval_min = 15
        config.app.search.wait_interval_max = 30
        config.app.browser.slow_mo = 200


# ============================================================
# 5. 组件初始化示例
# ============================================================

def create_browser_config(config):
    """创建浏览器配置"""

    # 旧式
    browser_config = {
        "headless": config.get("browser.headless", False),
        "slow_mo": config.get("browser.slow_mo", 100),
        "timeout": config.get("browser.timeout", 30000),
    }

    # 新式
    browser_config = {
        "headless": config.app.browser.headless,
        "slow_mo": config.app.browser.slow_mo,
        "timeout": config.app.browser.timeout,
    }

    return browser_config


# ============================================================
# 6. 类型安全优势
# ============================================================

"""
新式配置的优势:

1. IDE 自动补全
   - 输入 config.app. 即可看到所有可用配置项
   - 输入 config.app.browser. 即可看到浏览器相关配置

2. 类型检查
   - config.app.browser.headless 返回 bool 类型
   - config.app.search.desktop_count 返回 int 类型
   - 编辑器会在编译时提示类型错误

3. 文档提示
   - 每个配置类都有详细的属性说明
   - 鼠标悬停即可查看配置项的用途和默认值

4. 重构友好
   - 重命名配置项时，IDE 会提示所有引用位置
   - 找不到的配置项会在编译时报错
"""

# ============================================================
# 7. AppConfig 模型定义（供快速参考）
# ============================================================

"""
@dataclass
class AppConfig:
    search: SearchConfig
    browser: BrowserConfig
    account: AccountConfig
    login: LoginConfig
    query_engine: QueryEngineConfig
    task_system: TaskSystemConfig
    bing_theme: BingThemeConfig
    monitoring: MonitoringWithHealth
    notification: NotificationConfig
    scheduler: SchedulerConfig
    error_handling: ErrorHandlingConfig
    logging: LoggingConfig

@dataclass
class SearchConfig:
    desktop_count: int = 30
    mobile_count: int = 20
    wait_interval: int = 5
    wait_interval_min: int = 2
    wait_interval_max: int = 8
    search_terms_file: str = "tools/search_terms.txt"

@dataclass
class BrowserConfig:
    headless: bool = False
    prevent_focus: str = "basic"
    slow_mo: int = 100
    timeout: int = 30000
    type: str = "chromium"  # chromium(Playwright内置,推荐), chrome, edge

@dataclass
class AutoLoginConfig:
    enabled: bool = False
    email: str = ""
    password: str = ""
    totp_secret: str = ""
"""
