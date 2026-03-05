"""
简化版主题管理器
只包含核心功能：设置/恢复 Bing 主题
"""

import json
import time
from pathlib import Path

from playwright.async_api import BrowserContext


class SimpleThemeManager:
    """简化版主题管理器，只做核心功能"""

    def __init__(self, config):
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
        """设置主题Cookie"""
        if not self.enabled:
            return True

        theme_value = "1" if self.preferred_theme == "dark" else "0"
        try:
            await context.add_cookies(
                [
                    {
                        "name": "SRCHHPGUSR",
                        "value": f"WEBTHEME={theme_value}",
                        "domain": ".bing.com",
                        "path": "/",
                        "httpOnly": False,
                        "secure": True,
                        "sameSite": "Lax",
                    }
                ]
            )
            return True
        except Exception:
            return False

    async def save_theme_state(self, theme: str) -> bool:
        """保存主题状态到文件"""
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
        except Exception:
            return False

    async def load_theme_state(self) -> str | None:
        """从文件加载主题状态"""
        if not self.persistence_enabled:
            return None

        try:
            theme_file_path = Path(self.theme_state_file)
            if not theme_file_path.exists():
                return None

            with open(theme_file_path, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("theme")
        except Exception:
            return None
