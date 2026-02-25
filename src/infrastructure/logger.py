"""
日志系统模块
配置和管理应用程序日志，支持结构化 JSON 格式
"""

import json
import logging
from pathlib import Path


class StructuredJsonFormatter(logging.Formatter):
    """结构化 JSON 日志格式化器（用于文件日志，供 Agent 解析）"""

    def __init__(self, datefmt: str | None = None):
        super().__init__(datefmt=datefmt)
        self.datefmt = datefmt or "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # 从 record.__dict__ 中提取非标准字段作为 extra
        standard_fields = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
            "asctime",
        }
        extra = {
            k: v
            for k, v in record.__dict__.items()
            if k not in standard_fields and k not in log_entry
        }
        if extra:
            log_entry["extra"] = extra

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class StandardFormatter(logging.Formatter):
    """标准文本日志格式化器（用于控制台输出，人类可读）"""

    def __init__(self, datefmt: str | None = None):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt=datefmt or "%Y-%m-%d %H:%M:%S",
        )


def setup_logging(
    log_level: str = "INFO",
    log_file: str | None = "logs/automator.log",
    console: bool = True,
) -> logging.Logger:
    """
    设置日志系统

    文件日志使用 JSON 格式（结构化，供 Agent 解析）
    控制台日志使用标准文本格式（人类可读）

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，None 表示不写入文件
        console: 是否输出到控制台

    Returns:
        配置好的 logger 实例
    """
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    logger.handlers.clear()

    json_formatter = StructuredJsonFormatter()
    standard_formatter = StandardFormatter()

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(standard_formatter)
        logger.addHandler(console_handler)

    logger.info(f"日志系统初始化完成 - 级别: {log_level}")
    if log_file:
        logger.info(f"日志文件: {log_file} (JSON格式)")

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
