"""
MS Rewards Automator - Web API 服务器入口
启动 FastAPI 服务器和前端服务
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.app import lifespan
from api.routes import router as api_router
from api.websocket import ConnectionManager


logger = logging.getLogger(__name__)

connection_manager = ConnectionManager()


def create_web_app() -> FastAPI:
    """
    创建 Web 应用实例
    
    Returns:
        配置好的 FastAPI 应用实例
    """
    app = FastAPI(
        title="MS Rewards Automator",
        description="Microsoft Rewards 自动化工具 Web 界面",
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
    
    app.include_router(api_router, prefix="/api")
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await connection_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await connection_manager.send_personal_message(
                    {"type": "echo", "data": data}, 
                    websocket
                )
        except WebSocketDisconnect:
            await connection_manager.disconnect(websocket)
    
    frontend_dist = Path(__file__).parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
        
        @app.get("/{path:path}")
        async def serve_frontend(path: str):
            file_path = frontend_dist / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(frontend_dist / "index.html"))
    else:
        logger.warning(f"前端构建目录不存在: {frontend_dist}")
    
    return app


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    运行 Web 服务器
    
    Args:
        host: 监听地址
        port: 监听端口
    """
    app = create_web_app()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           MS Rewards Automator Web Interface                 ║
╠══════════════════════════════════════════════════════════════╣
║  服务地址: http://{host}:{port}                              ║
║  API 文档: http://{host}:{port}/docs                         ║
║  按 Ctrl+C 停止服务                                          ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MS Rewards Automator Web Server")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port)
