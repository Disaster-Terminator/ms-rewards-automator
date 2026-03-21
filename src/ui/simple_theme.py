"""
简化版主题管理器
只包含核心功能：设置/恢复 Bing 主题
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

from playwright.async_api import BrowserContext

logger = logging.getLogger(__name__)


class SimpleThemeManager:
    """简化版主题管理器，只做核心功能"""

    def __init__(self, config: Any) -> None:
        self.enabled = config.get("bing_theme.enabled", False) if config else False
        self.preferred_theme = config.get("bing_theme.theme", "dark") if config else "dark"
        self.persistence_enabled = (
            config.get("bing_theme.persistence_enabled", False) if config else False
        )
        self.theme_state_file = (
            config.get("bing_theme.theme_state_file", "logs/theme_state.json")
            if config
            else "logs/theme_state.json"
        )

    async def set_theme_cookie(self, context: BrowserContext) -> bool:
        """
        设置主题Cookie

        注意：此方法会读取现有的 SRCHHPGUSR Cookie 并只修改 WEBTHEME 部分，
        以保留用户的其他偏好设置（如 NRSLT, OBHLTH 等）。
        """
        if not self.enabled:
            return True

        theme_value = "1" if self.preferred_theme == "dark" else "0"
        try:
            # 读取现有的 Cookie
            existing_cookies = await context.cookies("https://www.bing.com")
            srchhpgusr_cookie = None

            for cookie in existing_cookies:
                if cookie.get("name") == "SRCHHPGUSR":
                    srchhpgusr_cookie = cookie
                    break

            # 构建新的 Cookie 值
            if srchhpgusr_cookie:
                # 解析现有值，保留其他设置
                existing_value = srchhpgusr_cookie.get("value", "")
                settings = {}

                # 解析现有设置（格式：KEY1=VALUE1;KEY2=VALUE2）
                for setting in existing_value.split(";"):
                    if "=" in setting:
                        key, val = setting.split("=", 1)
                        settings[key.strip()] = val.strip()

                # 更新主题设置
                settings["WEBTHEME"] = theme_value

                # 重建 Cookie 值
                new_value = ";".join(f"{k}={v}" for k, v in settings.items())
            else:
                # 没有现有 Cookie，创建新的
                new_value = f"WEBTHEME={theme_value}"

            # 设置 Cookie
            await context.add_cookies(
                [
                    {
                        "name": "SRCHHPGUSR",
                        "value": new_value,
                        "domain": ".bing.com",
                        "path": "/",
                        "httpOnly": False,
                        "secure": True,
                        "sameSite": "Lax",
                    }
                ]
            )
            return True
        except Exception as e:
            logger.error(f"设置主题Cookie失败: {e}")
            return False

    async def ensure_theme_before_search(self, context: BrowserContext) -> bool:
        """
        在搜索前确保主题Cookie已设置
        这是 SearchEngine 调用的接口方法

        Args:
            context: BrowserContext 对象

        Returns:
            是否成功
        """
        return await self.set_theme_cookie(context)

    def save_theme_state(self, theme: str) -> bool:
        """保存主题状态到文件（同步方法）"""
        if not self.persistence_enabled:
            return True

        try:
            theme_file_path = Path(self.theme_state_file)
            theme_file_path.parent.mkdir(parents=True, exist_ok=True)

            theme_state = {
                "theme": theme,
                "timestamp": time.time(),
            }

            with open(theme_file_path, "w", encoding="utf-8") as f:
                json.dump(theme_state, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存主题状态失败: {e}")
            return False

    def load_theme_state(self) -> str | None:
        """从文件加载主题状态（同步方法）"""
        if not self.persistence_enabled:
            return None

        try:
            theme_file_path = Path(self.theme_state_file)
            if not theme_file_path.exists():
                return None

            with open(theme_file_path, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("theme")
        except Exception as e:
            logger.error(f"加载主题状态失败: {e}")
            return None
