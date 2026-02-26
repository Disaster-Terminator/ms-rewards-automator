"""
通知推送模块
支持 Telegram Bot 和 Server酱 (微信推送)
"""

import logging
from datetime import datetime

import aiohttp

from constants import NOTIFICATION_URLS

logger = logging.getLogger(__name__)


class Notificator:
    """通知推送器类"""

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
        """
        发送 Telegram 消息

        Args:
            message: 消息内容

        Returns:
            是否发送成功
        """
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
                    else:
                        error_text = await response.text()
                        logger.error(f"Telegram 发送失败: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Telegram 发送异常: {e}")
            return False

    async def send_serverchan(self, title: str, content: str) -> bool:
        """
        发送 Server酱 消息（微信推送）

        Args:
            title: 消息标题
            content: 消息内容

        Returns:
            是否发送成功
        """
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
                        else:
                            logger.error(f"Server酱 发送失败: {result.get('message')}")
                            return False
                    else:
                        error_text = await response.text()
                        logger.error(f"Server酱 发送失败: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Server酱 发送异常: {e}")
            return False

    async def send_whatsapp(self, message: str) -> bool:
        """
        发送 WhatsApp 消息（通过 CallMeBot）

        Args:
            message: 消息内容

        Returns:
            是否发送成功
        """
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
                    else:
                        error_text = await response.text()
                        logger.error(f"WhatsApp 发送失败: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"WhatsApp 发送异常: {e}")
            return False

    async def send_daily_report(self, report_data: dict) -> bool:
        """
        发送每日报告

        Args:
            report_data: 报告数据字典

        Returns:
            是否发送成功
        """
        if not self.enabled:
            logger.debug("通知功能未启用")
            return False

        # 提取关键信息
        points_gained = report_data.get("points_gained", 0)
        current_points = report_data.get("current_points", 0)
        desktop_searches = report_data.get("desktop_searches", 0)
        mobile_searches = report_data.get("mobile_searches", 0)
        status = report_data.get("status", "未知")
        alerts = report_data.get("alerts", [])

        # 构建消息
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Telegram 消息（Markdown 格式）
        telegram_msg = f"""🎉 *MS Rewards 每日报告*

📅 日期: {date_str}
💰 今日获得: +{points_gained} 积分
📊 当前总积分: {current_points:,}
🖥️ 桌面搜索: {desktop_searches} 次
📱 移动搜索: {mobile_searches} 次
✅ 状态: {status}
"""

        if alerts:
            telegram_msg += f"\n⚠️ 告警: {len(alerts)} 条"

        # Server酱 消息
        serverchan_title = f"MS Rewards 每日报告 - {date_str}"
        serverchan_content = f"""
## 积分统计
- 今日获得: +{points_gained} 积分
- 当前总积分: {current_points:,}

## 任务完成情况
- 桌面搜索: {desktop_searches} 次
- 移动搜索: {mobile_searches} 次

## 状态
- {status}
"""

        if alerts:
            serverchan_content += f"\n## 告警\n- 共 {len(alerts)} 条告警"

        # WhatsApp 消息（纯文本）
        whatsapp_msg = f"""🎯 MS Rewards 报告

📅 {date_str}
💰 今日: +{points_gained}
📊 总计: {current_points:,}
🖥️ 桌面: {desktop_searches}次
📱 移动: {mobile_searches}次
✅ {status}
"""

        if alerts:
            whatsapp_msg += f"⚠️ 告警: {len(alerts)}条"

        # 发送通知
        success = False

        if self.telegram_enabled:
            success = await self.send_telegram(telegram_msg) or success

        if self.serverchan_enabled:
            success = await self.send_serverchan(serverchan_title, serverchan_content) or success

        if self.whatsapp_enabled:
            success = await self.send_whatsapp(whatsapp_msg) or success

        return success

    async def send_alert(self, alert_type: str, message: str) -> bool:
        """
        发送告警通知

        Args:
            alert_type: 告警类型
            message: 告警消息

        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False

        # Telegram 消息
        telegram_msg = f"""⚠️ *MS Rewards 告警*

类型: {alert_type}
消息: {message}
时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        # Server酱 消息
        serverchan_title = f"MS Rewards 告警 - {alert_type}"
        serverchan_content = f"""
## 告警信息
- 类型: {alert_type}
- 消息: {message}
- 时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        # WhatsApp 消息
        whatsapp_msg = f"""⚠️ MS Rewards 告警

类型: {alert_type}
消息: {message}
时间: {datetime.now().strftime("%H:%M:%S")}
"""

        # 发送通知
        success = False

        if self.telegram_enabled:
            success = await self.send_telegram(telegram_msg) or success

        if self.serverchan_enabled:
            success = await self.send_serverchan(serverchan_title, serverchan_content) or success

        if self.whatsapp_enabled:
            success = await self.send_whatsapp(whatsapp_msg) or success

        return success

    async def test_notification(self) -> dict[str, bool]:
        """
        测试通知功能

        Returns:
            各渠道测试结果
        """
        results = {}

        if self.telegram_enabled:
            logger.info("测试 Telegram 通知...")
            results["telegram"] = await self.send_telegram("🧪 测试消息 - MS Rewards Automator")

        if self.serverchan_enabled:
            logger.info("测试 Server酱 通知...")
            results["serverchan"] = await self.send_serverchan(
                "MS Rewards 测试", "这是一条测试消息"
            )

        if self.whatsapp_enabled:
            logger.info("测试 WhatsApp 通知...")
            results["whatsapp"] = await self.send_whatsapp("🧪 测试消息 - MS Rewards Automator")

        return results

        if self.serverchan_enabled:
            logger.info("测试 Server酱 通知...")
            results["serverchan"] = await self.send_serverchan(
                "测试消息", "这是一条来自 MS Rewards Automator 的测试消息"
            )

        return results
