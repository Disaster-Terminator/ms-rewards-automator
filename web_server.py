"""
MS Rewards Automator - Web API 服务器入口
启动 FastAPI 服务器和前端服务
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "automator.log", encoding="utf-8"),
    ],
)

import uvicorn  # noqa: E402
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from api.app import lifespan  # noqa: E402
from api.routes import router as api_router  # noqa: E402

logger = logging.getLogger(__name__)


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
        from api.app import connection_manager

        if not connection_manager:
            try:
                await websocket.close(code=1011, reason="Server not ready")
            except Exception:
                pass
            return

        try:
            await connection_manager.connect(websocket)
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            return

        try:
            while True:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                    try:
                        import json

                        message = json.loads(data)
                        if message.get("type") == "ping":
                            try:
                                await connection_manager.send_personal_message(
                                    {
                                        "type": "pong",
                                        "timestamp": __import__("datetime").datetime.now().isoformat(),
                                    },
                                    websocket,
                                )
                            except Exception:
                                pass
                    except json.JSONDecodeError:
                        pass
                except asyncio.TimeoutError:
                    try:
                        await connection_manager.send_personal_message(
                            {
                                "type": "ping",
                                "timestamp": __import__("datetime").datetime.now().isoformat(),
                            },
                            websocket,
                        )
                    except Exception:
                        break
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.debug(f"WebSocket error: {e}")
        finally:
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
