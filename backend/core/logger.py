"""
日志配置模块
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime


def setup_logger(name: str = "skills") -> logging.Logger:
    """
    配置并返回日志记录器

    日志输出到：
    1. 控制台（INFO 级别）
    2. logs/skills.log（按大小轮转）
    3. logs/error.log（仅错误，按时间轮转）
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 确保 logs 目录存在
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # 2. 文件轮转（按大小）
    file_handler = RotatingFileHandler(
        log_dir / "skills.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 3. 错误日志单独记录（按时间）
    error_handler = TimedRotatingFileHandler(
        log_dir / "error.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.suffix = "%Y-%m-%d"
    logger.addHandler(error_handler)

    return logger


# 创建全局日志实例
logger = setup_logger()


class LogContext:
    """日志上下文管理器，用于添加额外的上下文信息"""

    def __init__(self, **kwargs):
        self.extra = kwargs

    def __enter__(self):
        for key, value in self.extra.items():
            logger = logging.getLogger("skills")
            old_factory = logger_factory = logger.makeRecord

            def custom_factory(*args, **kwargs):
                record = old_factory(*args, **kwargs)
                for k, v in self.extra.items():
                    setattr(record, k, v)
                return record

            logger.makeRecord = custom_factory
        return self

    def __exit__(self, *args):
        pass
