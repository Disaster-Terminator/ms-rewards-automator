"""
Bing主题管理器模块
处理Bing搜索页面的深色主题设置和持久化
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import Page, BrowserContext, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

logger = logging.getLogger(__name__)


class BingThemeManager:
    """Bing主题管理器类"""
    
    def __init__(self, config=None):
        """
        初始化Bing主题管理器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.enabled = config.get("bing_theme.enabled", True) if config else True
        self.preferred_theme = config.get("bing_theme.theme", "dark") if config else "dark"
        self.force_theme = config.get("bing_theme.force_theme", True) if config else True
        
        # 会话间主题持久化配置
        self.persistence_enabled = config.get("bing_theme.persistence_enabled", True) if config else True
        self.theme_state_file = config.get("bing_theme.theme_state_file", "logs/theme_state.json") if config else "logs/theme_state.json"
        
        # 主题状态缓存
        self._theme_state_cache = None
        self._last_cache_update = 0
        self._cache_ttl = 300  # 5分钟缓存TTL
        
        # 主题相关的选择器
        self.theme_selectors = {
            "settings_button": [
                "button[aria-label*='Settings']",
                "button[title*='Settings']", 
                "a[href*='preferences']",
                "#id_sc",  # Bing设置按钮ID
                ".b_idOpen",  # Bing设置菜单
            ],
            "theme_option": [
                "input[value='dark']",
                "input[name='SRCHHPGUSR'][value*='THEME:1']",
                "label:has-text('Dark')",
                "div[data-value='dark']",
            ],
            "save_button": [
                "input[type='submit'][value*='Save']",
                "button:has-text('Save')",
                "input[value='保存']",
                "button:has-text('保存')",
            ]
        }
        
        logger.info(f"Bing主题管理器初始化完成 (enabled={self.enabled}, theme={self.preferred_theme}, persistence={self.persistence_enabled})")
    
    async def save_theme_state(self, theme: str, context_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        保存主题状态到持久化存储
        这是任务6.2.2的核心功能：实现会话间主题保持
        
        Args:
            theme: 当前主题
            context_info: 浏览器上下文信息
            
        Returns:
            是否保存成功
        """
        if not self.persistence_enabled:
            logger.debug("主题持久化已禁用")
            return True
        
        try:
            logger.debug(f"保存主题状态: {theme}")
            
            # 准备主题状态数据
            theme_state = {
                "theme": theme,
                "timestamp": asyncio.get_running_loop().time(),
                "preferred_theme": self.preferred_theme,
                "force_theme": self.force_theme,
                "context_info": context_info or {},
                "version": "1.0"
            }
            
            # 确保目录存在
            theme_file_path = Path(self.theme_state_file)
            theme_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存到文件
            with open(theme_file_path, 'w', encoding='utf-8') as f:
                json.dump(theme_state, f, indent=2, ensure_ascii=False)
            
            # 更新缓存
            self._theme_state_cache = theme_state
            self._last_cache_update = asyncio.get_running_loop().time()
            
            logger.debug(f"✓ 主题状态已保存到: {self.theme_state_file}")
            return True
            
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"保存主题状态失败（文件操作错误）: {e}")
            return False
        except json.JSONEncodeError as e:
            logger.error(f"保存主题状态失败（JSON编码错误）: {e}")
            return False
        except Exception as e:
            logger.error(f"保存主题状态时发生意外错误: {e}")
            return False
    
    async def load_theme_state(self) -> Optional[Dict[str, Any]]:
        """
        从持久化存储加载主题状态
        这是任务6.2.2的核心功能：实现会话间主题保持
        
        Returns:
            主题状态字典或None
        """
        if not self.persistence_enabled:
            logger.debug("主题持久化已禁用")
            return None
        
        try:
            # 检查缓存是否有效
            current_time = asyncio.get_running_loop().time()
            if (self._theme_state_cache and 
                self._last_cache_update and 
                current_time - self._last_cache_update < self._cache_ttl):
                logger.debug("使用缓存的主题状态")
                return self._theme_state_cache
            
            # 检查文件是否存在
            theme_file_path = Path(self.theme_state_file)
            if not theme_file_path.exists():
                logger.debug(f"主题状态文件不存在: {self.theme_state_file}")
                return None
            
            # 从文件加载
            with open(theme_file_path, 'r', encoding='utf-8') as f:
                theme_state = json.load(f)
            
            # 验证数据完整性
            if not self._validate_theme_state(theme_state):
                logger.warning("主题状态数据无效，忽略")
                return None
            
            # 更新缓存
            self._theme_state_cache = theme_state
            self._last_cache_update = current_time
            
            logger.debug(f"✓ 从文件加载主题状态: {theme_state.get('theme', '未知')}")
            return theme_state
            
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"加载主题状态失败（文件操作错误）: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"加载主题状态失败（JSON解析错误）: {e}")
            return None
        except Exception as e:
            logger.error(f"加载主题状态时发生意外错误: {e}")
            return None
    
    def _validate_theme_state(self, theme_state: Dict[str, Any]) -> bool:
        """
        验证主题状态数据的完整性
        
        Args:
            theme_state: 主题状态数据
            
        Returns:
            是否有效
        """
        try:
            # 检查必需字段
            required_fields = ["theme", "timestamp", "version"]
            for field in required_fields:
                if field not in theme_state:
                    logger.debug(f"主题状态缺少必需字段: {field}")
                    return False
            
            # 检查主题值是否有效
            theme = theme_state.get("theme")
            if theme not in ["dark", "light"]:
                logger.debug(f"无效的主题值: {theme}")
                return False
            
            # 检查时间戳是否合理（不能太旧）
            timestamp = theme_state.get("timestamp", 0)
            current_time = asyncio.get_running_loop().time()
            max_age = 30 * 24 * 3600  # 30天
            
            if current_time - timestamp > max_age:
                logger.debug("主题状态过期")
                return False
            
            return True
            
        except (KeyError, TypeError, ValueError) as e:
            logger.debug(f"验证主题状态时数据格式错误: {e}")
            return False
    
    async def restore_theme_from_state(self, page: Page) -> bool:
        """
        从持久化状态恢复主题设置
        这是任务6.2.2的核心功能：在新会话中恢复主题
        
        Args:
            page: Playwright页面对象
            
        Returns:
            是否恢复成功
        """
        if not self.persistence_enabled:
            logger.debug("主题持久化已禁用")
            return True
        
        try:
            logger.debug("尝试从持久化状态恢复主题...")
            
            # 加载保存的主题状态
            theme_state = await self.load_theme_state()
            if not theme_state:
                logger.debug("没有找到保存的主题状态")
                return False
            
            saved_theme = theme_state.get("theme")
            if not saved_theme:
                logger.debug("主题状态中没有主题信息")
                return False
            
            # 检查当前主题是否已经匹配
            current_theme = await self.detect_current_theme(page)
            if current_theme == saved_theme:
                logger.debug(f"当前主题已经是 {saved_theme}，无需恢复")
                return True
            
            logger.info(f"恢复主题设置: {current_theme} -> {saved_theme}")
            
            # 尝试恢复主题
            success = await self.set_theme(page, saved_theme)
            if success:
                logger.info(f"✓ 主题恢复成功: {saved_theme}")
                
                # 验证恢复结果
                await asyncio.sleep(1)
                restored_theme = await self.detect_current_theme(page)
                if restored_theme == saved_theme:
                    logger.debug("主题恢复验证成功")
                    return True
                else:
                    logger.warning(f"主题恢复验证失败: 期望 {saved_theme}, 实际 {restored_theme}")
                    return False
            else:
                logger.warning(f"主题恢复失败: {saved_theme}")
                return False
                
        except PlaywrightTimeout:
            logger.error("从持久化状态恢复主题超时")
            return False
        except PlaywrightError as e:
            logger.error(f"从持久化状态恢复主题失败: {e}")
            return False
        except Exception as e:
            logger.error(f"从持久化状态恢复主题时发生意外错误: {e}")
            return False
    
    async def ensure_theme_persistence(self, page: Page, context: Optional[BrowserContext] = None) -> bool:
        """
        确保主题设置的持久化
        这是任务6.2.2的扩展功能：主动确保主题持久化
        
        Args:
            page: Playwright页面对象
            context: 浏览器上下文（可选）
            
        Returns:
            是否成功确保持久化
        """
        if not self.persistence_enabled:
            logger.debug("主题持久化已禁用")
            return True
        
        try:
            logger.debug("确保主题设置的持久化...")
            
            # 1. 检测当前主题
            current_theme = await self.detect_current_theme(page)
            if not current_theme:
                logger.debug("无法检测当前主题，跳过持久化")
                return False
            
            # 2. 收集上下文信息
            context_info = {}
            if context:
                try:
                    # 获取用户代理
                    user_agent = await page.evaluate("navigator.userAgent")
                    context_info["user_agent"] = user_agent
                    
                    # 获取视口信息
                    viewport = page.viewport_size
                    if viewport:
                        context_info["viewport"] = {
                            "width": viewport["width"],
                            "height": viewport["height"]
                        }
                    
                    # 获取设备信息
                    is_mobile = await page.evaluate("'ontouchstart' in window")
                    context_info["is_mobile"] = is_mobile
                    
                except (PlaywrightTimeout, PlaywrightError) as e:
                    logger.debug(f"收集上下文信息失败: {e}")
            
            # 3. 保存主题状态
            save_success = await self.save_theme_state(current_theme, context_info)
            if not save_success:
                logger.warning("保存主题状态失败")
                return False
            
            # 4. 尝试在浏览器中设置持久化标记
            try:
                await self._set_browser_persistence_markers(page, current_theme)
            except (PlaywrightTimeout, PlaywrightError) as e:
                logger.debug(f"设置浏览器持久化标记失败: {e}")
            
            # 5. 如果有上下文，尝试保存到存储状态
            if context:
                try:
                    await self._save_theme_to_storage_state(context, current_theme)
                except (PlaywrightTimeout, PlaywrightError) as e:
                    logger.debug(f"保存主题到存储状态失败: {e}")
            
            logger.debug(f"✓ 主题持久化确保完成: {current_theme}")
            return True
            
        except PlaywrightTimeout:
            logger.error("确保主题持久化超时")
            return False
        except PlaywrightError as e:
            logger.error(f"确保主题持久化失败: {e}")
            return False
        except Exception as e:
            logger.error(f"确保主题持久化时发生意外错误: {e}")
            return False
    
    async def _set_browser_persistence_markers(self, page: Page, theme: str) -> bool:
        """
        在浏览器中设置持久化标记
        
        Args:
            page: Playwright页面对象
            theme: 主题
            
        Returns:
            是否设置成功
        """
        try:
            await page.evaluate(f"""
                () => {{
                    const theme = '{theme}';
                    const timestamp = Date.now();
                    
                    try {{
                        // 在localStorage中设置持久化标记
                        const persistenceData = {{
                            theme: theme,
                            timestamp: timestamp,
                            source: 'bing_theme_manager',
                            version: '1.0'
                        }};
                        
                        localStorage.setItem('bing-theme-persistence', JSON.stringify(persistenceData));
                        localStorage.setItem('theme-preference', theme);
                        localStorage.setItem('last-theme-update', timestamp.toString());
                        
                        // 在sessionStorage中也设置标记
                        sessionStorage.setItem('current-theme', theme);
                        sessionStorage.setItem('theme-source', 'persistence');
                        
                        // 设置页面属性标记
                        document.documentElement.setAttribute('data-persistent-theme', theme);
                        document.body.setAttribute('data-persistent-theme', theme);
                        
                        return true;
                    }} catch (e) {{
                        console.debug('设置持久化标记失败:', e);
                        return false;
                    }}
                }}
            """)
            
            logger.debug(f"✓ 浏览器持久化标记设置完成: {theme}")
            return True
            
        except PlaywrightTimeout:
            logger.debug("设置浏览器持久化标记超时")
            return False
        except PlaywrightError as e:
            logger.debug(f"设置浏览器持久化标记失败: {e}")
            return False
    
    async def _save_theme_to_storage_state(self, context: BrowserContext, theme: str) -> bool:
        """
        将主题信息保存到浏览器存储状态
        
        Args:
            context: 浏览器上下文
            theme: 主题
            
        Returns:
            是否保存成功
        """
        try:
            # 获取当前存储状态
            storage_state = await context.storage_state()
            
            # 添加主题相关的localStorage条目
            if "origins" not in storage_state:
                storage_state["origins"] = []
            
            # 查找或创建bing.com的存储条目
            bing_origin = None
            for origin in storage_state["origins"]:
                if "bing.com" in origin.get("origin", ""):
                    bing_origin = origin
                    break
            
            if not bing_origin:
                bing_origin = {
                    "origin": "https://www.bing.com",
                    "localStorage": []
                }
                storage_state["origins"].append(bing_origin)
            
            if "localStorage" not in bing_origin:
                bing_origin["localStorage"] = []
            
            # 添加或更新主题相关的localStorage条目
            theme_entries = [
                {"name": "bing-theme-persistence", "value": json.dumps({
                    "theme": theme,
                    "timestamp": asyncio.get_running_loop().time(),
                    "source": "bing_theme_manager",
                    "version": "1.0"
                })},
                {"name": "theme-preference", "value": theme},
                {"name": "last-theme-update", "value": str(int(asyncio.get_running_loop().time()))}
            ]
            
            # 移除旧的主题条目
            bing_origin["localStorage"] = [
                item for item in bing_origin["localStorage"] 
                if item.get("name") not in ["bing-theme-persistence", "theme-preference", "last-theme-update"]
            ]
            
            # 添加新的主题条目
            bing_origin["localStorage"].extend(theme_entries)
            
            logger.debug(f"✓ 主题信息已添加到存储状态: {theme}")
            return True
            
        except PlaywrightTimeout:
            logger.debug("保存主题到存储状态超时")
            return False
        except PlaywrightError as e:
            logger.debug(f"保存主题到存储状态失败: {e}")
            return False
    
    async def check_theme_persistence_integrity(self, page: Page) -> Dict[str, Any]:
        """
        检查主题持久化的完整性
        这是任务6.2.2的验证功能：确保持久化机制正常工作
        
        Args:
            page: Playwright页面对象
            
        Returns:
            完整性检查结果
        """
        integrity_result = {
            "overall_status": "unknown",
            "file_persistence": {"status": "unknown", "details": {}},
            "browser_persistence": {"status": "unknown", "details": {}},
            "theme_consistency": {"status": "unknown", "details": {}},
            "recommendations": [],
            "timestamp": asyncio.get_running_loop().time()
        }
        
        try:
            logger.debug("检查主题持久化完整性...")
            
            # 1. 检查文件持久化
            file_check = await self._check_file_persistence()
            integrity_result["file_persistence"] = file_check
            
            # 2. 检查浏览器持久化
            browser_check = await self._check_browser_persistence(page)
            integrity_result["browser_persistence"] = browser_check
            
            # 3. 检查主题一致性
            consistency_check = await self._check_theme_consistency(page)
            integrity_result["theme_consistency"] = consistency_check
            
            # 4. 计算总体状态
            status_scores = {
                "good": 3,
                "warning": 2,
                "error": 1,
                "unknown": 0
            }
            
            total_score = 0
            max_score = 0
            
            for check_name in ["file_persistence", "browser_persistence", "theme_consistency"]:
                check_result = integrity_result[check_name]
                status = check_result.get("status", "unknown")
                score = status_scores.get(status, 0)
                total_score += score
                max_score += 3
            
            if max_score > 0:
                score_ratio = total_score / max_score
                if score_ratio >= 0.8:
                    integrity_result["overall_status"] = "good"
                elif score_ratio >= 0.5:
                    integrity_result["overall_status"] = "warning"
                else:
                    integrity_result["overall_status"] = "error"
            
            # 5. 生成建议
            recommendations = self._generate_persistence_recommendations(integrity_result)
            integrity_result["recommendations"] = recommendations
            
            logger.debug(f"主题持久化完整性检查完成: {integrity_result['overall_status']}")
            return integrity_result
            
        except Exception as e:
            error_msg = f"检查主题持久化完整性失败: {str(e)}"
            logger.error(error_msg)
            integrity_result["overall_status"] = "error"
            integrity_result["error"] = error_msg
            return integrity_result
    
    async def _check_file_persistence(self) -> Dict[str, Any]:
        """检查文件持久化状态"""
        result = {"status": "unknown", "details": {}}
        
        try:
            theme_file_path = Path(self.theme_state_file)
            
            if not theme_file_path.exists():
                result["status"] = "warning"
                result["details"]["message"] = "主题状态文件不存在"
                result["details"]["file_path"] = str(theme_file_path)
                return result
            
            # 检查文件内容
            theme_state = await self.load_theme_state()
            if not theme_state:
                result["status"] = "error"
                result["details"]["message"] = "主题状态文件无效或损坏"
                return result
            
            # 检查文件年龄
            file_stat = theme_file_path.stat()
            file_age = asyncio.get_running_loop().time() - file_stat.st_mtime
            
            result["status"] = "good"
            result["details"] = {
                "message": "文件持久化正常",
                "file_path": str(theme_file_path),
                "file_size": file_stat.st_size,
                "file_age_seconds": file_age,
                "saved_theme": theme_state.get("theme"),
                "last_update": theme_state.get("timestamp")
            }
            
            return result
            
        except Exception as e:
            result["status"] = "error"
            result["details"]["message"] = f"检查文件持久化失败: {str(e)}"
            return result
    
    async def _check_browser_persistence(self, page: Page) -> Dict[str, Any]:
        """检查浏览器持久化状态"""
        result = {"status": "unknown", "details": {}}
        
        try:
            browser_persistence = await page.evaluate("""
                () => {
                    try {
                        const result = {
                            localStorage_markers: {},
                            sessionStorage_markers: {},
                            dom_markers: {}
                        };
                        
                        // 检查localStorage标记
                        const persistenceData = localStorage.getItem('bing-theme-persistence');
                        if (persistenceData) {
                            try {
                                result.localStorage_markers.persistence_data = JSON.parse(persistenceData);
                            } catch (e) {
                                result.localStorage_markers.persistence_data = 'invalid_json';
                            }
                        }
                        
                        result.localStorage_markers.theme_preference = localStorage.getItem('theme-preference');
                        result.localStorage_markers.last_theme_update = localStorage.getItem('last-theme-update');
                        
                        // 检查sessionStorage标记
                        result.sessionStorage_markers.current_theme = sessionStorage.getItem('current-theme');
                        result.sessionStorage_markers.theme_source = sessionStorage.getItem('theme-source');
                        
                        // 检查DOM标记
                        result.dom_markers.html_persistent_theme = document.documentElement.getAttribute('data-persistent-theme');
                        result.dom_markers.body_persistent_theme = document.body.getAttribute('data-persistent-theme');
                        
                        return result;
                    } catch (e) {
                        return { error: e.message };
                    }
                }
            """)
            
            if "error" in browser_persistence:
                result["status"] = "error"
                result["details"]["message"] = f"浏览器持久化检查失败: {browser_persistence['error']}"
                return result
            
            # 分析结果
            has_localStorage = any(browser_persistence["localStorage_markers"].values())
            has_sessionStorage = any(browser_persistence["sessionStorage_markers"].values())
            has_dom_markers = any(browser_persistence["dom_markers"].values())
            
            if has_localStorage and has_sessionStorage and has_dom_markers:
                result["status"] = "good"
                result["details"]["message"] = "浏览器持久化标记完整"
            elif has_localStorage or has_sessionStorage:
                result["status"] = "warning"
                result["details"]["message"] = "浏览器持久化标记部分缺失"
            else:
                result["status"] = "error"
                result["details"]["message"] = "浏览器持久化标记缺失"
            
            result["details"]["markers"] = browser_persistence
            return result
            
        except Exception as e:
            result["status"] = "error"
            result["details"]["message"] = f"检查浏览器持久化失败: {str(e)}"
            return result
    
    async def _check_theme_consistency(self, page: Page) -> Dict[str, Any]:
        """检查主题一致性"""
        result = {"status": "unknown", "details": {}}
        
        try:
            # 获取当前检测到的主题
            current_theme = await self.detect_current_theme(page)
            
            # 获取保存的主题状态
            saved_theme_state = await self.load_theme_state()
            saved_theme = saved_theme_state.get("theme") if saved_theme_state else None
            
            # 获取配置的首选主题
            preferred_theme = self.preferred_theme
            
            result["details"] = {
                "current_theme": current_theme,
                "saved_theme": saved_theme,
                "preferred_theme": preferred_theme
            }
            
            # 检查一致性
            themes = [current_theme, saved_theme, preferred_theme]
            unique_themes = set(filter(None, themes))
            
            if len(unique_themes) == 1:
                result["status"] = "good"
                result["details"]["message"] = "主题完全一致"
            elif len(unique_themes) == 2:
                result["status"] = "warning"
                result["details"]["message"] = "主题部分不一致"
            else:
                result["status"] = "error"
                result["details"]["message"] = "主题严重不一致"
            
            return result
            
        except Exception as e:
            result["status"] = "error"
            result["details"]["message"] = f"检查主题一致性失败: {str(e)}"
            return result
    
    def _generate_persistence_recommendations(self, integrity_result: Dict[str, Any]) -> list:
        """生成持久化建议"""
        recommendations = []
        
        try:
            # 基于文件持久化状态的建议
            file_status = integrity_result.get("file_persistence", {}).get("status")
            if file_status == "warning":
                recommendations.append("建议运行一次主题设置以创建持久化文件")
            elif file_status == "error":
                recommendations.append("主题状态文件损坏，建议删除后重新设置主题")
            
            # 基于浏览器持久化状态的建议
            browser_status = integrity_result.get("browser_persistence", {}).get("status")
            if browser_status == "warning":
                recommendations.append("浏览器持久化标记不完整，建议刷新页面后重新设置主题")
            elif browser_status == "error":
                recommendations.append("浏览器持久化标记缺失，建议重新设置主题")
            
            # 基于主题一致性的建议
            consistency_status = integrity_result.get("theme_consistency", {}).get("status")
            if consistency_status == "warning":
                recommendations.append("主题设置不一致，建议统一主题配置")
            elif consistency_status == "error":
                recommendations.append("主题设置严重不一致，建议重置所有主题设置")
            
            # 总体建议
            overall_status = integrity_result.get("overall_status")
            if overall_status == "good":
                recommendations.append("主题持久化工作正常，无需额外操作")
            elif overall_status == "warning":
                recommendations.append("建议定期检查主题持久化状态")
            elif overall_status == "error":
                recommendations.append("建议重新配置主题持久化设置")
            
            # 如果没有具体建议，提供通用建议
            if not recommendations:
                recommendations.append("建议检查主题配置和网络连接")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成持久化建议时发生异常: {e}")
            return ["生成建议时发生错误，建议手动检查主题设置"]
    
    async def cleanup_theme_persistence(self) -> bool:
        """
        清理主题持久化数据
        用于重置或故障排除
        
        Returns:
            是否清理成功
        """
        try:
            logger.info("清理主题持久化数据...")
            
            success_count = 0
            total_operations = 0
            
            # 1. 删除主题状态文件
            total_operations += 1
            try:
                theme_file_path = Path(self.theme_state_file)
                if theme_file_path.exists():
                    theme_file_path.unlink()
                    logger.debug(f"✓ 删除主题状态文件: {self.theme_state_file}")
                else:
                    logger.debug(f"主题状态文件不存在: {self.theme_state_file}")
                success_count += 1
            except Exception as e:
                logger.warning(f"删除主题状态文件失败: {e}")
            
            # 2. 清理缓存
            total_operations += 1
            try:
                self._theme_state_cache = None
                self._last_cache_update = 0
                logger.debug("✓ 清理主题状态缓存")
                success_count += 1
            except Exception as e:
                logger.warning(f"清理主题状态缓存失败: {e}")
            
            # 计算成功率
            success_rate = success_count / total_operations if total_operations > 0 else 0
            
            if success_rate >= 0.8:
                logger.info(f"✓ 主题持久化数据清理完成 ({success_count}/{total_operations})")
                return True
            else:
                logger.warning(f"主题持久化数据清理部分失败 ({success_count}/{total_operations})")
                return False
                
        except Exception as e:
            logger.error(f"清理主题持久化数据失败: {e}")
            return False
    
    async def detect_current_theme(self, page: Page) -> Optional[str]:
        """
        检测当前Bing页面的主题
        使用多种检测方法确保准确性和可靠性
        
        Args:
            page: Playwright页面对象
            
        Returns:
            当前主题 ("dark", "light", 或 None)
        """
        try:
            logger.debug("开始检测当前Bing主题...")
            
            # 收集所有检测方法的结果
            detection_results = []
            
            # 方法1: 检查CSS类和数据属性
            css_result = await self._detect_theme_by_css_classes(page)
            if css_result:
                detection_results.append(("css_classes", css_result))
                logger.debug(f"CSS类检测结果: {css_result}")
            
            # 方法2: 检查计算样式和背景色
            style_result = await self._detect_theme_by_computed_styles(page)
            if style_result:
                detection_results.append(("computed_styles", style_result))
                logger.debug(f"计算样式检测结果: {style_result}")
            
            # 方法3: 检查Cookie中的主题设置
            cookie_result = await self._detect_theme_by_cookies(page)
            if cookie_result:
                detection_results.append(("cookies", cookie_result))
                logger.debug(f"Cookie检测结果: {cookie_result}")
            
            # 方法4: 检查URL参数
            url_result = await self._detect_theme_by_url_params(page)
            if url_result:
                detection_results.append(("url_params", url_result))
                logger.debug(f"URL参数检测结果: {url_result}")
            
            # 方法5: 检查localStorage和sessionStorage
            storage_result = await self._detect_theme_by_storage(page)
            if storage_result:
                detection_results.append(("storage", storage_result))
                logger.debug(f"存储检测结果: {storage_result}")
            
            # 方法6: 检查meta标签和页面属性
            meta_result = await self._detect_theme_by_meta_tags(page)
            if meta_result:
                detection_results.append(("meta_tags", meta_result))
                logger.debug(f"Meta标签检测结果: {meta_result}")
            
            # 如果没有任何检测结果，返回默认值
            if not detection_results:
                logger.debug("所有检测方法都失败，返回默认浅色主题")
                return "light"
            
            # 使用投票机制决定最终主题
            final_theme = self._vote_for_theme(detection_results)
            logger.info(f"主题检测完成: {final_theme} (基于 {len(detection_results)} 种方法)")
            
            return final_theme
            
        except PlaywrightTimeout:
            logger.warning("检测主题超时")
            return None
        except PlaywrightError as e:
            logger.warning(f"检测主题失败: {e}")
            return None
        except Exception as e:
            logger.warning(f"检测主题时发生意外错误: {e}")
            return None
    
    async def _detect_theme_by_css_classes(self, page: Page) -> Optional[str]:
        """通过CSS类和数据属性检测主题"""
        try:
            # 深色主题指示器
            dark_indicators = [
                "body[class*='dark']",
                "body[data-theme='dark']", 
                "html[class*='dark']",
                "html[data-theme='dark']",
                ".b_dark",  # Bing深色主题类
                "body.dark-theme",
                "html.dark-theme",
                "[data-bs-theme='dark']",  # Bootstrap主题
                ".theme-dark",
                "body[class*='night']",
                "html[class*='night']"
            ]
            
            # 浅色主题指示器
            light_indicators = [
                "body[class*='light']",
                "body[data-theme='light']",
                "html[class*='light']", 
                "html[data-theme='light']",
                ".b_light",  # Bing浅色主题类
                "body.light-theme",
                "html.light-theme",
                "[data-bs-theme='light']",
                ".theme-light"
            ]
            
            # 检查深色主题指示器
            for selector in dark_indicators:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.debug(f"找到深色主题CSS指示器: {selector}")
                        return "dark"
                except (PlaywrightTimeout, PlaywrightError):
                    continue
            
            # 检查浅色主题指示器
            for selector in light_indicators:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.debug(f"找到浅色主题CSS指示器: {selector}")
                        return "light"
                except (PlaywrightTimeout, PlaywrightError):
                    continue
            
            return None
            
        except PlaywrightError as e:
            logger.debug(f"CSS类检测失败: {e}")
            return None
    
    async def _detect_theme_by_computed_styles(self, page: Page) -> Optional[str]:
        """通过计算样式和背景色检测主题"""
        try:
            theme_info = await page.evaluate("""
                () => {
                    try {
                        // 获取根元素和body的计算样式
                        const rootStyle = getComputedStyle(document.documentElement);
                        const bodyStyle = getComputedStyle(document.body);
                        
                        // 检查CSS变量
                        const cssVars = [
                            '--b-theme-bg', '--theme-bg', '--background-color',
                            '--bs-body-bg', '--body-bg', '--main-bg'
                        ];
                        
                        for (const varName of cssVars) {
                            const varValue = rootStyle.getPropertyValue(varName);
                            if (varValue) {
                                const brightness = getBrightnessFromColor(varValue);
                                if (brightness !== null) {
                                    return brightness < 128 ? 'dark' : 'light';
                                }
                            }
                        }
                        
                        // 检查背景色
                        const backgrounds = [
                            rootStyle.backgroundColor,
                            bodyStyle.backgroundColor,
                            rootStyle.getPropertyValue('background'),
                            bodyStyle.getPropertyValue('background')
                        ];
                        
                        for (const bg of backgrounds) {
                            if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                                const brightness = getBrightnessFromColor(bg);
                                if (brightness !== null) {
                                    return brightness < 128 ? 'dark' : 'light';
                                }
                            }
                        }
                        
                        // 检查特定的Bing主题类
                        if (document.body.classList.contains('b_dark') || 
                            document.documentElement.classList.contains('b_dark') ||
                            document.body.classList.contains('dark-theme') ||
                            document.documentElement.classList.contains('dark-theme')) {
                            return 'dark';
                        }
                        
                        if (document.body.classList.contains('b_light') || 
                            document.documentElement.classList.contains('b_light') ||
                            document.body.classList.contains('light-theme') ||
                            document.documentElement.classList.contains('light-theme')) {
                            return 'light';
                        }
                        
                        // 检查页面整体颜色方案
                        const colorScheme = rootStyle.getPropertyValue('color-scheme') || 
                                          bodyStyle.getPropertyValue('color-scheme');
                        if (colorScheme.includes('dark')) return 'dark';
                        if (colorScheme.includes('light')) return 'light';
                        
                        return null;
                        
                    } catch (e) {
                        console.debug('样式检测异常:', e);
                        return null;
                    }
                    
                    // 辅助函数：从颜色值计算亮度
                    function getBrightnessFromColor(color) {
                        try {
                            // 处理rgb/rgba格式
                            let match = color.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
                            if (match) {
                                const [r, g, b] = match.slice(1).map(Number);
                                return (r * 299 + g * 587 + b * 114) / 1000;
                            }
                            
                            // 处理十六进制格式
                            match = color.match(/^#([a-f\\d]{2})([a-f\\d]{2})([a-f\\d]{2})$/i);
                            if (match) {
                                const r = parseInt(match[1], 16);
                                const g = parseInt(match[2], 16);
                                const b = parseInt(match[3], 16);
                                return (r * 299 + g * 587 + b * 114) / 1000;
                            }
                            
                            // 处理命名颜色
                            const namedColors = {
                                'black': 0, 'white': 255, 'gray': 128, 'grey': 128,
                                'darkgray': 64, 'darkgrey': 64, 'lightgray': 192, 'lightgrey': 192
                            };
                            if (namedColors.hasOwnProperty(color.toLowerCase())) {
                                return namedColors[color.toLowerCase()];
                            }
                            
                            return null;
                        } catch (e) {
                            return null;
                        }
                    }
                }
            """)
            
            if theme_info:
                logger.debug(f"通过计算样式检测到主题: {theme_info}")
                return theme_info
            
            return None
            
        except PlaywrightError as e:
            logger.debug(f"计算样式检测失败: {e}")
            return None
    
    async def _detect_theme_by_cookies(self, page: Page) -> Optional[str]:
        """通过Cookie检测主题设置"""
        try:
            cookies = await page.context.cookies()
            
            for cookie in cookies:
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                
                # 检查Bing主题Cookie
                if 'SRCHHPGUSR' in name:
                    # 检查各种主题参数格式
                    theme_patterns = [
                        ('THEME:1', 'dark'), ('THEME=1', 'dark'), ('THEME%3A1', 'dark'),
                        ('THEME:0', 'light'), ('THEME=0', 'light'), ('THEME%3A0', 'light'),
                        ('theme:dark', 'dark'), ('theme=dark', 'dark'),
                        ('theme:light', 'light'), ('theme=light', 'light')
                    ]
                    
                    for pattern, theme in theme_patterns:
                        if pattern in value:
                            logger.debug(f"从Cookie检测到{theme}主题: {pattern}")
                            return theme
                
                # 检查其他可能的主题Cookie
                theme_cookie_names = ['theme', 'color-scheme', 'appearance', 'mode']
                if any(theme_name in name.lower() for theme_name in theme_cookie_names):
                    if any(dark_val in value.lower() for dark_val in ['dark', '1', 'night']):
                        logger.debug(f"从Cookie {name} 检测到深色主题")
                        return "dark"
                    elif any(light_val in value.lower() for light_val in ['light', '0', 'day']):
                        logger.debug(f"从Cookie {name} 检测到浅色主题")
                        return "light"
            
            return None
            
        except PlaywrightError as e:
            logger.debug(f"Cookie检测失败: {e}")
            return None
    
    async def _detect_theme_by_url_params(self, page: Page) -> Optional[str]:
        """通过URL参数检测主题设置"""
        try:
            url = page.url
            
            # 检查URL中的主题参数
            theme_patterns = [
                ('THEME=1', 'dark'), ('THEME%3D1', 'dark'), ('theme=dark', 'dark'),
                ('THEME=0', 'light'), ('THEME%3D0', 'light'), ('theme=light', 'light'),
                ('SRCHHPGUSR=THEME:1', 'dark'), ('SRCHHPGUSR=THEME:0', 'light')
            ]
            
            for pattern, theme in theme_patterns:
                if pattern in url:
                    logger.debug(f"从URL参数检测到{theme}主题: {pattern}")
                    return theme
            
            return None
            
        except PlaywrightError as e:
            logger.debug(f"URL参数检测失败: {e}")
            return None
    
    async def _detect_theme_by_storage(self, page: Page) -> Optional[str]:
        """通过localStorage和sessionStorage检测主题"""
        try:
            storage_result = await page.evaluate("""
                () => {
                    try {
                        // 检查localStorage
                        const localKeys = ['theme', 'color-scheme', 'appearance', 'mode', 'bing-theme'];
                        for (const key of localKeys) {
                            const value = localStorage.getItem(key);
                            if (value) {
                                if (value.toLowerCase().includes('dark')) return 'dark';
                                if (value.toLowerCase().includes('light')) return 'light';
                            }
                        }
                        
                        // 检查sessionStorage
                        const sessionKeys = ['theme', 'color-scheme', 'appearance', 'mode'];
                        for (const key of sessionKeys) {
                            const value = sessionStorage.getItem(key);
                            if (value) {
                                if (value.toLowerCase().includes('dark')) return 'dark';
                                if (value.toLowerCase().includes('light')) return 'light';
                            }
                        }
                        
                        return null;
                    } catch (e) {
                        return null;
                    }
                }
            """)
            
            if storage_result:
                logger.debug(f"从存储检测到主题: {storage_result}")
                return storage_result
            
            return None
            
        except PlaywrightError as e:
            logger.debug(f"存储检测失败: {e}")
            return None
    
    async def _detect_theme_by_meta_tags(self, page: Page) -> Optional[str]:
        """通过meta标签和页面属性检测主题"""
        try:
            meta_result = await page.evaluate("""
                () => {
                    try {
                        // 检查color-scheme meta标签
                        const colorSchemeMeta = document.querySelector('meta[name="color-scheme"]');
                        if (colorSchemeMeta) {
                            const content = colorSchemeMeta.getAttribute('content');
                            if (content && content.includes('dark')) return 'dark';
                            if (content && content.includes('light')) return 'light';
                        }
                        
                        // 检查theme-color meta标签
                        const themeColorMeta = document.querySelector('meta[name="theme-color"]');
                        if (themeColorMeta) {
                            const content = themeColorMeta.getAttribute('content');
                            if (content) {
                                // 简单的颜色亮度检测
                                if (content.toLowerCase() === '#000000' || 
                                    content.toLowerCase() === 'black' ||
                                    content.toLowerCase().includes('dark')) {
                                    return 'dark';
                                }
                                if (content.toLowerCase() === '#ffffff' || 
                                    content.toLowerCase() === 'white' ||
                                    content.toLowerCase().includes('light')) {
                                    return 'light';
                                }
                            }
                        }
                        
                        // 检查其他可能的meta标签
                        const metas = document.querySelectorAll('meta');
                        for (const meta of metas) {
                            const name = meta.getAttribute('name') || meta.getAttribute('property') || '';
                            const content = meta.getAttribute('content') || '';
                            
                            if (name.toLowerCase().includes('theme') || 
                                name.toLowerCase().includes('appearance')) {
                                if (content.toLowerCase().includes('dark')) return 'dark';
                                if (content.toLowerCase().includes('light')) return 'light';
                            }
                        }
                        
                        return null;
                    } catch (e) {
                        return null;
                    }
                }
            """)
            
            if meta_result:
                logger.debug(f"从Meta标签检测到主题: {meta_result}")
                return meta_result
            
            return None
            
        except PlaywrightError as e:
            logger.debug(f"Meta标签检测失败: {e}")
            return None
    
    def _vote_for_theme(self, detection_results: list) -> str:
        """
        基于多种检测方法的结果投票决定最终主题
        
        Args:
            detection_results: 检测结果列表，格式为 [(method_name, theme), ...]
            
        Returns:
            最终确定的主题
        """
        if not detection_results:
            return "light"  # 默认浅色主题
        
        # 统计投票
        votes = {"dark": 0, "light": 0}
        method_weights = {
            "css_classes": 3,      # CSS类权重最高，最可靠
            "computed_styles": 3,  # 计算样式权重也很高
            "cookies": 2,          # Cookie权重中等
            "url_params": 2,       # URL参数权重中等
            "storage": 1,          # 存储权重较低
            "meta_tags": 1         # Meta标签权重较低
        }
        
        total_weight = 0
        for method, theme in detection_results:
            weight = method_weights.get(method, 1)
            votes[theme] += weight
            total_weight += weight
            logger.debug(f"投票: {method} -> {theme} (权重: {weight})")
        
        # 决定最终主题
        if votes["dark"] > votes["light"]:
            confidence = votes["dark"] / total_weight * 100
            logger.debug(f"投票结果: 深色主题 (置信度: {confidence:.1f}%)")
            return "dark"
        elif votes["light"] > votes["dark"]:
            confidence = votes["light"] / total_weight * 100
            logger.debug(f"投票结果: 浅色主题 (置信度: {confidence:.1f}%)")
            return "light"
        else:
            # 平票时默认浅色主题
            logger.debug("投票平票，默认选择浅色主题")
            return "light"
    
    async def set_theme(self, page: Page, theme: str = "dark") -> bool:
        """
        设置Bing页面主题
        使用多种方法确保主题设置的可靠性，包含完善的失败处理
        
        Args:
            page: Playwright页面对象
            theme: 目标主题 ("dark" 或 "light")
            
        Returns:
            是否设置成功
        """
        if not self.enabled:
            logger.debug("主题管理已禁用")
            return True
        
        failure_details = []  # 记录失败详情
        
        try:
            logger.info(f"设置Bing主题为: {theme}")
            
            # 检查当前主题
            current_theme = await self.detect_current_theme(page)
            if current_theme == theme:
                logger.debug(f"主题已经是 {theme}，无需更改")
                return True
            
            # 定义设置方法列表，按优先级排序
            setting_methods = [
                ("URL参数", self._set_theme_by_url),
                ("Cookie", self._set_theme_by_cookie),
                ("LocalStorage", self._set_theme_by_localstorage),
                ("JavaScript注入", self._set_theme_by_javascript),
                ("设置页面", self._set_theme_by_settings),
                ("强制CSS", self._set_theme_by_force_css)
            ]
            
            # 尝试每种方法
            for method_name, method_func in setting_methods:
                try:
                    logger.debug(f"尝试通过{method_name}设置主题...")
                    success = await method_func(page, theme)
                    if success:
                        logger.info(f"✓ 通过{method_name}成功设置主题为: {theme}")
                        
                        # 验证设置是否生效
                        await asyncio.sleep(1)  # 等待主题应用
                        new_theme = await self.detect_current_theme(page)
                        if new_theme == theme:
                            logger.debug(f"主题设置验证成功: {new_theme}")
                            return True
                        else:
                            failure_msg = f"主题设置验证失败: 期望{theme}, 实际{new_theme}"
                            logger.warning(failure_msg)
                            failure_details.append(f"{method_name}: {failure_msg}")
                            continue
                    else:
                        failure_details.append(f"{method_name}: 方法返回失败")
                    
                except Exception as e:
                    failure_msg = f"{method_name}设置异常: {str(e)}"
                    logger.debug(failure_msg)
                    failure_details.append(failure_msg)
                    continue
            
            # 所有方法都失败，记录详细失败信息
            await self._handle_theme_setting_failure(page, theme, failure_details)
            return False
            
        except Exception as e:
            error_msg = f"设置主题过程异常: {str(e)}"
            logger.error(error_msg)
            failure_details.append(error_msg)
            await self._handle_theme_setting_failure(page, theme, failure_details)
            return False
    
    async def _set_theme_by_url(self, page: Page, theme: str) -> bool:
        """通过URL参数设置主题"""
        try:
            logger.debug("尝试通过URL参数设置主题...")
            
            current_url = page.url
            
            # 构建主题参数
            theme_param = "1" if theme == "dark" else "0"
            
            # 多种URL参数格式
            url_variations = []
            
            # 方法1: SRCHHPGUSR参数
            if "SRCHHPGUSR" in current_url:
                # 更新现有参数
                import re
                new_url = re.sub(r'THEME[:=]\d', f'THEME={theme_param}', current_url)
                if new_url != current_url:
                    url_variations.append(new_url)
                
                # 尝试冒号格式
                new_url2 = re.sub(r'THEME[:=]\d', f'THEME:{theme_param}', current_url)
                if new_url2 != current_url and new_url2 != new_url:
                    url_variations.append(new_url2)
            else:
                # 添加新参数
                separator = "&" if "?" in current_url else "?"
                url_variations.extend([
                    f"{current_url}{separator}SRCHHPGUSR=THEME={theme_param}",
                    f"{current_url}{separator}SRCHHPGUSR=THEME:{theme_param}",
                    f"{current_url}{separator}THEME={theme_param}",
                    f"{current_url}{separator}theme={theme}",
                    f"{current_url}{separator}color-scheme={theme}"
                ])
            
            # 尝试每种URL变体
            for url_variant in url_variations:
                try:
                    logger.debug(f"尝试URL: {url_variant}")
                    await page.goto(url_variant, wait_until="domcontentloaded", timeout=10000)
                    await asyncio.sleep(1)
                    
                    # 快速验证是否生效
                    quick_check = await self._quick_theme_check(page, theme)
                    if quick_check:
                        logger.debug("✓ URL参数设置主题成功")
                        return True
                        
                except (PlaywrightTimeout, PlaywrightError) as e:
                    logger.debug(f"URL变体失败: {e}")
                    continue
            
            return False
            
        except PlaywrightError as e:
            logger.debug(f"URL参数设置主题失败: {e}")
            return False
    
    async def _set_theme_by_cookie(self, page: Page, theme: str) -> bool:
        """通过Cookie设置主题"""
        try:
            logger.debug("尝试通过Cookie设置主题...")
            
            theme_value = "1" if theme == "dark" else "0"
            
            # 多种Cookie设置方式
            cookie_variations = [
                # Bing标准格式
                {'name': 'SRCHHPGUSR', 'value': f'THEME={theme_value}'},
                {'name': 'SRCHHPGUSR', 'value': f'THEME:{theme_value}'},
                {'name': 'SRCHHPGUSR', 'value': f'THEME%3D{theme_value}'},
                {'name': 'SRCHHPGUSR', 'value': f'THEME%3A{theme_value}'},
                
                # 通用主题Cookie
                {'name': 'theme', 'value': theme},
                {'name': 'color-scheme', 'value': theme},
                {'name': 'appearance', 'value': theme},
                {'name': 'mode', 'value': theme},
                {'name': 'bing-theme', 'value': theme},
                
                # 数值格式
                {'name': 'theme-mode', 'value': theme_value},
                {'name': 'dark-mode', 'value': theme_value},
            ]
            
            # 设置所有Cookie变体
            for cookie_data in cookie_variations:
                try:
                    cookie_full = {
                        'name': cookie_data['name'],
                        'value': cookie_data['value'],
                        'domain': '.bing.com',
                        'path': '/',
                        'httpOnly': False,
                        'secure': True,
                        'sameSite': 'Lax'
                    }
                    
                    await page.context.add_cookies([cookie_full])
                    
                except (PlaywrightTimeout, PlaywrightError) as e:
                    logger.debug(f"设置Cookie {cookie_data['name']} 失败: {e}")
                    continue
            
            # 刷新页面使Cookie生效
            await page.reload(wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(1)
            
            # 验证Cookie是否生效
            quick_check = await self._quick_theme_check(page, theme)
            if quick_check:
                logger.debug("✓ Cookie设置主题成功")
                return True
            
            return False
            
        except PlaywrightTimeout:
            logger.debug("Cookie设置主题超时")
            return False
        except PlaywrightError as e:
            logger.debug(f"Cookie设置主题失败: {e}")
            return False
    
    async def _quick_theme_check(self, page: Page, expected_theme: str) -> bool:
        """快速检查主题是否设置成功"""
        try:
            # 使用最可靠的检测方法进行快速验证
            css_result = await self._detect_theme_by_css_classes(page)
            if css_result == expected_theme:
                return True
            
            style_result = await self._detect_theme_by_computed_styles(page)
            if style_result == expected_theme:
                return True
            
            cookie_result = await self._detect_theme_by_cookies(page)
            if cookie_result == expected_theme:
                return True
            
            return False
            
        except (PlaywrightTimeout, PlaywrightError):
            return False
    
    async def _set_theme_by_localstorage(self, page: Page, theme: str) -> bool:
        """通过localStorage设置主题"""
        try:
            logger.debug("尝试通过localStorage设置主题...")
            
            # 设置localStorage中的主题值
            theme_value = "1" if theme == "dark" else "0"
            
            await page.evaluate(f"""
                () => {{
                    try {{
                        // 设置多种可能的localStorage键
                        const themeKeys = [
                            'bing-theme',
                            'theme',
                            'color-scheme', 
                            'appearance',
                            'SRCHHPGUSR'
                        ];
                        
                        const themeValue = '{theme}';
                        const themeNum = '{theme_value}';
                        
                        // 设置各种格式的主题值
                        for (const key of themeKeys) {{
                            localStorage.setItem(key, themeValue);
                            localStorage.setItem(key + '-mode', themeValue);
                            localStorage.setItem(key + '-setting', themeNum);
                        }}
                        
                        // 设置Bing特定的主题参数
                        localStorage.setItem('SRCHHPGUSR', `THEME=${{themeNum}}`);
                        localStorage.setItem('bing-theme-preference', themeValue);
                        
                        // 触发存储事件
                        window.dispatchEvent(new StorageEvent('storage', {{
                            key: 'theme',
                            newValue: themeValue,
                            storageArea: localStorage
                        }}));
                        
                        return true;
                    }} catch (e) {{
                        console.debug('localStorage设置失败:', e);
                        return false;
                    }}
                }}
            """)
            
            # 刷新页面使设置生效
            await page.reload(wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(1)
            
            logger.debug("✓ localStorage设置主题完成")
            return True
            
        except PlaywrightTimeout:
            logger.debug("localStorage设置主题超时")
            return False
        except PlaywrightError as e:
            logger.debug(f"localStorage设置主题失败: {e}")
            return False
    
    async def _set_theme_by_javascript(self, page: Page, theme: str) -> bool:
        """通过JavaScript直接设置主题"""
        try:
            logger.debug("尝试通过JavaScript注入设置主题...")
            
            theme_value = "1" if theme == "dark" else "0"
            
            result = await page.evaluate(f"""
                () => {{
                    try {{
                        const theme = '{theme}';
                        const themeNum = '{theme_value}';
                        
                        // 方法1: 直接设置CSS类
                        document.documentElement.className = 
                            document.documentElement.className.replace(/\\b(light|dark)(-theme)?\\b/g, '');
                        document.body.className = 
                            document.body.className.replace(/\\b(light|dark)(-theme)?\\b/g, '');
                        
                        document.documentElement.classList.add(theme + '-theme');
                        document.body.classList.add(theme + '-theme');
                        
                        // 方法2: 设置data属性
                        document.documentElement.setAttribute('data-theme', theme);
                        document.body.setAttribute('data-theme', theme);
                        document.documentElement.setAttribute('data-bs-theme', theme);
                        
                        // 方法3: 设置CSS变量
                        const root = document.documentElement;
                        if (theme === 'dark') {{
                            root.style.setProperty('--bs-body-bg', '#212529');
                            root.style.setProperty('--bs-body-color', '#ffffff');
                            root.style.setProperty('--background-color', '#212529');
                            root.style.setProperty('--text-color', '#ffffff');
                        }} else {{
                            root.style.setProperty('--bs-body-bg', '#ffffff');
                            root.style.setProperty('--bs-body-color', '#212529');
                            root.style.setProperty('--background-color', '#ffffff');
                            root.style.setProperty('--text-color', '#212529');
                        }}
                        
                        // 方法4: 设置color-scheme
                        root.style.setProperty('color-scheme', theme);
                        document.body.style.setProperty('color-scheme', theme);
                        
                        // 方法5: 触发主题变更事件
                        const themeChangeEvent = new CustomEvent('themechange', {{
                            detail: {{ theme: theme, value: themeNum }}
                        }});
                        document.dispatchEvent(themeChangeEvent);
                        
                        // 方法6: 尝试调用Bing的主题设置函数（如果存在）
                        if (typeof window.setTheme === 'function') {{
                            window.setTheme(theme);
                        }}
                        if (typeof window.changeTheme === 'function') {{
                            window.changeTheme(theme);
                        }}
                        if (typeof window.updateTheme === 'function') {{
                            window.updateTheme(theme);
                        }}
                        
                        return true;
                    }} catch (e) {{
                        console.debug('JavaScript主题设置失败:', e);
                        return false;
                    }}
                }}
            """)
            
            if result:
                logger.debug("✓ JavaScript注入设置主题完成")
                return True
            
            return False
            
        except PlaywrightTimeout:
            logger.debug("JavaScript注入设置主题超时")
            return False
        except PlaywrightError as e:
            logger.debug(f"JavaScript注入设置主题失败: {e}")
            return False
    
    async def _set_theme_by_force_css(self, page: Page, theme: str) -> bool:
        """通过强制CSS样式设置主题"""
        try:
            logger.debug("尝试通过强制CSS设置主题...")
            
            # 注入强制主题CSS
            css_content = self._generate_force_theme_css(theme)
            
            await page.add_style_tag(content=css_content)
            
            # 同时设置页面属性
            await page.evaluate(f"""
                () => {{
                    const theme = '{theme}';
                    
                    // 设置根元素属性
                    document.documentElement.setAttribute('data-forced-theme', theme);
                    document.body.setAttribute('data-forced-theme', theme);
                    
                    // 添加强制主题类
                    document.documentElement.classList.add('forced-' + theme + '-theme');
                    document.body.classList.add('forced-' + theme + '-theme');
                }}
            """)
            
            logger.debug("✓ 强制CSS设置主题完成")
            return True
            
        except PlaywrightTimeout:
            logger.debug("强制CSS设置主题超时")
            return False
        except PlaywrightError as e:
            logger.debug(f"强制CSS设置主题失败: {e}")
            return False
    
    def _generate_force_theme_css(self, theme: str) -> str:
        """生成强制主题CSS样式 - 保留灰度层次，避免纯黑"""
        if theme == "dark":
            return """
            /* 深色主题样式 - 保留灰度层次 */
            html[data-forced-theme="dark"], 
            body[data-forced-theme="dark"],
            html.forced-dark-theme,
            body.forced-dark-theme {
                background-color: #1a1a2e !important;
                color: #e0e0e0 !important;
                color-scheme: dark !important;
            }
            
            /* Bing头部 - 使用中等深度的灰色 */
            .b_header {
                background-color: #16213e !important;
                border-bottom: 1px solid #2a2a4a !important;
            }
            
            /* 搜索框 - 使用较深的灰色 */
            .b_searchbox, .b_searchboxForm, #sb_form_q {
                background-color: #0f3460 !important;
                border: 1px solid #1a1a4a !important;
                color: #e0e0e0 !important;
            }
            
            /* 搜索结果卡片 - 使用不同深度的灰色 */
            .b_algo {
                background-color: #1a1a2e !important;
                border-bottom: 1px solid #2a2a4a !important;
                padding: 12px 0 !important;
            }
            
            .b_algo h2 {
                color: #4da6ff !important;
            }
            
            .b_algo p, .b_algo span {
                color: #b0b0b0 !important;
            }
            
            /* 侧边栏 */
            .b_ans, .b_rs {
                background-color: #16213e !important;
                border-radius: 8px !important;
                padding: 16px !important;
            }
            
            /* 页脚 */
            .b_footer {
                background-color: #0d0d1a !important;
                border-top: 1px solid #2a2a4a !important;
            }
            
            /* 输入框 */
            input[type="text"], input[type="search"], textarea {
                background-color: #1a1a3e !important;
                color: #e0e0e0 !important;
                border: 1px solid #2a2a5a !important;
            }
            
            /* 链接 */
            a, a:visited {
                color: #4da6ff !important;
            }
            
            a:hover {
                color: #80c4ff !important;
            }
            
            /* 强调文字 */
            strong, b {
                color: #ffffff !important;
            }
            """
        else:
            return """
            /* 浅色主题样式 - 保留灰度层次 */
            html[data-forced-theme="light"], 
            body[data-forced-theme="light"],
            html.forced-light-theme,
            body.forced-light-theme {
                background-color: #f5f5f5 !important;
                color: #333333 !important;
                color-scheme: light !important;
            }
            
            /* Bing头部 */
            .b_header {
                background-color: #ffffff !important;
                border-bottom: 1px solid #e0e0e0 !important;
            }
            
            /* 搜索框 */
            .b_searchbox, .b_searchboxForm, #sb_form_q {
                background-color: #ffffff !important;
                border: 1px solid #d0d0d0 !important;
                color: #333333 !important;
            }
            
            /* 搜索结果卡片 */
            .b_algo {
                background-color: #ffffff !important;
                border-bottom: 1px solid #e8e8e8 !important;
                padding: 12px 0 !important;
            }
            
            .b_algo h2 {
                color: #0066cc !important;
            }
            
            .b_algo p, .b_algo span {
                color: #555555 !important;
            }
            
            /* 侧边栏 */
            .b_ans, .b_rs {
                background-color: #fafafa !important;
                border: 1px solid #e0e0e0 !important;
                border-radius: 8px !important;
                padding: 16px !important;
            }
            
            /* 页脚 */
            .b_footer {
                background-color: #f0f0f0 !important;
                border-top: 1px solid #e0e0e0 !important;
            }
            
            /* 输入框 */
            input[type="text"], input[type="search"], textarea {
                background-color: #ffffff !important;
                color: #333333 !important;
                border: 1px solid #c0c0c0 !important;
            }
            
            /* 链接 */
            a, a:visited {
                color: #0066cc !important;
            }
            
            a:hover {
                color: #004499 !important;
            }
            
            /* 强调文字 */
            strong, b {
                color: #000000 !important;
            }
            """
    
    async def _set_theme_by_settings(self, page: Page, theme: str) -> bool:
        """通过设置页面设置主题"""
        try:
            logger.debug("尝试通过设置页面设置主题...")
            
            # 扩展的设置按钮选择器
            settings_selectors = [
                "button[aria-label*='Settings']",
                "button[title*='Settings']", 
                "a[href*='preferences']",
                "#id_sc",  # Bing设置按钮ID
                ".b_idOpen",  # Bing设置菜单
                "button[data-testid*='settings']",
                ".settings-button",
                "[role='button'][aria-label*='设置']",
                "button:has-text('Settings')",
                "button:has-text('设置')",
                ".header-settings",
                "#settings-menu"
            ]
            
            # 查找设置按钮
            settings_button = None
            for selector in settings_selectors:
                try:
                    settings_button = await page.wait_for_selector(selector, timeout=2000)
                    if settings_button and await settings_button.is_visible():
                        logger.debug(f"找到设置按钮: {selector}")
                        break
                except (PlaywrightTimeout, PlaywrightError):
                    continue
            
            if not settings_button:
                logger.debug("未找到设置按钮")
                return False
            
            # 点击设置按钮
            await settings_button.click()
            await asyncio.sleep(1)
            
            # 扩展的主题选项选择器
            theme_value = "1" if theme == "dark" else "0"
            theme_selectors = [
                f"input[value='{theme}']",
                f"input[name='SRCHHPGUSR'][value*='THEME:{theme_value}']",
                f"label:has-text('{theme.title()}')",
                f"div[data-value='{theme}']",
                f"button[data-theme='{theme}']",
                f".theme-option[data-theme='{theme}']",
                f"input[type='radio'][value='{theme}']",
                f"select option[value='{theme}']",
                "input[name*='theme']",
                "select[name*='theme']",
                ".dark-mode-toggle" if theme == "dark" else ".light-mode-toggle",
                "[data-testid*='theme']",
                ".theme-selector"
            ]
            
            # 查找主题选项
            theme_option = None
            for selector in theme_selectors:
                try:
                    theme_option = await page.wait_for_selector(selector, timeout=2000)
                    if theme_option:
                        logger.debug(f"找到主题选项: {selector}")
                        break
                except (PlaywrightTimeout, PlaywrightError):
                    continue
            
            if not theme_option:
                logger.debug("未找到主题选项")
                try:
                    theme_text = "Dark" if theme == "dark" else "Light"
                    theme_option = await page.get_by_text(theme_text).first
                    if theme_option:
                        logger.debug(f"通过文本找到主题选项: {theme_text}")
                except (PlaywrightTimeout, PlaywrightError):
                    return False
            
            if not theme_option:
                return False
            
            # 选择主题
            element_type = await theme_option.evaluate("el => el.tagName.toLowerCase()")
            
            if element_type == "input":
                input_type = await theme_option.get_attribute("type")
                if input_type in ["radio", "checkbox"]:
                    await theme_option.check()
                else:
                    await theme_option.click()
            elif element_type == "select":
                await theme_option.select_option(value=theme)
            else:
                await theme_option.click()
            
            await asyncio.sleep(0.5)
            
            # 扩展的保存按钮选择器
            save_selectors = [
                "input[type='submit'][value*='Save']",
                "button:has-text('Save')",
                "input[value='保存']",
                "button:has-text('保存')",
                "button[type='submit']",
                ".save-button",
                ".apply-button",
                "button:has-text('Apply')",
                "button:has-text('应用')",
                "[data-testid*='save']",
                "[data-testid*='apply']",
                ".btn-primary",
                ".submit-btn"
            ]
            
            # 查找保存按钮
            save_button = None
            for selector in save_selectors:
                try:
                    save_button = await page.wait_for_selector(selector, timeout=2000)
                    if save_button and await save_button.is_visible():
                        logger.debug(f"找到保存按钮: {selector}")
                        break
                except (PlaywrightTimeout, PlaywrightError):
                    continue
            
            if save_button:
                await save_button.click()
                await asyncio.sleep(1)
                logger.debug("点击了保存按钮")
            else:
                logger.debug("未找到保存按钮，可能自动保存")
            
            # 验证主题是否生效
            quick_check = await self._quick_theme_check(page, theme)
            if quick_check:
                logger.debug("✓ 设置页面设置主题成功")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"设置页面设置主题失败: {e}")
            return False
    
    async def set_theme_with_retry(self, page: Page, theme: str = "dark", max_retries: int = 3) -> bool:
        """
        带重试机制的主题设置
        
        Args:
            page: Playwright页面对象
            theme: 目标主题 ("dark" 或 "light")
            max_retries: 最大重试次数
            
        Returns:
            是否设置成功
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"主题设置尝试 {attempt + 1}/{max_retries}")
                
                success = await self.set_theme(page, theme)
                if success:
                    logger.info(f"✓ 第{attempt + 1}次尝试成功设置主题为: {theme}")
                    return True
                
                if attempt < max_retries - 1:
                    logger.debug(f"第{attempt + 1}次尝试失败，等待后重试...")
                    await asyncio.sleep(2)  # 等待2秒后重试
                
            except Exception as e:
                logger.debug(f"第{attempt + 1}次尝试异常: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
        
        logger.warning(f"经过{max_retries}次尝试仍无法设置主题")
        return False
    
    async def force_theme_application(self, page: Page, theme: str = "dark") -> bool:
        """
        强制应用主题（使用所有可用方法）
        
        Args:
            page: Playwright页面对象
            theme: 目标主题 ("dark" 或 "light")
            
        Returns:
            是否至少有一种方法成功
        """
        try:
            logger.info(f"强制应用主题: {theme}")
            
            success_count = 0
            methods = [
                ("URL参数", self._set_theme_by_url),
                ("Cookie", self._set_theme_by_cookie),
                ("LocalStorage", self._set_theme_by_localstorage),
                ("JavaScript注入", self._set_theme_by_javascript),
                ("强制CSS", self._set_theme_by_force_css)
            ]
            
            # 并行执行所有方法（除了需要页面刷新的）
            for method_name, method_func in methods:
                try:
                    if method_name in ["URL参数", "Cookie"]:
                        # 这些方法需要页面刷新，单独执行
                        continue
                    
                    success = await method_func(page, theme)
                    if success:
                        success_count += 1
                        logger.debug(f"✓ {method_name}强制应用成功")
                    
                except Exception as e:
                    logger.debug(f"{method_name}强制应用失败: {e}")
            
            # 最后尝试需要刷新的方法
            for method_name, method_func in methods:
                if method_name not in ["URL参数", "Cookie"]:
                    continue
                
                try:
                    success = await method_func(page, theme)
                    if success:
                        success_count += 1
                        logger.debug(f"✓ {method_name}强制应用成功")
                        break  # 只需要一个刷新方法成功即可
                except Exception as e:
                    logger.debug(f"{method_name}强制应用失败: {e}")
            
            if success_count > 0:
                logger.info(f"✓ 强制主题应用完成，{success_count}种方法成功")
                return True
            else:
                logger.warning("所有强制主题应用方法都失败")
                return False
                
        except Exception as e:
            logger.error(f"强制主题应用异常: {e}")
            return False
    
    async def get_theme_status_report(self, page: Page) -> Dict[str, Any]:
        """
        获取详细的主题状态报告
        
        Args:
            page: Playwright页面对象
            
        Returns:
            主题状态报告字典
        """
        try:
            logger.debug("生成主题状态报告...")
            
            # 收集所有检测方法的结果
            detection_results = {}
            
            methods = [
                ("CSS类", self._detect_theme_by_css_classes),
                ("计算样式", self._detect_theme_by_computed_styles),
                ("Cookie", self._detect_theme_by_cookies),
                ("URL参数", self._detect_theme_by_url_params),
                ("存储", self._detect_theme_by_storage),
                ("Meta标签", self._detect_theme_by_meta_tags)
            ]
            
            for method_name, method_func in methods:
                try:
                    result = await method_func(page)
                    detection_results[method_name] = result
                except Exception as e:
                    detection_results[method_name] = f"错误: {str(e)}"
            
            # 获取最终主题
            final_theme = await self.detect_current_theme(page)
            
            # 获取页面信息
            page_info = {
                "url": page.url,
                "title": await page.title() if page else "未知",
                "user_agent": await page.evaluate("navigator.userAgent") if page else "未知"
            }
            
            # 获取配置信息
            config_info = self.get_theme_config()
            
            report = {
                "timestamp": asyncio.get_running_loop().time(),
                "final_theme": final_theme,
                "detection_results": detection_results,
                "page_info": page_info,
                "config": config_info,
                "status": "成功" if final_theme else "失败"
            }
            
            logger.debug(f"主题状态报告生成完成: {final_theme}")
            return report
            
        except Exception as e:
            logger.error(f"生成主题状态报告失败: {e}")
            return {
                "timestamp": asyncio.get_running_loop().time(),
                "final_theme": None,
                "detection_results": {},
                "page_info": {},
                "config": self.get_theme_config(),
                "status": f"错误: {str(e)}"
            }
    
    async def ensure_theme_before_search(self, page: Page, context: Optional[BrowserContext] = None) -> bool:
        """
        在搜索前确保主题设置正确，包含完善的失败处理和会话间持久化
        这是任务6.2.2的集成功能：在搜索前确保主题持久化
        
        Args:
            page: Playwright页面对象
            context: 浏览器上下文（可选）
            
        Returns:
            是否成功（失败不会阻止搜索继续）
        """
        if not self.enabled or not self.force_theme:
            return True
        
        try:
            logger.debug("搜索前检查主题设置和持久化...")
            
            # 1. 首先检测当前主题
            current_theme = await self.detect_current_theme(page)
            logger.debug(f"当前检测到的主题: {current_theme}, 期望主题: {self.preferred_theme}")
            
            # 2. 如果主题已经正确，直接返回（避免不必要的操作）
            if current_theme == self.preferred_theme:
                logger.debug(f"主题已正确设置为: {current_theme}")
                # 确保持久化状态是最新的（只在主题正确时保存）
                if self.persistence_enabled:
                    await self.ensure_theme_persistence(page, context)
                return True
            
            # 3. 主题不匹配，需要设置
            logger.info(f"主题不匹配 (当前: {current_theme}, 期望: {self.preferred_theme})，尝试设置")
            
            # 首先尝试标准设置
            success = await self.set_theme(page, self.preferred_theme)
            if success:
                logger.debug("搜索前主题设置成功")
                # 验证设置是否真的生效
                await asyncio.sleep(0.5)
                verified_theme = await self.detect_current_theme(page)
                if verified_theme == self.preferred_theme:
                    logger.debug(f"主题设置验证成功: {verified_theme}")
                    # 保存正确的主题状态
                    if self.persistence_enabled:
                        await self.ensure_theme_persistence(page, context)
                    return True
                else:
                    logger.warning(f"主题设置验证失败: 期望{self.preferred_theme}, 实际{verified_theme}")
            
            # 如果标准设置失败，尝试降级策略
            logger.debug("标准主题设置失败，尝试降级策略...")
            fallback_success = await self.set_theme_with_fallback(page, self.preferred_theme)
            if fallback_success:
                logger.debug("搜索前主题降级设置成功")
                # 验证降级设置
                await asyncio.sleep(0.5)
                verified_theme = await self.detect_current_theme(page)
                if verified_theme == self.preferred_theme:
                    logger.debug(f"降级主题设置验证成功: {verified_theme}")
                    # 保存正确的主题状态
                    if self.persistence_enabled:
                        await self.ensure_theme_persistence(page, context)
                    return True
            
            # 所有方法都失败，记录警告但不阻止搜索
            logger.warning(f"搜索前主题设置完全失败，将继续搜索 (当前主题: {current_theme})")
            return True  # 不阻止搜索继续
            
        except Exception as e:
            logger.warning(f"搜索前主题检查异常: {e}，将继续搜索")
            return True  # 异常不应该阻止搜索继续
    
    def get_theme_config(self) -> Dict[str, Any]:
        """
        获取主题配置信息
        
        Returns:
            主题配置字典
        """
        return {
            "enabled": self.enabled,
            "preferred_theme": self.preferred_theme,
            "force_theme": self.force_theme,
        }
    
    async def get_failure_statistics(self) -> Dict[str, Any]:
        """
        获取主题设置失败统计信息
        
        Returns:
            失败统计字典
        """
        try:
            # 这里可以扩展为从日志文件或数据库中读取统计信息
            # 目前返回基本的配置和状态信息
            
            stats = {
                "config": self.get_theme_config(),
                "last_check_time": asyncio.get_running_loop().time(),
                "available_methods": [
                    "URL参数",
                    "Cookie", 
                    "LocalStorage",
                    "JavaScript注入",
                    "设置页面",
                    "强制CSS"
                ],
                "fallback_strategies": [
                    "强制应用所有方法",
                    "仅应用CSS样式",
                    "设置最小化主题标记"
                ]
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取失败统计信息异常: {e}")
            return {
                "error": str(e),
                "config": self.get_theme_config()
            }
    
    async def verify_theme_persistence(self, page: Page) -> bool:
        """
        验证主题设置是否持久化
        
        Args:
            page: Playwright页面对象
            
        Returns:
            主题是否持久化
        """
        try:
            logger.debug("验证主题持久化...")
            
            # 记录当前主题
            original_theme = await self.detect_current_theme(page)
            
            # 刷新页面
            await page.reload(wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(1)
            
            # 检查主题是否保持
            new_theme = await self.detect_current_theme(page)
            
            is_persistent = (original_theme == new_theme)
            
            if is_persistent:
                logger.debug(f"✓ 主题持久化验证成功: {new_theme}")
            else:
                logger.warning(f"主题持久化失败: {original_theme} -> {new_theme}")
            
            return is_persistent
            
        except Exception as e:
            logger.warning(f"主题持久化验证失败: {e}")
            return False
    
    async def verify_theme_setting(self, page: Page, expected_theme: str = "dark") -> Dict[str, Any]:
        """
        验证主题设置是否成功应用
        这是任务6.2.1的核心实现：提供全面的主题设置验证功能
        
        Args:
            page: Playwright页面对象
            expected_theme: 期望的主题 ("dark" 或 "light")
            
        Returns:
            验证结果字典，包含详细的验证信息
        """
        verification_result = {
            "success": False,
            "expected_theme": expected_theme,
            "detected_theme": None,
            "verification_methods": {},
            "persistence_check": False,
            "verification_score": 0.0,
            "recommendations": [],
            "timestamp": asyncio.get_running_loop().time(),
            "error": None
        }
        
        try:
            logger.info(f"开始验证主题设置: {expected_theme}")
            
            # 1. 基础主题检测验证
            detected_theme = await self.detect_current_theme(page)
            verification_result["detected_theme"] = detected_theme
            
            if not detected_theme:
                verification_result["error"] = "无法检测当前主题"
                verification_result["recommendations"].append("页面可能未完全加载或不支持主题检测")
                return verification_result
            
            # 2. 详细验证各种检测方法
            verification_methods = await self._verify_theme_by_all_methods(page, expected_theme)
            verification_result["verification_methods"] = verification_methods
            
            # 3. 计算验证分数
            verification_score = self._calculate_verification_score(verification_methods, detected_theme, expected_theme)
            verification_result["verification_score"] = verification_score
            
            # 4. 主题持久化验证
            if detected_theme == expected_theme:
                logger.debug("主题匹配，进行持久化验证...")
                persistence_result = await self._verify_theme_persistence_detailed(page, expected_theme)
                verification_result["persistence_check"] = persistence_result["is_persistent"]
                verification_result["persistence_details"] = persistence_result
            else:
                logger.debug(f"主题不匹配 (期望: {expected_theme}, 实际: {detected_theme})，跳过持久化验证")
                verification_result["persistence_check"] = False
            
            # 5. 确定最终验证结果
            verification_result["success"] = (
                detected_theme == expected_theme and 
                verification_score >= 0.7 and  # 至少70%的方法验证成功
                (verification_result["persistence_check"] or detected_theme != expected_theme)
            )
            
            # 6. 生成建议
            recommendations = self._generate_verification_recommendations(
                verification_result, verification_methods, detected_theme, expected_theme
            )
            verification_result["recommendations"] = recommendations
            
            # 7. 记录验证结果
            if verification_result["success"]:
                logger.info(f"✓ 主题设置验证成功: {expected_theme} (分数: {verification_score:.2f})")
            else:
                logger.warning(f"主题设置验证失败: 期望 {expected_theme}, 检测到 {detected_theme} (分数: {verification_score:.2f})")
            
            return verification_result
            
        except Exception as e:
            error_msg = f"主题设置验证异常: {str(e)}"
            logger.error(error_msg)
            verification_result["error"] = error_msg
            verification_result["recommendations"].append("验证过程中发生异常，建议检查页面状态和网络连接")
            return verification_result
    
    async def _verify_theme_by_all_methods(self, page: Page, expected_theme: str) -> Dict[str, Any]:
        """
        使用所有检测方法验证主题设置
        
        Args:
            page: Playwright页面对象
            expected_theme: 期望的主题
            
        Returns:
            各种方法的验证结果
        """
        methods_result = {}
        
        # 定义所有检测方法
        detection_methods = [
            ("css_classes", self._detect_theme_by_css_classes, 3),
            ("computed_styles", self._detect_theme_by_computed_styles, 3),
            ("cookies", self._detect_theme_by_cookies, 2),
            ("url_params", self._detect_theme_by_url_params, 2),
            ("storage", self._detect_theme_by_storage, 1),
            ("meta_tags", self._detect_theme_by_meta_tags, 1)
        ]
        
        for method_name, method_func, weight in detection_methods:
            try:
                result = await method_func(page)
                methods_result[method_name] = {
                    "result": result,
                    "matches_expected": result == expected_theme,
                    "weight": weight,
                    "status": "success",
                    "error": None
                }
                logger.debug(f"验证方法 {method_name}: {result} (期望: {expected_theme})")
                
            except Exception as e:
                methods_result[method_name] = {
                    "result": None,
                    "matches_expected": False,
                    "weight": weight,
                    "status": "error",
                    "error": str(e)
                }
                logger.debug(f"验证方法 {method_name} 失败: {e}")
        
        return methods_result
    
    def _calculate_verification_score(self, methods_result: Dict[str, Any], detected_theme: str, expected_theme: str) -> float:
        """
        计算主题验证分数
        
        Args:
            methods_result: 各种方法的验证结果
            detected_theme: 检测到的主题
            expected_theme: 期望的主题
            
        Returns:
            验证分数 (0.0 - 1.0)
        """
        if not methods_result:
            return 0.0
        
        total_weight = 0
        matched_weight = 0
        
        for method_name, result in methods_result.items():
            weight = result.get("weight", 1)
            total_weight += weight
            
            if result.get("matches_expected", False):
                matched_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        # 基础分数基于权重匹配
        base_score = matched_weight / total_weight
        
        # 如果最终检测结果匹配，给予额外加分
        if detected_theme == expected_theme:
            base_score = min(1.0, base_score + 0.2)
        
        return base_score
    
    async def _verify_theme_persistence_detailed(self, page: Page, expected_theme: str) -> Dict[str, Any]:
        """
        详细的主题持久化验证
        
        Args:
            page: Playwright页面对象
            expected_theme: 期望的主题
            
        Returns:
            详细的持久化验证结果
        """
        persistence_result = {
            "is_persistent": False,
            "before_refresh": None,
            "after_refresh": None,
            "refresh_successful": False,
            "verification_methods_before": {},
            "verification_methods_after": {},
            "error": None
        }
        
        try:
            logger.debug("开始详细持久化验证...")
            
            # 1. 记录刷新前的状态
            before_theme = await self.detect_current_theme(page)
            before_methods = await self._verify_theme_by_all_methods(page, expected_theme)
            
            persistence_result["before_refresh"] = before_theme
            persistence_result["verification_methods_before"] = before_methods
            
            # 2. 刷新页面
            try:
                await page.reload(wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2)  # 等待主题应用
                persistence_result["refresh_successful"] = True
                logger.debug("页面刷新成功")
            except (PlaywrightTimeout, PlaywrightError) as e:
                persistence_result["refresh_successful"] = False
                persistence_result["error"] = f"页面刷新失败: {str(e)}"
                logger.warning(f"页面刷新失败: {e}")
                return persistence_result
            
            # 3. 记录刷新后的状态
            after_theme = await self.detect_current_theme(page)
            after_methods = await self._verify_theme_by_all_methods(page, expected_theme)
            
            persistence_result["after_refresh"] = after_theme
            persistence_result["verification_methods_after"] = after_methods
            
            # 4. 判断持久化结果
            persistence_result["is_persistent"] = (
                before_theme == after_theme == expected_theme and
                before_theme is not None and
                after_theme is not None
            )
            
            if persistence_result["is_persistent"]:
                logger.debug(f"✓ 主题持久化验证成功: {expected_theme}")
            else:
                logger.warning(f"主题持久化验证失败: {before_theme} -> {after_theme} (期望: {expected_theme})")
            
            return persistence_result
            
        except Exception as e:
            error_msg = f"详细持久化验证异常: {str(e)}"
            logger.error(error_msg)
            persistence_result["error"] = error_msg
            return persistence_result
    
    def _generate_verification_recommendations(self, verification_result: Dict[str, Any], 
                                             methods_result: Dict[str, Any], 
                                             detected_theme: str, 
                                             expected_theme: str) -> list:
        """
        基于验证结果生成建议
        
        Args:
            verification_result: 验证结果
            methods_result: 各种方法的验证结果
            detected_theme: 检测到的主题
            expected_theme: 期望的主题
            
        Returns:
            建议列表
        """
        recommendations = []
        
        try:
            # 1. 基于主题匹配情况的建议
            if detected_theme != expected_theme:
                if detected_theme is None:
                    recommendations.append("无法检测到当前主题，建议检查页面是否为Bing搜索页面")
                    recommendations.append("确保页面完全加载后再进行主题验证")
                else:
                    recommendations.append(f"当前主题为 {detected_theme}，但期望为 {expected_theme}，建议重新设置主题")
                    recommendations.append("可以尝试使用强制主题应用功能")
            
            # 2. 基于验证分数的建议
            score = verification_result.get("verification_score", 0.0)
            if score < 0.3:
                recommendations.append("验证分数过低，建议检查页面状态和主题设置方法")
                recommendations.append("可能需要使用多种主题设置方法来确保成功")
            elif score < 0.7:
                recommendations.append("验证分数中等，建议优化主题设置方法")
                recommendations.append("某些检测方法可能不适用于当前页面")
            
            # 3. 基于各种检测方法的建议
            failed_methods = []
            error_methods = []
            
            for method_name, result in methods_result.items():
                if result.get("status") == "error":
                    error_methods.append(method_name)
                elif not result.get("matches_expected", False):
                    failed_methods.append(method_name)
            
            if error_methods:
                recommendations.append(f"以下检测方法发生错误: {', '.join(error_methods)}")
                recommendations.append("建议检查页面JavaScript执行环境和网络连接")
            
            if failed_methods:
                recommendations.append(f"以下检测方法未匹配期望主题: {', '.join(failed_methods)}")
                recommendations.append("可能需要针对这些方法优化主题设置策略")
            
            # 4. 基于持久化验证的建议
            if not verification_result.get("persistence_check", False) and detected_theme == expected_theme:
                recommendations.append("主题设置未能持久化，建议检查Cookie和localStorage设置")
                recommendations.append("可能需要使用更持久的主题设置方法")
            
            # 5. 通用建议
            if not recommendations:
                recommendations.append("主题验证完全成功，无需额外操作")
            else:
                recommendations.append("建议在设置主题后等待1-2秒再进行验证")
                recommendations.append("如果问题持续，可以考虑禁用主题管理功能")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成验证建议时发生异常: {e}")
            return ["生成建议时发生错误，建议手动检查主题设置"]
    
    async def verify_and_fix_theme_setting(self, page: Page, expected_theme: str = "dark", 
                                         max_attempts: int = 3) -> Dict[str, Any]:
        """
        验证主题设置，如果验证失败则尝试修复
        这是任务6.2.1的扩展功能：提供验证和自动修复的组合功能
        
        Args:
            page: Playwright页面对象
            expected_theme: 期望的主题
            max_attempts: 最大修复尝试次数
            
        Returns:
            验证和修复结果
        """
        result = {
            "final_success": False,
            "initial_verification": None,
            "fix_attempts": [],
            "final_verification": None,
            "total_attempts": 0,
            "error": None
        }
        
        try:
            logger.info(f"开始验证和修复主题设置: {expected_theme}")
            
            # 1. 初始验证
            initial_verification = await self.verify_theme_setting(page, expected_theme)
            result["initial_verification"] = initial_verification
            
            if initial_verification["success"]:
                logger.info("✓ 初始主题验证成功，无需修复")
                result["final_success"] = True
                result["final_verification"] = initial_verification
                return result
            
            logger.info(f"初始主题验证失败 (分数: {initial_verification['verification_score']:.2f})，开始修复...")
            
            # 2. 尝试修复
            for attempt in range(max_attempts):
                result["total_attempts"] = attempt + 1
                logger.info(f"主题修复尝试 {attempt + 1}/{max_attempts}")
                
                fix_attempt = {
                    "attempt_number": attempt + 1,
                    "method_used": None,
                    "success": False,
                    "verification_after_fix": None,
                    "error": None
                }
                
                try:
                    # 选择修复方法
                    if attempt == 0:
                        # 第一次尝试：标准设置
                        fix_attempt["method_used"] = "standard_setting"
                        fix_success = await self.set_theme(page, expected_theme)
                    elif attempt == 1:
                        # 第二次尝试：带重试的设置
                        fix_attempt["method_used"] = "retry_setting"
                        fix_success = await self.set_theme_with_retry(page, expected_theme, max_retries=2)
                    else:
                        # 最后尝试：降级策略
                        fix_attempt["method_used"] = "fallback_setting"
                        fix_success = await self.set_theme_with_fallback(page, expected_theme)
                    
                    fix_attempt["success"] = fix_success
                    
                    if fix_success:
                        # 修复成功，进行验证
                        await asyncio.sleep(1)  # 等待主题应用
                        verification_after_fix = await self.verify_theme_setting(page, expected_theme)
                        fix_attempt["verification_after_fix"] = verification_after_fix
                        
                        if verification_after_fix["success"]:
                            logger.info(f"✓ 第{attempt + 1}次修复成功")
                            result["final_success"] = True
                            result["final_verification"] = verification_after_fix
                            result["fix_attempts"].append(fix_attempt)
                            return result
                        else:
                            logger.warning(f"第{attempt + 1}次修复后验证仍失败 (分数: {verification_after_fix['verification_score']:.2f})")
                    else:
                        logger.warning(f"第{attempt + 1}次修复方法失败")
                    
                except Exception as e:
                    error_msg = f"第{attempt + 1}次修复尝试异常: {str(e)}"
                    logger.error(error_msg)
                    fix_attempt["error"] = error_msg
                
                result["fix_attempts"].append(fix_attempt)
                
                # 如果不是最后一次尝试，等待一下再继续
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
            
            # 3. 所有修复尝试都失败，进行最终验证
            logger.warning(f"所有{max_attempts}次修复尝试都失败")
            final_verification = await self.verify_theme_setting(page, expected_theme)
            result["final_verification"] = final_verification
            result["final_success"] = final_verification["success"]
            
            return result
            
        except Exception as e:
            error_msg = f"验证和修复主题设置异常: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            return result
    
    async def _handle_theme_setting_failure(self, page: Page, theme: str, failure_details: list) -> None:
        """
        处理主题设置失败的情况
        提供详细的错误报告和诊断信息
        
        Args:
            page: Playwright页面对象
            theme: 目标主题
            failure_details: 失败详情列表
        """
        try:
            logger.warning(f"所有主题设置方法都失败了，目标主题: {theme}")
            
            # 记录详细失败信息
            for i, detail in enumerate(failure_details, 1):
                logger.debug(f"失败详情 {i}: {detail}")
            
            # 生成诊断报告
            diagnostic_info = await self._generate_theme_failure_diagnostic(page, theme, failure_details)
            
            # 记录诊断信息
            logger.info("主题设置失败诊断报告:")
            logger.info(f"  页面URL: {diagnostic_info.get('page_url', '未知')}")
            logger.info(f"  页面标题: {diagnostic_info.get('page_title', '未知')}")
            logger.info(f"  当前检测到的主题: {diagnostic_info.get('current_theme', '未知')}")
            logger.info(f"  目标主题: {theme}")
            logger.info(f"  失败方法数量: {len(failure_details)}")
            
            # 提供解决建议
            suggestions = self._generate_failure_suggestions(diagnostic_info, theme)
            if suggestions:
                logger.info("建议的解决方案:")
                for i, suggestion in enumerate(suggestions, 1):
                    logger.info(f"  {i}. {suggestion}")
            
            # 尝试保存诊断截图（如果可能）
            await self._save_failure_screenshot(page, theme)
            
        except Exception as e:
            logger.error(f"处理主题设置失败时发生异常: {e}")
    
    async def _generate_theme_failure_diagnostic(self, page: Page, theme: str, failure_details: list) -> Dict[str, Any]:
        """
        生成主题设置失败的诊断信息
        
        Args:
            page: Playwright页面对象
            theme: 目标主题
            failure_details: 失败详情列表
            
        Returns:
            诊断信息字典
        """
        diagnostic = {
            "timestamp": asyncio.get_running_loop().time(),
            "target_theme": theme,
            "failure_count": len(failure_details),
            "failure_details": failure_details,
            # 确保这些字段总是存在
            "current_theme": "未知",
            "page_url": "未知",
            "page_title": "未知",
            "page_ready_state": "未知",
            "is_bing_page": False,
            "page_has_error": "未知",
            "network_online": "未知"
        }
        
        try:
            # 页面基本信息
            if page:
                diagnostic["page_url"] = page.url
                try:
                    diagnostic["page_title"] = await page.title()
                except Exception:
                    diagnostic["page_title"] = "获取失败"
            
            # 当前主题检测
            try:
                current_theme = await self.detect_current_theme(page)
                diagnostic["current_theme"] = current_theme if current_theme else "未知"
            except Exception as e:
                diagnostic["current_theme"] = f"检测失败: {str(e)}"
            
            # 页面状态检查
            try:
                page_ready = await page.evaluate("document.readyState")
                diagnostic["page_ready_state"] = page_ready
            except Exception:
                diagnostic["page_ready_state"] = "未知"
            
            # 检查是否为Bing页面
            diagnostic["is_bing_page"] = "bing.com" in diagnostic["page_url"].lower()
            
            # 检查页面是否有错误
            try:
                has_error = await page.evaluate("""
                    () => {
                        return document.body.innerText.toLowerCase().includes('error') ||
                               document.body.innerText.toLowerCase().includes('404') ||
                               document.body.innerText.toLowerCase().includes('500');
                    }
                """)
                diagnostic["page_has_error"] = has_error
            except Exception:
                diagnostic["page_has_error"] = "未知"
            
            # 检查网络状态
            try:
                network_state = await page.evaluate("navigator.onLine")
                diagnostic["network_online"] = network_state
            except Exception:
                diagnostic["network_online"] = "未知"
            
        except Exception as e:
            diagnostic["diagnostic_error"] = str(e)
        
        return diagnostic
    
    def _generate_failure_suggestions(self, diagnostic_info: Dict[str, Any], theme: str) -> list:
        """
        基于诊断信息生成失败解决建议
        
        Args:
            diagnostic_info: 诊断信息
            theme: 目标主题
            
        Returns:
            建议列表
        """
        suggestions = []
        
        try:
            # 检查是否为Bing页面
            if not diagnostic_info.get("is_bing_page", False):
                suggestions.append("确保当前页面是Bing搜索页面 (bing.com)")
            
            # 检查页面状态
            if diagnostic_info.get("page_ready_state") != "complete":
                suggestions.append("等待页面完全加载后再尝试设置主题")
            
            # 检查网络状态
            if diagnostic_info.get("network_online") is False:
                suggestions.append("检查网络连接是否正常")
            
            # 检查页面错误
            if diagnostic_info.get("page_has_error"):
                suggestions.append("页面可能存在错误，尝试刷新页面后重试")
            
            # 检查当前主题
            current_theme = diagnostic_info.get("current_theme")
            if current_theme and current_theme != theme:
                suggestions.append(f"当前主题为 {current_theme}，可能需要手动设置为 {theme}")
            elif current_theme == "未知":
                suggestions.append("无法检测当前主题，页面可能不支持主题设置")
            
            # 通用建议
            suggestions.extend([
                "尝试刷新页面后重新设置主题",
                "检查浏览器是否支持JavaScript",
                "尝试清除浏览器缓存和Cookie",
                "考虑使用不同的浏览器或用户代理"
            ])
            
            # 如果失败次数很多，建议禁用主题管理
            if diagnostic_info.get("failure_count", 0) >= 6:
                suggestions.append("考虑在配置中禁用主题管理 (bing_theme.enabled: false)")
            
        except Exception as e:
            suggestions.append(f"生成建议时发生错误: {str(e)}")
        
        return suggestions
    
    async def _save_failure_screenshot(self, page: Page, theme: str) -> bool:
        """
        保存主题设置失败时的截图
        
        Args:
            page: Playwright页面对象
            theme: 目标主题
            
        Returns:
            是否成功保存截图
        """
        try:
            if not page:
                return False
            
            # 创建截图目录
            from pathlib import Path
            import time
            
            screenshot_dir = Path("logs/theme_failures")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成截图文件名
            timestamp = int(time.time())
            screenshot_path = screenshot_dir / f"theme_failure_{theme}_{timestamp}.png"
            
            # 保存截图
            await page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"已保存主题设置失败截图: {screenshot_path}")
            
            return True
            
        except Exception as e:
            logger.debug(f"保存失败截图时发生异常: {e}")
            return False
    
    async def set_theme_with_fallback(self, page: Page, theme: str = "dark") -> bool:
        """
        带降级策略的主题设置
        如果标准设置失败，尝试降级方案
        
        Args:
            page: Playwright页面对象
            theme: 目标主题 ("dark" 或 "light")
            
        Returns:
            是否设置成功（包括降级方案）
        """
        try:
            logger.debug(f"开始带降级策略的主题设置: {theme}")
            
            # 首先尝试标准设置
            success = await self.set_theme(page, theme)
            if success:
                logger.debug("标准主题设置成功")
                return True
            
            logger.info("标准主题设置失败，尝试降级策略...")
            
            # 降级策略1: 强制应用所有方法
            logger.debug("降级策略1: 强制应用所有方法")
            force_success = await self.force_theme_application(page, theme)
            if force_success:
                logger.info("✓ 降级策略1成功: 强制应用")
                return True
            
            # 降级策略2: 仅应用CSS样式（不验证）
            logger.debug("降级策略2: 仅应用CSS样式")
            css_success = await self._apply_css_only_theme(page, theme)
            if css_success:
                logger.info("✓ 降级策略2成功: CSS样式应用")
                return True
            
            # 降级策略3: 设置最小化主题标记
            logger.debug("降级策略3: 设置最小化主题标记")
            minimal_success = await self._apply_minimal_theme_markers(page, theme)
            if minimal_success:
                logger.info("✓ 降级策略3成功: 最小化主题标记")
                return True
            
            logger.warning("所有降级策略都失败，主题设置完全失败")
            return False
            
        except Exception as e:
            logger.error(f"带降级策略的主题设置异常: {e}")
            return False
    
    async def _apply_css_only_theme(self, page: Page, theme: str) -> bool:
        """
        仅应用CSS样式的主题设置（降级方案）
        
        Args:
            page: Playwright页面对象
            theme: 目标主题
            
        Returns:
            是否成功应用CSS
        """
        try:
            logger.debug(f"应用仅CSS的{theme}主题...")
            
            # 生成并注入CSS
            css_content = self._generate_force_theme_css(theme)
            await page.add_style_tag(content=css_content)
            
            # 设置基本的页面属性
            await page.evaluate(f"""
                () => {{
                    const theme = '{theme}';
                    document.documentElement.setAttribute('data-fallback-theme', theme);
                    document.body.setAttribute('data-fallback-theme', theme);
                    document.documentElement.classList.add('fallback-' + theme + '-theme');
                    document.body.classList.add('fallback-' + theme + '-theme');
                }}
            """)
            
            logger.debug("✓ CSS主题样式应用完成")
            return True
            
        except Exception as e:
            logger.debug(f"CSS主题应用失败: {e}")
            return False
    
    async def _apply_minimal_theme_markers(self, page: Page, theme: str) -> bool:
        """
        应用最小化主题标记（最后的降级方案）
        
        Args:
            page: Playwright页面对象
            theme: 目标主题
            
        Returns:
            是否成功应用标记
        """
        try:
            logger.debug(f"应用最小化{theme}主题标记...")
            
            # 仅设置最基本的标记
            await page.evaluate(f"""
                () => {{
                    const theme = '{theme}';
                    try {{
                        // 设置最基本的属性
                        document.documentElement.setAttribute('data-minimal-theme', theme);
                        document.body.setAttribute('data-minimal-theme', theme);
                        
                        // 尝试设置基本的颜色方案
                        document.documentElement.style.colorScheme = theme;
                        
                        // 在localStorage中记录主题偏好
                        localStorage.setItem('theme-fallback', theme);
                        
                        return true;
                    }} catch (e) {{
                        console.debug('最小化主题标记设置异常:', e);
                        return false;
                    }}
                }}
            """)
            
            logger.debug("✓ 最小化主题标记应用完成")
            return True
            
        except Exception as e:
            logger.debug(f"最小化主题标记应用失败: {e}")
            return False