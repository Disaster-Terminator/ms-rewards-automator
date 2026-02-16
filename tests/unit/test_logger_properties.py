"""
日志系统属性测试
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.logger import setup_logging


@given(log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]))
@settings(max_examples=50)
def test_property_logging_completeness(log_level):
    """
    属性 17: 操作日志完整性
    验证需求: 9.1, 9.3

    属性: 对于任何有效的日志级别，日志系统应该能够正确初始化并记录消息
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")

        # 设置日志系统
        logger = setup_logging(log_level=log_level, log_file=log_file, console=False)

        # 验证 logger 已配置
        assert logger is not None
        assert logger.level == getattr(logging, log_level.upper())

        # 记录不同级别的消息
        test_message = f"Test message at {log_level}"
        logger.debug(f"DEBUG: {test_message}")
        logger.info(f"INFO: {test_message}")
        logger.warning(f"WARNING: {test_message}")
        logger.error(f"ERROR: {test_message}")
        logger.critical(f"CRITICAL: {test_message}")

        # 刷新并关闭所有 handlers
        for handler in logger.handlers[:]:
            handler.flush()
            handler.close()
            logger.removeHandler(handler)

        # 验证日志文件存在
        assert os.path.exists(log_file)

        # 读取日志内容
        with open(log_file, encoding="utf-8") as f:
            log_content = f.read()

        # 验证至少记录了一些消息
        assert len(log_content) > 0

        # 根据日志级别验证消息
        level_hierarchy = {
            "DEBUG": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "INFO": ["INFO", "WARNING", "ERROR", "CRITICAL"],
            "WARNING": ["WARNING", "ERROR", "CRITICAL"],
            "ERROR": ["ERROR", "CRITICAL"],
            "CRITICAL": ["CRITICAL"],
        }

        expected_levels = level_hierarchy[log_level]
        for level in expected_levels:
            assert level in log_content


@given(
    message=st.text(
        min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=("Cc", "Cs"))
    )
)
@settings(max_examples=50)
def test_property_log_message_persistence(message):
    """
    属性: 日志消息持久化

    属性: 记录的日志消息应该能够被写入文件并正确读取
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")

        logger = setup_logging(log_level="INFO", log_file=log_file, console=False)

        # 记录消息
        logger.info(message)

        # 刷新并关闭所有 handlers
        for handler in logger.handlers[:]:
            handler.flush()
            handler.close()
            logger.removeHandler(handler)

        # 读取日志文件
        with open(log_file, encoding="utf-8") as f:
            log_content = f.read()

        # 验证消息在日志中（排除控制字符）
        assert message in log_content or len(message.strip()) == 0
