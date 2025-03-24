"""
通用工具模块

主要功能：
- 数据处理
- 时间处理
- 文件操作
- 数值计算
- API请求
"""

import json
import time
from typing import Optional, Union, Dict, List, Any, Tuple

from utils.logger import Logger

logger = Logger.get_logger()


# -------------------------------- 其他工具函数 --------------------------------


def singleton(cls):
    """
    单例模式装饰器

    Args:
        cls: 类

    Returns:
        function: 获取实例的函数
    """
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def format_number(
    number: float, precision: int = 8, remove_trailing_zeros: bool = True
) -> str:
    """
    格式化数字

    Args:
        number: 数字
        precision: 精度
        remove_trailing_zeros: 是否移除尾部的0

    Returns:
        str: 格式化后的字符串
    """
    try:
        format_str = f"{{:.{precision}f}}"
        result = format_str.format(number)

        if remove_trailing_zeros:
            if "." in result:
                result = result.rstrip("0").rstrip(".")

        return result
    except Exception as e:
        logger.error(f"Failed to format number: {e}")
        return ""


def retry(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    函数重试装饰器

    Args:
        func: 要重试的函数
        max_retries: 最大重试次数
        delay: 初始延迟时间(秒)
        backoff: 延迟时间的增长系数
        exceptions: 需要重试的异常类型

    Returns:
        Any: 函数返回值
    """

    def wrapper(*args, **kwargs):
        retries = 0
        cur_delay = delay

        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                retries += 1
                if retries == max_retries:
                    raise e

                logger.warning(
                    f"Retry {retries}/{max_retries} for {func.__name__} "
                    f"after {cur_delay}s due to {str(e)}"
                )

                time.sleep(cur_delay)
                cur_delay *= backoff

    return wrapper


def load_json(file_path: str) -> Dict:
    """
    加载JSON文件

    Args:
        file_path: 文件路径

    Returns:
        Dict: JSON数据
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        return {}
