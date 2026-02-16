"""
日志系统模块
配置和管理应用程序日志
"""

import logging
from pathlib import Path


def setup_logging(
    log_level: str = "INFO", log_file: str | None = "logs/automator.log", console: bool = True
) -> logging.Logger:
    """
    设置日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，None 表示不写入文件
        console: 是否输出到控制台

    Returns:
        配置好的 logger 实例
    """
    # 创建日志目录
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

    # 获取根 logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有的 handlers
    logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 文件 handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 控制台 handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info(f"日志系统初始化完成 - 级别: {log_level}")
    if log_file:
        logger.info(f"日志文件: {log_file}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger

    Args:
        name: logger 名称

    Returns:
        logger 实例
    """
    return logging.getLogger(name)
