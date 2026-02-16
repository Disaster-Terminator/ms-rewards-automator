"""
MS Rewards Automator - Web API 模块
提供 RESTful API 和 WebSocket 支持
"""

from .app import create_app
from .routes import router

__all__ = ["create_app", "router"]
