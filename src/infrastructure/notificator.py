"""
通知推送模块
支持 Telegram Bot 和 Server酱 (微信推送)
"""

import logging
from datetime import datetime

import aiohttp

from constants import NOTIFICATION_URLS

logger = logging.getLogger(__name__)

# 消息模板（减少重复代码）
MESSAGE_TEMPLATES = {
    "telegram_daily": (
        "🎉 *MS Rewards 每日报告*\n\n"
        "📅 日期: {date_str}\n"
        "💰 今日获得: +{points_gained} 积分\n"
        "📊 当前总积分: {current_points:,}\n"
        "🖥️ 桌面搜索: {desktop_searches} 次\n"
        "📱 移动搜索: {mobile_searches} 次\n"
        "✅ 状态: {status}"
        "{alerts_section}"
    ),
    "serverchan_daily": (
        "## 积分统计\n"
        "- 今日获得: +{points_gained} 积分\n"
        "- 当前总积分: {current_points:,}\n\n"
        "## 任务完成情况\n"
        "- 桌面搜索: {desktop_searches} 次\n"
        "- 移动搜索: {mobile_searches} 次\n\n"
        "## 状态\n"
        "- {status}"
        "{alerts_section}"
    ),
    "whatsapp_daily": (
        "🎯 MS Rewards 报告\n\n"
        "📅 {date_str}\n"
        "💰 今日: +{points_gained}\n"
        "📊 总计: {current_points:,}\n"
        "🖥️ 桌面: {desktop_searches}次\n"
        "📱 移动: {mobile_searches}次\n"
        "✅ {status}"
        "{alerts_section}"
    ),
    "telegram_alert": (
        "⚠️ *MS Rewards 告警*\n\n类型: {alert_type}\n消息: {message}\n时间: {time_str}"
    ),
    "serverchan_alert": (
        "## 告警信息\n- 类型: {alert_type}\n- 消息: {message}\n- 时间: {time_str}"
    ),
    "whatsapp_alert": (
        "⚠️ MS Rewards 告警\n\n类型: {alert_type}\n消息: {message}\n时间: {time_str}"
    ),
}

# 测试消息
TEST_MESSAGES = {
    "telegram": "🧪 测试消息 - MS Rewards Automator",
    "serverchan_title": "MS Rewards 测试",
    "serverchan_content": "这是一条测试消息",
    "whatsapp": "🧪 测试消息 - MS Rewards Automator",
}


class Notificator:
    """通知推送器类 - 简化版"""

    def __init__(self, config):
        """
        初始化通知推送器

        Args:
            config: ConfigManager 实例
        """
        self.config = config

        self.enabled = config.get("notification.enabled", False)
        self.telegram_enabled = config.get("notification.telegram.enabled", False)
        self.telegram_bot_token = config.get_with_env(
            "notification.telegram.bot_token", "TELEGRAM_BOT_TOKEN", ""
        )
        self.telegram_chat_id = config.get_with_env(
            "notification.telegram.chat_id", "TELEGRAM_CHAT_ID", ""
        )

        self.serverchan_enabled = config.get("notification.serverchan.enabled", False)
        self.serverchan_key = config.get_with_env(
            "notification.serverchan.key", "SERVERCHAN_KEY", ""
        )

        self.whatsapp_enabled = config.get("notification.whatsapp.enabled", False)
        self.whatsapp_phone = config.get_with_env(
            "notification.whatsapp.phone", "WHATSAPP_PHONE", ""
        )
        self.whatsapp_apikey = config.get_with_env(
            "notification.whatsapp.apikey", "WHATSAPP_APIKEY", ""
        )

        logger.info(f"通知推送器初始化完成 (enabled={self.enabled})")
        if self.telegram_enabled:
            logger.info("  - Telegram Bot: 已启用")
        if self.serverchan_enabled:
            logger.info("  - Server酱: 已启用")
        if self.whatsapp_enabled:
            logger.info("  - WhatsApp: 已启用")

    async def send_telegram(self, message: str) -> bool:
        """发送 Telegram 消息"""
        if not self.telegram_enabled or not self.telegram_bot_token or not self.telegram_chat_id:
            logger.debug("Telegram 未配置，跳过发送")
            return False

        url = NOTIFICATION_URLS["telegram_api"].format(token=self.telegram_bot_token)
        payload = {"chat_id": self.telegram_chat_id, "text": message, "parse_mode": "Markdown"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        logger.info("✓ Telegram 消息发送成功")
                        return True
                    error_text = await response.text()
                    logger.error(f"Telegram 发送失败: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Telegram 发送异常: {e}")
            return False

    async def send_serverchan(self, title: str, content: str) -> bool:
        """发送 Server酱 消息"""
        if not self.serverchan_enabled or not self.serverchan_key:
            logger.debug("Server酱 未配置，跳过发送")
            return False

        url = NOTIFICATION_URLS["serverchan"].format(key=self.serverchan_key)
        payload = {"title": title, "desp": content}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == 0:
                            logger.info("✓ Server酱 消息发送成功")
                            return True
                        logger.error(f"Server酱 发送失败: {result.get('message')}")
                        return False
                    error_text = await response.text()
                    logger.error(f"Server酱 发送失败: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Server酱 发送异常: {e}")
            return False

    async def send_whatsapp(self, message: str) -> bool:
        """发送 WhatsApp 消息"""
        if not self.whatsapp_enabled or not self.whatsapp_phone or not self.whatsapp_apikey:
            logger.debug("WhatsApp 未配置，跳过发送")
            return False

        url = NOTIFICATION_URLS["callmebot_whatsapp"]
        params = {"phone": self.whatsapp_phone, "text": message, "apikey": self.whatsapp_apikey}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        logger.info("✓ WhatsApp 消息发送成功")
                        return True
                    error_text = await response.text()
                    logger.error(f"WhatsApp 发送失败: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"WhatsApp 发送异常: {e}")
            return False

    # ============================================
    # 公共接口
    # ============================================

    async def send_daily_report(self, report_data: dict) -> bool:
        """发送每日报告（使用统一模板）"""
        if not self.enabled:
            logger.debug("通知功能未启用")
            return False

        # 准备数据
        data = {
            "date_str": datetime.now().strftime("%Y-%m-%d"),
            "points_gained": report_data.get("points_gained") or 0,
            "current_points": report_data.get("current_points") or 0,
            "desktop_searches": report_data.get("desktop_searches") or 0,
            "mobile_searches": report_data.get("mobile_searches") or 0,
            "status": report_data.get("status") or "未知",
            "alerts_section": "",
        }

        alerts = report_data.get("alerts", [])
        if alerts:
            data["alerts_section"] = f"\n⚠️ 告警: {len(alerts)} 条"

        success = False

        if self.telegram_enabled:
            msg = MESSAGE_TEMPLATES["telegram_daily"].format(**data)
            success = await self.send_telegram(msg) or success

        if self.serverchan_enabled:
            date_str = data["date_str"]
            title = f"MS Rewards 每日报告 - {date_str}"
            content = MESSAGE_TEMPLATES["serverchan_daily"].format(**data)
            success = await self.send_serverchan(title, content) or success

        if self.whatsapp_enabled:
            msg = MESSAGE_TEMPLATES["whatsapp_daily"].format(**data)
            success = await self.send_whatsapp(msg) or success

        return success

    async def send_alert(self, alert_type: str, message: str) -> bool:
        """发送告警通知（使用统一模板）"""
        if not self.enabled:
            return False

        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 转义花括号，防止 str.format() 将消息中的 {placeholder} 误认为格式字段
        data = {
            "alert_type": alert_type.replace("{", "{{").replace("}", "}}"),
            "message": message.replace("{", "{{").replace("}", "}}"),
            "time_str": time_str,
        }

        success = False

        if self.telegram_enabled:
            msg = MESSAGE_TEMPLATES["telegram_alert"].format(**data)
            success = await self.send_telegram(msg) or success

        if self.serverchan_enabled:
            title = f"MS Rewards 告警 - {alert_type}"
            content = MESSAGE_TEMPLATES["serverchan_alert"].format(**data)
            success = await self.send_serverchan(title, content) or success

        if self.whatsapp_enabled:
            msg = MESSAGE_TEMPLATES["whatsapp_alert"].format(**data)
            success = await self.send_whatsapp(msg) or success

        return success

    async def test_notification(self) -> dict[str, bool]:
        """测试通知功能"""
        results = {}

        if self.telegram_enabled:
            logger.info("测试 Telegram 通知...")
            results["telegram"] = await self.send_telegram(TEST_MESSAGES["telegram"])

        if self.serverchan_enabled:
            logger.info("测试 Server酱 通知...")
            results["serverchan"] = await self.send_serverchan(
                TEST_MESSAGES["serverchan_title"], TEST_MESSAGES["serverchan_content"]
            )

        if self.whatsapp_enabled:
            logger.info("测试 WhatsApp 通知...")
            results["whatsapp"] = await self.send_whatsapp(TEST_MESSAGES["whatsapp"])

        return results
