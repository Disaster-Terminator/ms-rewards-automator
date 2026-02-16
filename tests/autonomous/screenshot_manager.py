"""
截图管理器
自动截图、命名、存储和管理测试截图
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ScreenshotManager:
    """截图管理器"""

    def __init__(self, base_dir: str = "logs/screenshots"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.screenshots: list[dict[str, Any]] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.base_dir / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"截图管理器初始化: {self.session_dir}")

    async def capture(
        self, page, name: str, context: str = "", full_page: bool = False
    ) -> str | None:
        """
        捕获截图

        Args:
            page: Playwright Page 对象
            name: 截图名称
            context: 上下文描述
            full_page: 是否全页截图（默认False，避免页面滚动）

        Returns:
            截图路径
        """
        try:
            timestamp = datetime.now().strftime("%H%M%S_%f")
            safe_name = name.replace(" ", "_").replace("/", "_")[:50]
            filename = f"{timestamp}_{safe_name}.png"
            filepath = self.session_dir / filename

            await page.screenshot(path=str(filepath), full_page=full_page)

            screenshot_record = {
                "timestamp": datetime.now().isoformat(),
                "filename": filename,
                "filepath": str(filepath),
                "name": name,
                "context": context,
                "url": page.url if page else None,
            }

            self.screenshots.append(screenshot_record)
            logger.debug(f"截图已保存: {filename}")

            return str(filepath)

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    async def capture_on_error(self, page, error: Exception, context: str = "") -> str | None:
        """错误时自动截图"""
        error_name = f"error_{type(error).__name__}"
        return await self.capture(page, error_name, context=f"ERROR: {context} - {str(error)}")

    async def capture_element(self, page, selector: str, name: str) -> str | None:
        """截取特定元素"""
        try:
            element = await page.query_selector(selector)
            if element:
                timestamp = datetime.now().strftime("%H%M%S_%f")
                safe_name = name.replace(" ", "_")[:30]
                filename = f"{timestamp}_element_{safe_name}.png"
                filepath = self.session_dir / filename

                await element.screenshot(path=str(filepath))

                self.screenshots.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "filename": filename,
                        "filepath": str(filepath),
                        "name": name,
                        "context": f"Element: {selector}",
                        "url": page.url,
                    }
                )

                return str(filepath)
        except Exception as e:
            logger.debug(f"元素截图失败 {selector}: {e}")
        return None

    def get_session_summary(self) -> dict[str, Any]:
        """获取会话截图摘要"""
        return {
            "session_id": self.session_id,
            "session_dir": str(self.session_dir),
            "total_screenshots": len(self.screenshots),
            "screenshots": self.screenshots,
        }

    def save_manifest(self) -> str:
        """保存截图清单"""
        manifest_path = self.session_dir / "manifest.json"

        manifest = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "total_screenshots": len(self.screenshots),
            "screenshots": self.screenshots,
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"截图清单已保存: {manifest_path}")
        return str(manifest_path)
