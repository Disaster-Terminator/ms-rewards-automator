"""
任务服务
管理任务执行和状态
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.config_manager import ConfigManager
from infrastructure.ms_rewards_app import MSRewardsApp


logger = logging.getLogger(__name__)


class TaskService:
    """任务服务类"""
    
    def __init__(self, connection_manager, config_service):
        """
        初始化任务服务
        
        Args:
            connection_manager: WebSocket 连接管理器
            config_service: 配置服务
        """
        self.connection_manager = connection_manager
        self.config_service = config_service
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        self.status = {
            "is_running": False,
            "current_operation": "空闲",
            "progress": 0,
            "total_steps": 8,
            "desktop_searches_completed": 0,
            "desktop_searches_total": 0,
            "mobile_searches_completed": 0,
            "mobile_searches_total": 0,
            "initial_points": None,
            "current_points": None,
            "points_gained": 0,
            "error_count": 0,
            "warning_count": 0,
            "start_time": None,
            "elapsed_seconds": 0.0,
        }
        
        self._history_file = Path("logs/task_history.json")
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前任务状态"""
        status = self.status.copy()
        
        if status["start_time"]:
            status["elapsed_seconds"] = time.time() - status["start_time"]
        
        return status
    
    def get_points_info(self) -> Dict[str, Any]:
        """获取积分信息"""
        return {
            "current_points": self.status["current_points"],
            "lifetime_points": None,
            "points_gained_today": self.status["points_gained"],
            "last_updated": datetime.now().isoformat() if self.status["current_points"] else None,
        }
    
    def get_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取历史记录
        
        Args:
            days: 查询天数
            
        Returns:
            历史记录列表
        """
        history = []
        
        if self._history_file.exists():
            try:
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    all_history = json.load(f)
                
                cutoff = datetime.now().timestamp() - (days * 24 * 3600)
                history = [
                    h for h in all_history 
                    if datetime.fromisoformat(h["timestamp"]).timestamp() >= cutoff
                ]
            except Exception as e:
                logger.error(f"加载历史记录失败: {e}")
        
        return history
    
    async def start_task(
        self,
        mode: str = "normal",
        headless: bool = False,
        desktop_only: bool = False,
        mobile_only: bool = False,
        skip_daily_tasks: bool = False,
    ):
        if self.is_running:
            logger.warning("任务已在运行中")
            return
        
        self.is_running = True
        self._stop_event.clear()
        
        desktop_count = self.config_service.get("search.desktop_count", 30)
        mobile_count = self.config_service.get("search.mobile_count", 20)
        
        self.status.update({
            "is_running": True,
            "current_operation": "初始化",
            "progress": 0,
            "desktop_searches_completed": 0,
            "desktop_searches_total": desktop_count,
            "mobile_searches_completed": 0,
            "mobile_searches_total": mobile_count,
            "initial_points": None,
            "current_points": None,
            "points_gained": 0,
            "error_count": 0,
            "warning_count": 0,
            "start_time": time.time(),
            "elapsed_seconds": 0.0,
        })
        
        await self.connection_manager.broadcast_task_event(
            "started", 
            "任务已启动",
            {"mode": mode, "headless": headless}
        )
        
        self._task = asyncio.current_task()
        
        try:
            config = ConfigManager("config.yaml")
            
            if headless:
                config.set("browser.headless", True)
            
            class Args:
                def __init__(self):
                    self.mode = mode
                    self.dev = mode == "dev"
                    self.usermode = mode == "usermode"
                    self.headless = headless
                    self.browser = "chromium"
                    self.desktop_only = desktop_only
                    self.mobile_only = mobile_only
                    self.skip_daily_tasks = skip_daily_tasks
                    self.dry_run = False
            
            args = Args()
            app = MSRewardsApp(config, args)
            
            def status_callback(operation: str, progress: int, total: int):
                self.status["current_operation"] = operation
                self.status["progress"] = progress
                self.status["total_steps"] = total
                asyncio.create_task(self._broadcast_status_update())
            
            def search_callback(device: str, completed: int, total: int):
                if device == "desktop":
                    self.status["desktop_searches_completed"] = completed
                    self.status["desktop_searches_total"] = total
                else:
                    self.status["mobile_searches_completed"] = completed
                    self.status["mobile_searches_total"] = total
                asyncio.create_task(self._broadcast_status_update())
            
            def points_callback(current: int, initial: int):
                self.status["current_points"] = current
                self.status["initial_points"] = initial
                self.status["points_gained"] = current - initial if initial else 0
                asyncio.create_task(self._broadcast_points_update())
            
            exit_code = await app.run()
            
            self.status["current_operation"] = "完成"
            self.status["progress"] = self.status["total_steps"]
            
            await self._save_history()
            
            await self.connection_manager.broadcast_task_event(
                "completed",
                "任务执行完成",
                {
                    "exit_code": exit_code,
                    "points_gained": self.status["points_gained"],
                    "duration": time.time() - self.status["start_time"] if self.status["start_time"] else 0,
                }
            )
            
        except asyncio.CancelledError:
            logger.info("任务被取消")
            self.status["current_operation"] = "已取消"
            await self.connection_manager.broadcast_task_event("cancelled", "任务已取消")
            
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            self.status["error_count"] += 1
            self.status["current_operation"] = f"错误: {str(e)}"
            await self.connection_manager.broadcast_task_event("error", f"任务执行失败: {e}")
            
        finally:
            self.is_running = False
            self.status["is_running"] = False
            self._task = None
            await self._broadcast_status_update()
    
    async def stop_task(self):
        """停止当前任务"""
        if not self.is_running:
            return
        
        logger.info("正在停止任务...")
        self._stop_event.set()
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self.is_running = False
        self.status["is_running"] = False
        self.status["current_operation"] = "已停止"
        
        await self._broadcast_status_update()
    
    async def _broadcast_status_update(self):
        """广播状态更新"""
        await self.connection_manager.broadcast_status(self.get_status())
    
    async def _broadcast_points_update(self):
        """广播积分更新"""
        await self.connection_manager.broadcast_points(self.get_points_info())
    
    async def _save_history(self):
        """保存历史记录"""
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            
            history = []
            if self._history_file.exists():
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            history.append({
                "timestamp": datetime.now().isoformat(),
                "points_gained": self.status["points_gained"],
                "desktop_searches": self.status["desktop_searches_completed"],
                "mobile_searches": self.status["mobile_searches_completed"],
                "errors": self.status["error_count"],
                "duration_seconds": time.time() - self.status["start_time"] if self.status["start_time"] else 0,
            })
            
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(history[-100:], f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
