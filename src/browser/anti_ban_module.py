"""
反封禁模块
实现多层反检测策略，隐藏自动化特征
"""

import random
import asyncio
import logging
from typing import List, Dict, Any
from playwright.async_api import Page, BrowserContext

logger = logging.getLogger(__name__)


# 设备配置常量
DEVICE_CONFIGS = {
    "desktop_edge": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "viewport": {"width": 1920, "height": 1080},
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
    },
    "desktop_chrome": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
    },
    "desktop_chromium": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
    },
    "mobile_iphone": {
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 390, "height": 844},
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "mobile_android": {
        "user_agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "viewport": {"width": 412, "height": 915},
        "device_scale_factor": 2.625,
        "is_mobile": True,
        "has_touch": True,
    }
}


class AntiBanModule:
    """反封禁模块类"""
    
    def __init__(self, config):
        """
        初始化反封禁模块
        
        Args:
            config: ConfigManager 实例
        """
        self.config = config
        self.wait_min = config.get("search.wait_interval.min", 5)
        self.wait_max = config.get("search.wait_interval.max", 15)
        
        # 滚动配置
        self.scroll_enabled = config.get("anti_detection.scroll_behavior.enabled", True)
        self.min_scrolls = config.get("anti_detection.scroll_behavior.min_scrolls", 2)
        self.max_scrolls = config.get("anti_detection.scroll_behavior.max_scrolls", 5)
        self.scroll_delay_min = config.get("anti_detection.scroll_behavior.scroll_delay_min", 500)
        self.scroll_delay_max = config.get("anti_detection.scroll_behavior.scroll_delay_max", 2000)
        
        logger.info("反封禁模块初始化完成")
    
    def get_random_wait_time(self) -> float:
        """
        获取随机等待时间
        
        Returns:
            随机等待时间（秒）
        """
        wait_time = random.uniform(self.wait_min, self.wait_max)
        logger.debug(f"生成随机等待时间: {wait_time:.2f} 秒")
        return wait_time
    
    def get_random_viewport(self, base_width: int = 1920, base_height: int = 1080) -> Dict[str, int]:
        """
        生成随机视口大小（在合理范围内）
        
        Args:
            base_width: 基础宽度
            base_height: 基础高度
            
        Returns:
            视口配置字典
        """
        # 在基础尺寸的 ±10% 范围内随机
        width_variance = int(base_width * 0.1)
        height_variance = int(base_height * 0.1)
        
        width = random.randint(base_width - width_variance, base_width + width_variance)
        height = random.randint(base_height - height_variance, base_height + height_variance)
        
        viewport = {"width": width, "height": height}
        logger.debug(f"生成随机视口: {viewport}")
        return viewport
    
    async def simulate_human_scroll(self, page: Page) -> None:
        """
        模拟人类滚动行为
        
        Args:
            page: Playwright Page 对象
        """
        if not self.scroll_enabled:
            logger.debug("滚动行为已禁用")
            return
        
        scroll_count = random.randint(self.min_scrolls, self.max_scrolls)
        logger.debug(f"开始模拟滚动，次数: {scroll_count}")
        
        for i in range(scroll_count):
            # 随机滚动距离（200-800 像素）
            scroll_distance = random.randint(200, 800)
            
            # 使用缓动函数模拟自然滚动
            try:
                await page.evaluate(f"""
                    window.scrollBy({{
                        top: {scroll_distance},
                        behavior: 'smooth'
                    }});
                """)
                
                # 随机停留时间
                delay = random.uniform(
                    self.scroll_delay_min / 1000,
                    self.scroll_delay_max / 1000
                )
                await asyncio.sleep(delay)
                
                logger.debug(f"滚动 {i+1}/{scroll_count}: {scroll_distance}px, 延迟 {delay:.2f}s")
                
            except Exception as e:
                logger.warning(f"滚动时出错: {e}")
                break
    
    async def simulate_human_typing(self, page: Page, selector: str, text: str) -> None:
        """
        模拟人类打字速度
        
        Args:
            page: Playwright Page 对象
            selector: 输入框选择器
            text: 要输入的文本
        """
        try:
            element = await page.query_selector(selector)
            if not element:
                logger.warning(f"未找到元素: {selector}")
                return
            
            # 先点击聚焦
            await element.click()
            await asyncio.sleep(0.1)
            
            logger.debug(f"开始模拟打字: {text}")
            
            for i, char in enumerate(text):
                await element.type(char)
                
                # 每个字符之间随机延迟 50-150ms
                delay = random.uniform(0.05, 0.15)
                await asyncio.sleep(delay)
                
                # 偶尔有更长的停顿（模拟思考）
                if random.random() < 0.1:  # 10% 概率
                    think_delay = random.uniform(0.3, 0.8)
                    await asyncio.sleep(think_delay)
                    logger.debug(f"模拟思考停顿: {think_delay:.2f}s")
            
            logger.debug("打字完成")
            
        except Exception as e:
            logger.error(f"模拟打字时出错: {e}")
    
    def get_stealth_scripts(self) -> List[str]:
        """
        获取反检测 JavaScript 脚本列表
        
        Returns:
            脚本列表
        """
        scripts = [
            # 脚本 1: 隐藏 webdriver 标志
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """,
            
            # 脚本 2: 修改 plugins 长度
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            """,
            
            # 脚本 3: 修改 languages
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'zh-CN', 'zh']
            });
            """,
            
            # 脚本 4: 覆盖 permissions API
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            """,
            
            # 脚本 5: 修改 chrome 对象
            """
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            """,
            
            # 脚本 6: 覆盖 navigator.platform
            """
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            """,
            
            # 脚本 7: 修改 hardwareConcurrency
            """
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            """,
            
            # 脚本 8: 修改 deviceMemory
            """
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            """,
        ]
        
        return scripts
    
    async def inject_stealth_scripts(self, page: Page) -> None:
        """
        向页面注入反检测脚本
        
        Args:
            page: Playwright Page 对象
        """
        scripts = self.get_stealth_scripts()
        
        for i, script in enumerate(scripts):
            try:
                await page.evaluate(script)
                logger.debug(f"注入反检测脚本 {i+1}/{len(scripts)}")
            except Exception as e:
                logger.warning(f"注入脚本 {i+1} 失败: {e}")
        
        logger.info("反检测脚本注入完成")
    
    def get_device_config(self, device_type: str) -> Dict[str, Any]:
        """
        获取设备配置
        
        Args:
            device_type: 设备类型 (desktop_edge, desktop_chromium, mobile_iphone, mobile_android)
            
        Returns:
            设备配置字典
        """
        if device_type not in DEVICE_CONFIGS:
            logger.warning(f"未知设备类型: {device_type}，使用默认 desktop_edge")
            device_type = "desktop_edge"
        
        config = DEVICE_CONFIGS[device_type].copy()
        
        # 如果启用了随机视口，则随机化视口大小
        if self.config.get("anti_detection.random_viewport", True):
            base_viewport = config["viewport"]
            config["viewport"] = self.get_random_viewport(
                base_viewport["width"],
                base_viewport["height"]
            )
        
        logger.info(f"获取设备配置: {device_type}")
        return config
