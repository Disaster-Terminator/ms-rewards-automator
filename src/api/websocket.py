"""
WebSocket 连接管理器
管理 WebSocket 连接和实时状态推送
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Set
from datetime import datetime
from fastapi import WebSocket


logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """
        接受新的 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接实例
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket 连接已建立，当前连接数: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """
        断开 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接实例
        """
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket 连接已断开，当前连接数: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        发送消息给特定客户端
        
        Args:
            message: 消息内容
            websocket: 目标 WebSocket 连接
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            await self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        广播消息给所有连接的客户端
        
        Args:
            message: 消息内容
        """
        if not self.active_connections:
            return
        
        message_json = json.dumps(message, ensure_ascii=False, default=str)
        disconnected = set()
        
        async with self._lock:
            connections = list(self.active_connections)
        
        for connection in connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.debug(f"广播消息失败: {e}")
                disconnected.add(connection)
        
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def broadcast_status(self, status: Dict[str, Any]):
        """
        广播任务状态更新
        
        Args:
            status: 状态数据
        """
        await self.broadcast({
            "type": "status_update",
            "timestamp": datetime.now().isoformat(),
            "data": status
        })
    
    async def broadcast_log(self, log_line: str):
        """
        广播日志消息
        
        Args:
            log_line: 日志行
        """
        await self.broadcast({
            "type": "log",
            "timestamp": datetime.now().isoformat(),
            "data": log_line
        })
    
    async def broadcast_health(self, health: Dict[str, Any]):
        """
        广播健康状态更新
        
        Args:
            health: 健康状态数据
        """
        await self.broadcast({
            "type": "health_update",
            "timestamp": datetime.now().isoformat(),
            "data": health
        })
    
    async def broadcast_points(self, points: Dict[str, Any]):
        """
        广播积分更新
        
        Args:
            points: 积分数据
        """
        await self.broadcast({
            "type": "points_update",
            "timestamp": datetime.now().isoformat(),
            "data": points
        })
    
    async def broadcast_task_event(self, event_type: str, message: str, details: Dict[str, Any] = None):
        """
        广播任务事件
        
        Args:
            event_type: 事件类型 (started, completed, error, etc.)
            message: 事件消息
            details: 事件详情
        """
        await self.broadcast({
            "type": "task_event",
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "details": details or {}
        })
