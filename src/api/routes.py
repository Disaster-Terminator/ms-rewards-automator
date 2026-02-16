"""
API 路由定义
定义所有 RESTful API 端点
"""

import asyncio
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .websocket import ConnectionManager


logger = logging.getLogger(__name__)
router = APIRouter()


class TaskStartRequest(BaseModel):
    mode: str = "normal"
    headless: bool = False
    desktop_only: bool = False
    mobile_only: bool = False
    skip_daily_tasks: bool = False


class TaskStatusResponse(BaseModel):
    is_running: bool
    current_operation: str
    progress: int
    total_steps: int
    desktop_searches_completed: int
    desktop_searches_total: int
    mobile_searches_completed: int
    mobile_searches_total: int
    initial_points: Optional[int]
    current_points: Optional[int]
    points_gained: int
    error_count: int
    warning_count: int
    start_time: Optional[float]
    elapsed_seconds: float


class ConfigResponse(BaseModel):
    search: dict
    browser: dict
    account: dict
    login: dict
    task_system: dict
    notification: dict
    scheduler: dict
    logging: dict
    bing_theme: dict
    monitoring: dict


class ConfigUpdateRequest(BaseModel):
    search: Optional[dict] = None
    browser: Optional[dict] = None
    account: Optional[dict] = None
    login: Optional[dict] = None
    task_system: Optional[dict] = None
    notification: Optional[dict] = None
    scheduler: Optional[dict] = None
    logging: Optional[dict] = None
    bing_theme: Optional[dict] = None
    monitoring: Optional[dict] = None


class HealthResponse(BaseModel):
    overall: str
    system: dict
    network: dict
    browser: dict
    search_stats: dict
    uptime_seconds: float
    recommendations: List[str]


class PointsResponse(BaseModel):
    current_points: Optional[int]
    lifetime_points: Optional[int]
    points_gained_today: int
    last_updated: Optional[str]


def get_services(request: Request):
    """获取服务实例"""
    services = {
        "task_service": getattr(request.app.state, 'task_service', None),
        "config_service": getattr(request.app.state, 'config_service', None),
        "log_service": getattr(request.app.state, 'log_service', None),
        "health_service": getattr(request.app.state, 'health_service', None),
        "connection_manager": getattr(request.app.state, 'connection_manager', None),
    }
    
    for name, service in services.items():
        if service is None:
            raise HTTPException(status_code=503, detail=f"服务未就绪: {name}")
    
    return services


@router.get("/status", response_model=TaskStatusResponse)
async def get_task_status(request: Request):
    """获取当前任务状态"""
    services = get_services(request)
    task_service = services["task_service"]
    
    status = task_service.get_status()
    return TaskStatusResponse(**status)


@router.post("/task/start")
async def start_task(request: Request, task_request: TaskStartRequest):
    """启动任务"""
    try:
        services = get_services(request)
        task_service = services["task_service"]
        
        if task_service.is_running:
            raise HTTPException(status_code=400, detail="任务正在运行中")
        
        asyncio.create_task(task_service.start_task(
            mode=task_request.mode,
            headless=task_request.headless,
            desktop_only=task_request.desktop_only,
            mobile_only=task_request.mobile_only,
            skip_daily_tasks=task_request.skip_daily_tasks,
        ))
        
        return {"message": "任务已启动", "status": "starting"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"启动任务失败: {str(e)}")


@router.post("/task/stop")
async def stop_task(request: Request):
    """停止任务"""
    services = get_services(request)
    task_service = services["task_service"]
    
    if not task_service.is_running:
        raise HTTPException(status_code=400, detail="没有正在运行的任务")
    
    await task_service.stop_task()
    return {"message": "任务已停止", "status": "stopped"}


@router.get("/config", response_model=ConfigResponse)
async def get_config(request: Request):
    """获取当前配置"""
    services = get_services(request)
    config_service = services["config_service"]
    
    config = config_service.get_config()
    return ConfigResponse(**config)


@router.put("/config")
async def update_config(request: Request, config_update: ConfigUpdateRequest):
    """更新配置"""
    services = get_services(request)
    config_service = services["config_service"]
    
    update_dict = config_update.model_dump(exclude_unset=True)
    config_service.update_config(update_dict)
    
    return {"message": "配置已更新"}


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request):
    """获取健康状态"""
    services = get_services(request)
    health_service = services["health_service"]
    
    health = health_service.get_health()
    return HealthResponse(**health)


@router.get("/points", response_model=PointsResponse)
async def get_points(request: Request):
    """获取积分信息"""
    services = get_services(request)
    task_service = services["task_service"]
    
    points = task_service.get_points_info()
    return PointsResponse(**points)


@router.get("/logs/recent")
async def get_recent_logs(request: Request, lines: int = 100):
    """获取最近的日志"""
    services = get_services(request)
    log_service = services["log_service"]
    
    logs = log_service.get_recent_logs(lines)
    return {"logs": logs, "count": len(logs)}


@router.get("/logs/stream")
async def stream_logs(request: Request):
    """实时日志流"""
    services = get_services(request)
    log_service = services["log_service"]
    
    async def log_generator():
        async for line in log_service.log_stream():
            yield f"data: {line}\n\n"
    
    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
    )


@router.get("/history")
async def get_history(request: Request, days: int = 7):
    """获取历史记录"""
    services = get_services(request)
    task_service = services["task_service"]
    
    history = task_service.get_history(days)
    return {"history": history, "days": days}


@router.get("/dashboard")
async def get_dashboard(request: Request):
    """获取仪表盘数据"""
    services = get_services(request)
    task_service = services["task_service"]
    health_service = services["health_service"]
    config_service = services["config_service"]
    
    dashboard_data = {
        "status": task_service.get_status(),
        "health": health_service.get_health(),
        "config_summary": config_service.get_summary(),
        "points": task_service.get_points_info(),
    }
    
    return dashboard_data
