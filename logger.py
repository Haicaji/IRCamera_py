"""
IR Camera Viewer - 红外摄像头查看器

日志模块
"""

import logging
import sys
from datetime import datetime


def setup_logger(name: str = "IRCamera", level: int = logging.INFO) -> logging.Logger:
    """设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 格式化器
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


# 全局日志实例
logger = setup_logger()


def log_info(message: str):
    """记录信息日志"""
    logger.info(message)


def log_warning(message: str):
    """记录警告日志"""
    logger.warning(message)


def log_error(message: str):
    """记录错误日志"""
    logger.error(message)


def log_debug(message: str):
    """记录调试日志"""
    logger.debug(message)
