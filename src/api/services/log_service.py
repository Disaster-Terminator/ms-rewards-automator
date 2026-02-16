"""
日志服务
管理日志读取和实时推送
"""

import asyncio
import logging
import time
import threading
from typing import List, Optional, AsyncGenerator, TYPE_CHECKING
from pathlib import Path
from datetime import datetime
import queue

if TYPE_CHECKING:
    from api.websocket import ConnectionManager


logger = logging.getLogger(__name__)


class LogService:
    """日志服务类"""
    
    def __init__(self, log_file: str = "logs/automator.log"):
        """
        初始化日志服务
        
        Args:
            log_file: 日志文件路径
        """
        self.log_file = Path(log_file)
        self._log_queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._watcher_thread: Optional[threading.Thread] = None
        self._subscribers: List[asyncio.Queue] = []
        self._connection_manager: Optional['ConnectionManager'] = None
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
    
    def set_connection_manager(self, manager: 'ConnectionManager'):
        """设置 WebSocket 连接管理器"""
        self._connection_manager = manager
    
    def start_log_watcher(self):
        """启动日志监视器"""
        if self._watcher_thread and self._watcher_thread.is_alive():
            return
        
        try:
            self._async_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._async_loop = None
        
        self._stop_event.clear()
        self._watcher_thread = threading.Thread(target=self._watch_log_file, daemon=True)
        self._watcher_thread.start()
        logger.info("日志监视器已启动")
    
    def stop_log_watcher(self):
        """停止日志监视器"""
        self._stop_event.set()
        if self._watcher_thread:
            self._watcher_thread.join(timeout=2)
        logger.info("日志监视器已停止")
    
    def _watch_log_file(self):
        """监视日志文件变化"""
        try:
            if not self.log_file.exists():
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                self.log_file.touch()
            
            with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(0, 2)
                
                while not self._stop_event.is_set():
                    line = f.readline()
                    if line:
                        line_stripped = line.strip()
                        self._log_queue.put(line_stripped)
                        self._notify_subscribers(line_stripped)
                        self._broadcast_to_websocket(line_stripped)
                    else:
                        time.sleep(0.1)
                        
        except Exception as e:
            logger.error(f"日志监视器错误: {e}")
    
    def _notify_subscribers(self, line: str):
        """通知所有订阅者"""
        for q in self._subscribers:
            try:
                q.put_nowait(line)
            except asyncio.QueueFull:
                pass
    
    def _broadcast_to_websocket(self, line: str):
        """广播日志到 WebSocket"""
        if self._connection_manager and self._async_loop and not self._stop_event.is_set():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._connection_manager.broadcast_log(line),
                    self._async_loop
                )
                future.result(timeout=1.0)
            except Exception as e:
                logger.debug(f"广播日志失败: {e}")
    
    def get_recent_logs(self, lines: int = 100) -> List[str]:
        """
        获取最近的日志
        
        Args:
            lines: 行数
            
        Returns:
            日志行列表
        """
        try:
            if not self.log_file.exists():
                return []
            
            with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
                return [line.strip() for line in all_lines[-lines:]]
                
        except Exception as e:
            logger.error(f"读取日志失败: {e}")
            return []
    
    async def log_stream(self) -> AsyncGenerator[str, None]:
        """
        日志流生成器
        
        Yields:
            日志行
        """
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(q)
        
        try:
            while True:
                try:
                    line = await asyncio.wait_for(q.get(), timeout=1.0)
                    yield line
                except asyncio.TimeoutError:
                    yield ""
        finally:
            self._subscribers.remove(q)
    
    def search_logs(self, keyword: str, lines: int = 1000) -> List[str]:
        """
        搜索日志
        
        Args:
            keyword: 搜索关键词
            lines: 搜索范围行数
            
        Returns:
            匹配的日志行
        """
        try:
            if not self.log_file.exists():
                return []
            
            results = []
            with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if keyword.lower() in line.lower():
                        results.append(line.strip())
                        if len(results) >= lines:
                            break
            
            return results
            
        except Exception as e:
            logger.error(f"搜索日志失败: {e}")
            return []
    
    def get_log_stats(self) -> dict:
        """
        获取日志统计
        
        Returns:
            统计信息
        """
        try:
            if not self.log_file.exists():
                return {"exists": False}
            
            stat = self.log_file.stat()
            
            error_count = 0
            warning_count = 0
            
            with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if 'ERROR' in line:
                        error_count += 1
                    elif 'WARNING' in line:
                        warning_count += 1
            
            return {
                "exists": True,
                "size_bytes": stat.st_size,
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "error_count": error_count,
                "warning_count": warning_count,
            }
            
        except Exception as e:
            logger.error(f"获取日志统计失败: {e}")
            return {"exists": False, "error": str(e)}
