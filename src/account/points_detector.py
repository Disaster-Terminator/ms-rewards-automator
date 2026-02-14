"""
积分检测器模块
从 Microsoft Rewards Dashboard 抓取积分信息
"""

import logging
import re
from typing import Optional, Dict
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class PointsDetector:
    """积分检测器类"""
    
    DASHBOARD_URL = "https://rewards.bing.com/"
    
    POINTS_SELECTORS = [
        "span.mee-rewards-user-status-balance",
        "span[class*='balance']",
        "div[class*='user-status'] span",
        "[data-m*='points']",
        "span[id*='points']",
        ".rewards-balance",
        "[data-bi-id='rewards-balance']",
        "h1[class*='points']",
        "div[class*='points'] span",
        "span[class*='points']",
    ]
    
    # 任务状态选择器
    TASK_SELECTORS = {
        "desktop_search": [
            "div[data-bi-id='pc-search']",
            "div[class*='desktop-search']",
            "div[class*='pc-search']",
        ],
        "mobile_search": [
            "div[data-bi-id='mobile-search']",
            "div[class*='mobile-search']",
        ],
        "daily_set": [
            "div[data-bi-id='daily-set']",
            "div[class*='daily-set']",
        ]
    }
    
    def __init__(self):
        """初始化积分检测器"""
        logger.info("积分检测器初始化完成")
    
    async def get_current_points(self, page: Page, skip_navigation: bool = False) -> Optional[int]:
        """
        从页面抓取当前积分总数
        
        Args:
            page: Playwright Page 对象
            skip_navigation: 是否跳过导航（如果已经在 Dashboard 页面）
            
        Returns:
            积分数量，失败返回 None
        """
        try:
            if not skip_navigation:
                logger.info(f"导航到 Dashboard: {self.DASHBOARD_URL}")
                
                try:
                    await page.goto(self.DASHBOARD_URL, wait_until="networkidle", timeout=45000)
                except Exception as e:
                    logger.warning(f"页面加载超时，尝试继续: {e}")
                
                await page.wait_for_timeout(3000)
                
                current_url = page.url
                if "login" in current_url.lower() or "oauth" in current_url.lower():
                    logger.info("检测到 OAuth 页面，等待自动登录...")
                    try:
                        await page.wait_for_url("**/rewards.*", timeout=20000)
                        await page.wait_for_timeout(2000)
                    except Exception as e:
                        logger.warning(f"OAuth 等待超时: {e}")
            else:
                logger.debug("跳过导航，使用当前页面")
                await page.wait_for_timeout(1000)
            
            logger.debug("尝试从页面源码提取积分...")
            points = await self._extract_points_from_source(page)
            
            if points is not None:
                logger.info(f"✓ 从源码提取积分: {points:,}")
                return points
            
            logger.debug("源码提取失败，尝试选择器...")
            for selector in self.POINTS_SELECTORS:
                try:
                    logger.debug(f"尝试选择器: {selector}")
                    element = await page.wait_for_selector(selector, timeout=5000)
                    
                    if element:
                        points_text = await element.text_content()
                        logger.debug(f"找到积分文本: {points_text}")
                        
                        points = self._parse_points(points_text)
                        
                        if points is not None and points >= 100:
                            logger.info(f"✓ 当前积分: {points:,}")
                            return points
                        elif points is not None:
                            logger.debug(f"积分值太小，可能是误识别: {points}")
                        
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue
            
            logger.error("无法获取当前积分")
            
            try:
                await page.screenshot(path="screenshots/points_detection_failed.png")
                logger.info("已保存失败截图: screenshots/points_detection_failed.png")
            except Exception:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"获取积分时出错: {e}")
            return None
    
    def _parse_points(self, text: str) -> Optional[int]:
        """
        从文本中解析积分数字
        
        Args:
            text: 包含积分的文本
            
        Returns:
            积分数量，失败返回 None
        """
        if not text:
            return None
        
        try:
            # 移除所有非数字字符（保留数字）
            # 支持格式: "1,234", "1234", "1,234 points", "Available points: 1,234"
            numbers = re.findall(r'\d+', text.replace(',', ''))
            
            if numbers:
                # 取最大的数字（通常是积分总数）
                points = max(int(n) for n in numbers)
                
                # 合理性检查（积分通常在 0 到 1,000,000 之间）
                if 0 <= points <= 1000000:
                    return points
                else:
                    logger.warning(f"积分数值异常: {points}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"解析积分失败: {e}, 文本: {text}")
            return None
    
    async def _extract_points_from_source(self, page: Page) -> Optional[int]:
        """
        从页面源码中提取积分
        
        Args:
            page: Playwright Page 对象
            
        Returns:
            积分数量，失败返回 None
        """
        try:
            await page.wait_for_timeout(2000)
            
            user_balance_selectors = [
                "span.mee-rewards-user-status-balance",
                "div[class*='user-status']",
                "[class*='balance']",
                "[id*='balance']",
            ]
            
            for selector in user_balance_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for elem in elements:
                        text = await elem.text_content()
                        if text:
                            points = self._parse_points(text)
                            if points is not None and points >= 100:
                                logger.debug(f"从用户区域提取积分: {points} (选择器: {selector})")
                                return points
                except Exception as e:
                    logger.debug(f"选择器 {selector} 提取失败: {e}")
                    continue
            
            content = await page.content()
            
            user_points_patterns = [
                r'"availablePoints"\s*:\s*(\d+)',
                r'"pointsBalance"\s*:\s*(\d+)',
                r'"totalPoints"\s*:\s*(\d+)',
                r'"currentPoints"\s*:\s*(\d+)',
                r'"userPoints"\s*:\s*(\d+)',
                r'balance\s*:\s*(\d+)',
            ]
            
            for pattern in user_points_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    for m in matches:
                        try:
                            points = int(m.replace(',', ''))
                            if 100 <= points <= 1000000:
                                logger.debug(f"从源码 JSON 提取积分: {points} (模式: {pattern})")
                                return points
                        except ValueError:
                            continue
            
            try:
                page_text = await page.evaluate("() => document.body.innerText")
                
                balance_patterns = [
                    r'(?:Available|Current|Total|Your)\s*(?:Points?|Balance)[:\s]*(\d[\d,]*)',
                    r'(?:Points?|Balance)[:\s]*(\d[\d,]*)\s*(?:points?)?',
                    r'(\d[\d,]*)\s*(?:Available|Current)\s*(?:points?)',
                ]
                
                for pattern in balance_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        for m in matches:
                            try:
                                points = int(m.replace(',', ''))
                                if 100 <= points <= 1000000:
                                    logger.debug(f"从页面文本提取积分: {points} (模式: {pattern})")
                                    return points
                            except ValueError:
                                continue
            except Exception as e:
                logger.debug(f"从页面文本提取失败: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"从源码提取积分失败: {e}")
            return None
    
    async def get_daily_task_status(self, page: Page) -> Dict[str, dict]:
        """
        获取每日任务完成状态
        
        Args:
            page: Playwright Page 对象
            
        Returns:
            任务状态字典
        """
        tasks = {}
        
        try:
            # 确保在 Dashboard 页面
            if self.DASHBOARD_URL not in page.url:
                await page.goto(self.DASHBOARD_URL, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(3000)
            
            # 检查桌面搜索状态
            tasks["desktop_search"] = await self._check_task_status(
                page, 
                self.TASK_SELECTORS["desktop_search"],
                "桌面搜索"
            )
            
            # 检查移动搜索状态
            tasks["mobile_search"] = await self._check_task_status(
                page,
                self.TASK_SELECTORS["mobile_search"],
                "移动搜索"
            )
            
            # 检查每日任务集
            tasks["daily_set"] = await self._check_task_status(
                page,
                self.TASK_SELECTORS["daily_set"],
                "每日任务"
            )
            
            logger.info(f"任务状态: {tasks}")
            return tasks
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            return tasks
    
    async def _check_task_status(
        self, 
        page: Page, 
        selectors: list, 
        task_name: str
    ) -> dict:
        """
        检查单个任务的状态
        
        Args:
            page: Playwright Page 对象
            selectors: 选择器列表
            task_name: 任务名称
            
        Returns:
            任务状态字典
        """
        status = {
            "found": False,
            "completed": False,
            "progress": None,
            "max_progress": None
        }
        
        try:
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    
                    if element:
                        status["found"] = True
                        
                        # 检查是否完成
                        class_attr = await element.get_attribute("class")
                        data_status = await element.get_attribute("data-bi-status")
                        
                        if class_attr and ("complete" in class_attr.lower() or "done" in class_attr.lower()):
                            status["completed"] = True
                        
                        if data_status and data_status.lower() == "complete":
                            status["completed"] = True
                        
                        # 尝试提取进度
                        text = await element.text_content()
                        if text:
                            # 查找类似 "15/30" 的进度
                            progress_match = re.search(r'(\d+)\s*/\s*(\d+)', text)
                            if progress_match:
                                status["progress"] = int(progress_match.group(1))
                                status["max_progress"] = int(progress_match.group(2))
                                
                                if status["progress"] >= status["max_progress"]:
                                    status["completed"] = True
                        
                        logger.debug(f"{task_name} 状态: {status}")
                        return status
                        
                except Exception as e:
                    logger.debug(f"检查 {task_name} 选择器 {selector} 失败: {e}")
                    continue
            
            logger.debug(f"{task_name} 未找到")
            return status
            
        except Exception as e:
            logger.error(f"检查 {task_name} 状态失败: {e}")
            return status
    
    async def wait_for_points_update(
        self, 
        page: Page, 
        initial_points: int, 
        timeout: int = 30
    ) -> Optional[int]:
        """
        等待积分更新
        
        Args:
            page: Playwright Page 对象
            initial_points: 初始积分
            timeout: 超时时间（秒）
            
        Returns:
            新的积分数量，超时返回 None
        """
        import asyncio
        
        logger.info(f"等待积分更新（初始: {initial_points}）")
        
        start_time = asyncio.get_running_loop().time()
        
        while True:
            # 检查超时
            if asyncio.get_running_loop().time() - start_time > timeout:
                logger.warning(f"等待积分更新超时（{timeout}秒）")
                return None
            
            # 获取当前积分
            current_points = await self.get_current_points(page)
            
            if current_points is not None and current_points > initial_points:
                logger.info(f"✓ 积分已更新: {initial_points} -> {current_points} (+{current_points - initial_points})")
                return current_points
            
            # 等待一段时间再检查
            await asyncio.sleep(2)
