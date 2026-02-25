#!/usr/bin/env python3
"""
Tools 共享工具函数

提供 .env 加载和 sys.path 设置等通用功能
"""

import os
import sys
from pathlib import Path


def setup_project_path() -> None:
    """
    设置项目路径，确保可以导入 src 模块

    将项目根目录和 src 目录添加到 sys.path
    """
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"

    project_root_str = str(project_root)
    src_path_str = str(src_path)

    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    if src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)


def load_env_file() -> None:
    """
    从 .env 文件加载环境变量

    只加载尚未设置的环境变量，不覆盖已存在的值
    """
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key and value and key not in os.environ:
                    os.environ[key] = value


def get_github_token() -> str | None:
    """
    获取 GitHub Token

    优先从环境变量获取，如果不存在则尝试从 .env 文件加载

    Returns:
        GitHub Token 或 None
    """
    load_env_file()
    return os.environ.get("GITHUB_TOKEN")


def require_github_token() -> str:
    """
    获取 GitHub Token，如果不存在则抛出异常

    Returns:
        GitHub Token

    Raises:
        RuntimeError: 如果未设置 GITHUB_TOKEN
    """
    token = get_github_token()
    if not token:
        raise RuntimeError("未设置 GITHUB_TOKEN 环境变量，请在 .env 文件中配置或设置环境变量")
    return token
