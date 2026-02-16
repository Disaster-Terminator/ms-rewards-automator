"""
FastAPI 应用工厂
创建和配置 FastAPI 应用实例
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .routes import router
from .websocket import ConnectionManager
from .services import TaskService, ConfigService, LogService, HealthService


logger = logging.getLogger(__name__)

task_service: Optional[TaskService] = None
config_service: Optional[ConfigService] = None
log_service: Optional[LogService] = None
health_service: Optional[HealthService] = None
connection_manager: Optional[ConnectionManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global task_service, config_service, log_service, health_service, connection_manager
    
    logger.info("正在启动 API 服务...")
    
    connection_manager = ConnectionManager()
    config_service = ConfigService()
    log_service = LogService()
    health_service = HealthService()
    task_service = TaskService(connection_manager, config_service)
    
    log_service.set_connection_manager(connection_manager)
    
    app.state.task_service = task_service
    app.state.config_service = config_service
    app.state.log_service = log_service
    app.state.health_service = health_service
    app.state.connection_manager = connection_manager
    
    log_service.start_log_watcher()
    
    logger.info("API 服务已启动，WebSocket 连接管理器已初始化")
    
    yield
    
    logger.info("正在关闭 API 服务...")
    
    if task_service and task_service.is_running:
        await task_service.stop_task()
    
    if log_service:
        log_service.stop_log_watcher()
    
    logger.info("API 服务已关闭")


def create_app(config_path: str = "config.yaml") -> FastAPI:
    """
    创建 FastAPI 应用实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置好的 FastAPI 应用实例
    """
    app = FastAPI(
        title="MS Rewards Automator API",
        description="Microsoft Rewards 自动化工具的 Web API",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router, prefix="/api")
    
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
    
    return app
