"""
浏览器模拟器模块
创建和配置不同平台的浏览器实例，集成反检测机制
"""

import asyncio
import logging
import os
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright, Page
from browser.anti_focus_scripts import AntiFocusScripts
from browser.state_manager import BrowserStateManager

logger = logging.getLogger(__name__)


class BrowserSimulator:
    """浏览器模拟器类"""
    
    def __init__(self, config, anti_ban):
        """
        初始化浏览器模拟器
        
        Args:
            config: ConfigManager 实例
            anti_ban: AntiBanModule 实例
        """
        self.config = config
        self.anti_ban = anti_ban
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        
        # 初始化状态管理器
        self.state_manager = BrowserStateManager(config)
        
        logger.info("浏览器模拟器初始化完成")
    
    async def start_playwright(self):
        """启动 Playwright"""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            logger.info("Playwright 已启动")
    
    def _get_browser_args(self, device_type: str = "desktop", browser_type: str = "chromium") -> list[str]:
        """
        获取浏览器启动参数

        Args:
            device_type: 设备类型 ("desktop" 或 "mobile")
            browser_type: 浏览器类型 ("chromium", "edge", "chrome")

        Returns:
            启动参数列表
        """
        # 基础参数
        base_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--no-default-browser-check',
            '--disable-default-apps',
            '--no-first-run',
            '--disable-popup-blocking',
            '--disable-background-timer-throttling',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--disable-hang-monitor',
            '--disable-prompt-on-repost',
            '--disable-domain-reliability',
            '--disable-component-extensions-with-background-pages',
        ]

        # Edge 特定：禁用登录弹窗和同步提示（仅当 browser_type 为 edge 时）
        if browser_type == "edge":
            edge_specific_args = [
                '--disable-features=msEdgeEnableNurturingFramework',  # 禁用 Edge 培育框架（弹窗系统）
                '--disable-features=msEdgeSignInCtaOnNtp',  # 禁用新标签页登录提示
                '--disable-features=msEdgeSignInPromo',  # 禁用登录推广
                '--disable-features=msEdgeSyncPromo',  # 禁用同步推广
                '--disable-features=EdgeEnhanceSecurityMode',  # 禁用增强安全模式提示
                '--disable-features=EdgeShoppingAssistant',  # 禁用购物助手
                '--disable-features=EdgeCollectionsEnabled',  # 禁用集锦
                '--disable-features=msImplicitSignin',  # 禁用隐式登录
                '--disable-features=msSignInWithMicrosoft',  # 禁用 Microsoft 登录提示
            ]
            base_args.extend(edge_specific_args)

        # 通用禁用选项
        browser_args.extend([
            '--disable-sync',  # 完全禁用同步
            '--disable-features=IdentityManager',  # 禁用身份管理器
            '--disable-features=AutofillEnableAccountWalletStorage',  # 禁用账户钱包
            '--disable-features=msEdgeWalletIntegration',  # 禁用钱包集成
            # 禁用 Windows 凭据管理器集成（关键！）
            '--password-store=basic',  # 使用基本密码存储，不使用系统凭据管理器
            '--disable-features=PasswordImport',  # 禁用密码导入
            '--disable-features=PasswordManager',  # 禁用密码管理器
            '--disable-features=PasswordManagerOnboarding',  # 禁用密码管理器引导
            '--disable-features=PasswordSuggestions',  # 禁用密码建议
            '--disable-features=AutofillServerCommunication',  # 禁用自动填充服务器通信
        ])
            # WSL2 兼容参数（解决 sigtrap/page crash 问题）
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu-rasterization',
            '--use-gl=swiftshader',
            '--disable-features=Crashpad',  # 禁用崩溃报告（解决 sigtrap）
        
        # 防焦点参数（仅在非无头模式且启用防焦点时添加）
        headless = self.config.get("browser.headless", False)
        prevent_focus = self.config.get("browser.prevent_focus", "enhanced")
        
        if not headless and prevent_focus:
            focus_prevention_args = [
                '--disable-focus-on-load',               # 禁用加载时自动聚焦
                '--disable-raise-on-focus',              # 禁用聚焦时窗口置顶
                '--no-startup-window',                   # 不显示启动窗口
                '--disable-background-mode',             # 禁用后台模式
                '--disable-backgrounding-occluded-windows', # 禁用被遮挡窗口的后台处理
                '--disable-renderer-backgrounding',      # 禁用渲染器后台处理
                '--disable-features=FocusMode',          # 禁用焦点模式
                '--disable-features=TabHoverCards',      # 禁用标签页悬停卡片
                '--disable-features=TabGroups',          # 禁用标签页分组
                '--disable-features=DesktopPWAsTabStrip', # 禁用PWA标签条
                '--disable-features=WebAppManifestDisplayOverride', # 禁用Web应用显示覆盖
                '--disable-client-side-phishing-detection', # 禁用客户端钓鱼检测
                '--disable-sync',                        # 禁用同步
                '--disable-background-networking',       # 禁用后台网络
                '--disable-background-downloads',        # 禁用后台下载
                '--disable-component-update',            # 禁用组件更新
                '--disable-default-apps',                # 禁用默认应用
                '--disable-extensions',                  # 禁用扩展（可选）
                '--disable-plugins',                     # 禁用插件
                '--disable-print-preview',               # 禁用打印预览
                '--disable-speech-api',                  # 禁用语音API
                '--disable-file-system',                 # 禁用文件系统API
                '--disable-notifications',               # 禁用通知
                '--disable-permissions-api',             # 禁用权限API
                '--disable-presentation-api',            # 禁用演示API
                '--disable-remote-fonts',                # 禁用远程字体
                '--disable-shared-workers',              # 禁用共享Worker
                '--disable-speech-synthesis-api',        # 禁用语音合成API
                '--disable-web-security',                # 禁用Web安全（已包含但重要）
                '--allow-running-insecure-content',      # 允许不安全内容
                '--disable-features=VizDisplayCompositor', # 禁用显示合成器
                '--disable-features=AudioServiceOutOfProcess', # 禁用音频服务进程外
                '--disable-features=VizServiceDisplay',  # 禁用Viz服务显示
            ]
            base_args.extend(focus_prevention_args)
        
        # 主题相关参数
        if self.config.get("browser.force_dark_mode", True):
            theme_args = [
                '--force-dark-mode',
                '--enable-features=WebUIDarkMode',
                '--enable-features=WebContentsForceDark',
                '--force-color-profile=srgb',
            ]
            base_args.extend(theme_args)
        
        # 移动设备特定参数
        if device_type == "mobile":
            mobile_args = [
                '--disable-features=VizDisplayCompositor',
                '--disable-features=AudioServiceOutOfProcess',
                '--enable-features=UseSkiaRenderer',
                '--disable-gpu-sandbox',
            ]
            base_args.extend(mobile_args)
        
        # 性能优化参数
        performance_args = [
            '--max_old_space_size=4096',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-features=CalculateNativeWinOcclusion',
        ]
        base_args.extend(performance_args)
        
        return base_args
    
    async def create_desktop_browser(self, browser_type: str = "chromium") -> Browser:
        """
        创建桌面浏览器实例（Edge 或 Chrome）
        
        Args:
            browser_type: 浏览器类型 ("edge" 或 "chrome")
            
        Returns:
            Browser 实例
        """
        await self.start_playwright()
        
        # 获取浏览器配置
        headless = self.config.get("browser.headless", False)
        slow_mo = self.config.get("browser.slow_mo", 100)
        
        # 根据浏览器类型选择设备配置
        device_key = f"desktop_{browser_type}"
        device_config = self.anti_ban.get_device_config(device_key)
        
        logger.info(f"创建桌面浏览器: {browser_type}, headless={headless}")
        
        # 获取启动参数
        browser_args = self._get_browser_args("desktop", browser_type)
        
        # 根据浏览器类型设置 channel
        channel = None
        if browser_type == "edge":
            channel = "msedge"
        elif browser_type == "chrome":
            channel = "chrome"
        # chromium 不指定 channel，使用 Playwright 自带的
        
        # 启动 Chromium
        if channel:
            logger.info(f"使用浏览器通道: {channel}")
            self.browser = await self.playwright.chromium.launch(
                channel=channel,
                headless=headless,
                slow_mo=slow_mo,
                args=browser_args
            )
        else:
            logger.info("使用 Playwright 自带的 Chromium")
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                slow_mo=slow_mo,
                args=browser_args
            )
        
        logger.info(f"桌面浏览器创建成功: {browser_type}")
        return self.browser
    
    async def create_mobile_browser(self, device: str = "iPhone 12") -> Browser:
        """
        创建移动设备浏览器实例
        
        Args:
            device: 设备类型 ("iPhone 12" 或 "Android")
            
        Returns:
            Browser 实例
        """
        await self.start_playwright()
        
        # 获取浏览器配置
        headless = self.config.get("browser.headless", False)
        slow_mo = self.config.get("browser.slow_mo", 100)
        
        # 根据设备类型选择配置
        if "iphone" in device.lower():
            device_key = "mobile_iphone"
        else:
            device_key = "mobile_android"
        
        device_config = self.anti_ban.get_device_config(device_key)
        
        logger.info(f"创建移动浏览器: {device}, headless={headless}")
        
        # 获取启动参数
        browser_args = self._get_browser_args("mobile", device)
        
        # 启动 Chromium
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=browser_args
        )
        
        logger.info(f"移动浏览器创建成功: {device}")
        return self.browser
    
    async def create_context(
        self,
        browser: Browser,
        device_type: str = "desktop_chromium",
        storage_state: Optional[str] = None
    ) -> tuple[BrowserContext, Page]:
        """
        创建浏览器上下文，加载会话状态
        
        Args:
            browser: Browser 实例
            device_type: 设备类型
            storage_state: 会话状态文件路径
            
        Returns:
            (BrowserContext, Page) 元组 - 上下文和主页面
        """
        # 获取设备配置
        device_config = self.anti_ban.get_device_config(device_type)
        
        # 调整视口大小（避免太大）
        viewport = device_config["viewport"].copy()
        if not device_config.get("is_mobile", False):
            # 桌面端使用更合理的窗口大小
            viewport = {"width": 1280, "height": 720}
        
        # 准备上下文选项
        context_options = {
            "user_agent": device_config["user_agent"],
            "viewport": viewport,
            "device_scale_factor": 1.0,  # 固定为 1.0 避免缩放问题
            "is_mobile": device_config.get("is_mobile", False),
            "has_touch": device_config.get("has_touch", False),
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "color_scheme": "dark",  # 设置为黑夜模式
        }
        
        # 如果提供了 storage_state，加载它
        if storage_state and os.path.exists(storage_state):
            context_options["storage_state"] = storage_state
            logger.info(f"加载会话状态: {storage_state}")
        
        # 创建上下文
        context = await browser.new_context(**context_options)
        
        # 添加对话框处理器 - 自动接受所有对话框（包括 beforeunload）
        context.on("dialog", lambda dialog: asyncio.create_task(self._handle_dialog(dialog)))
        
        # 应用防置顶脚本（如果启用）
        prevent_focus = self.config.get("browser.prevent_focus", "enhanced")
        if prevent_focus:
            await self._apply_anti_focus_scripts(context)
        
        # 应用反检测脚本
        await self.apply_stealth(context)
        
        # 创建主页面
        main_page = await context.new_page()
        
        # 注册到状态管理器
        self.state_manager.register_browser(browser, context, main_page)
        
        # 集成主题持久化：在创建上下文后尝试恢复主题设置
        try:
            from ui.bing_theme_manager import BingThemeManager
            theme_manager = BingThemeManager(self.config)
            if theme_manager.persistence_enabled:
                logger.debug("尝试在新上下文中恢复主题设置...")
                # 导航到Bing首页以便应用主题
                await main_page.goto("https://www.bing.com", wait_until="domcontentloaded", timeout=10000)
                await asyncio.sleep(1)  # 等待页面稳定
                
                # 尝试恢复主题
                restore_success = await theme_manager.restore_theme_from_state(main_page)
                if restore_success:
                    logger.debug("✓ 在新上下文中成功恢复主题设置")
                else:
                    logger.debug("在新上下文中恢复主题设置失败，将使用默认设置")
        except Exception as e:
            logger.debug(f"上下文主题恢复过程中发生异常: {e}")
        
        logger.info(f"浏览器上下文创建成功: {device_type}, 视口: {viewport}")
        return context, main_page
    
    async def _handle_dialog(self, dialog) -> None:
        """
        处理浏览器对话框（alert, confirm, prompt, beforeunload）
        
        Args:
            dialog: Dialog 实例
        """
        try:
            dialog_type = dialog.type
            message = dialog.message
            logger.debug(f"检测到浏览器对话框: type={dialog_type}, message={message}")
            
            # 自动接受所有对话框
            # - alert: 点击"确定"
            # - confirm: 点击"确定"（返回 true）
            # - prompt: 点击"确定"并返回空字符串
            # - beforeunload: 点击"离开"（允许导航）
            await dialog.accept()
            logger.debug(f"已自动接受对话框: {dialog_type}")
            
        except Exception as e:
            logger.warning(f"处理对话框时出错: {e}")
            # 如果接受失败，尝试关闭
            try:
                await dialog.dismiss()
            except Exception:
                pass
    
    async def _apply_anti_focus_scripts(self, context: BrowserContext) -> None:
        """
        应用防置顶脚本到浏览器上下文
        
        Args:
            context: BrowserContext 实例
        """
        try:
            # 获取防焦点模式
            prevent_focus = self.config.get("browser.prevent_focus", "enhanced")
            
            if prevent_focus == False or prevent_focus == "false":
                logger.debug("防置顶功能已禁用")
                return
            
            # 根据模式选择脚本级别
            if prevent_focus == "enhanced":
                script_level = "enhanced"
            elif prevent_focus == "basic":
                script_level = "basic"
            else:
                # 默认使用增强模式
                script_level = "enhanced"
            
            anti_focus_script = AntiFocusScripts.get_script_by_level(script_level)
            
            # 注入防置顶脚本
            await context.add_init_script(anti_focus_script)
            
            logger.debug(f"防置顶脚本已注入 (模式: {prevent_focus})")
            
        except Exception as e:
            logger.warning(f"注入防置顶脚本失败: {e}")
            # 降级到基础脚本
            try:
                basic_script = AntiFocusScripts.get_basic_anti_focus_script()
                await context.add_init_script(basic_script)
                logger.debug("已降级到基础防置顶脚本")
            except Exception as e2:
                logger.error(f"基础防置顶脚本也失败: {e2}")
    
    async def apply_stealth(self, context: BrowserContext) -> None:
        """
        应用反检测脚本到浏览器上下文
        
        Args:
            context: BrowserContext 实例
        """
        use_stealth = self.config.get("anti_detection.use_stealth", True)
        
        if not use_stealth:
            logger.info("反检测功能已禁用")
            return
        
        logger.info("开始应用反检测脚本...")
        
        # 方法 1: 尝试使用 playwright-stealth（如果可用）
        try:
            from playwright_stealth import stealth_async
            
            # 为上下文中的所有新页面应用 stealth
            async def apply_stealth_to_page(page):
                try:
                    # 检查页面是否已关闭
                    if page.is_closed():
                        logger.debug("页面已关闭，跳过 stealth 应用")
                        return
                    
                    await stealth_async(page)
                    logger.debug("playwright-stealth 应用成功")
                except Exception as e:
                    # 忽略页面已关闭的错误
                    if "closed" in str(e).lower():
                        logger.debug(f"页面已关闭，跳过 stealth: {e}")
                    else:
                        logger.warning(f"应用 stealth 失败: {e}")
            
            # 监听新页面创建事件
            context.on("page", lambda page: apply_stealth_to_page(page))
            
            logger.info("使用 playwright-stealth 库")
            
        except ImportError:
            logger.warning("playwright-stealth 未安装，使用原生方法")
        
        # 方法 2: 使用原生 add_init_script 方法（备用或补充）
        scripts = self.anti_ban.get_stealth_scripts()
        
        for script in scripts:
            try:
                await context.add_init_script(script)
            except Exception as e:
                logger.warning(f"注入脚本失败: {e}")
        
        logger.info("反检测脚本应用完成")
    
    async def create_manual_login_context(
        self,
        device_type: str = "desktop_chromium",
        storage_state: Optional[str] = None
    ) -> tuple[Browser, BrowserContext, Page]:
        """
        创建用于手动登录的浏览器上下文
        这个方法会以有头模式启动浏览器，方便用户手动登录
        
        Args:
            device_type: 设备类型
            storage_state: 会话状态文件路径（用于保存登录状态）
            
        Returns:
            (Browser, BrowserContext, Page) 元组
        """
        logger.info("=== 手动登录模式 ===")
        logger.info("浏览器将以有头模式启动，请手动完成登录")
        
        # 强制使用有头模式
        original_headless = self.config.get("browser.headless")
        self.config.config["browser"]["headless"] = False
        
        # 创建浏览器
        if "mobile" in device_type:
            browser = await self.create_mobile_browser()
        else:
            browser_type = device_type.split("_")[1] if "_" in device_type else "chromium"
            browser = await self.create_desktop_browser(browser_type)
        
        # 创建上下文（传入 storage_state 以便保存登录状态）
        context, page = await self.create_context(browser, device_type, storage_state=storage_state)
        
        # 恢复原始配置
        self.config.config["browser"]["headless"] = original_headless
        
        logger.info("手动登录浏览器已启动")
        return browser, context, page
    
    async def close_browser(self):
        """只关闭浏览器，不停止 Playwright"""
        # 使用状态管理器清理资源
        await self.state_manager.cleanup_resources()
        
        if self.browser:
            self.browser = None
            logger.info("浏览器已关闭")
    
    async def close(self):
        """关闭浏览器和 Playwright"""
        await self.close_browser()
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            logger.info("Playwright 已停止")
    
    async def check_browser_health(self) -> bool:
        """检查浏览器健康状态"""
        return await self.state_manager.check_browser_health()
    
    async def recover_browser(self) -> bool:
        """从浏览器错误中恢复"""
        return await self.state_manager.recover_from_error()
    
    def get_browser_stats(self):
        """获取浏览器性能统计"""
        return self.state_manager.get_performance_stats()
