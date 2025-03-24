import datetime
import pandas as pd
import numpy as np
import requests
import os
import json
import time
import glob
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, List, Any, Tuple
from utils.logger import Logger

logger = Logger.get_logger()
# -------------------------------- 时间处理相关 --------------------------------


def get_hour() -> str:
    """
    获取当前时间(时:分:秒)

    Returns:
        str: 当前时间字符串
    """
    try:
        return datetime.now().strftime("%H:%M:%S")
    except Exception as e:
        logger.error(f"Failed to get current hour: {e}")
        return ""


def date_to_str(date: datetime.date) -> str:
    """
    日期转字符串

    Args:
        date: 日期对象

    Returns:
        str: 日期字符串(YYYY-MM-DD)
    """
    try:
        return date.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Failed to convert date to string: {e}")
        return ""


def str_to_date(date_str: str) -> datetime.date:
    """
    字符串转日期

    Args:
        date_str: 日期字符串(YYYY-MM-DD)

    Returns:
        datetime.date: 日期对象
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception as e:
        logger.error(f"Failed to convert string to date: {e}")
        return None


def timestamp_to_datetime(
    timestamp: Union[int, float], unit: str = "ms"
) -> datetime | None:
    """
    时间戳转datetime

    Args:
        timestamp: 时间戳
        unit: 单位(s/ms/us/ns)

    Returns:
        datetime: datetime对象
    """
    try:
        if unit == "ms":
            return datetime.fromtimestamp(timestamp / 1000)
        elif unit == "us":
            return datetime.fromtimestamp(timestamp / 1000000)
        elif unit == "ns":
            return datetime.fromtimestamp(timestamp / 1000000000)
        else:
            return datetime.fromtimestamp(timestamp)
    except Exception as e:
        logger.error(f"Failed to convert timestamp to datetime: {e}")
        return None


def datetime_to_timestamp(dt: datetime, unit: str = "ms") -> int:
    """
    datetime转时间戳

    Args:
        dt: datetime对象
        unit: 单位(s/ms/us/ns)

    Returns:
        int: 时间戳
    """
    try:
        timestamp = int(dt.timestamp())
        if unit == "ms":
            return timestamp * 1000
        elif unit == "us":
            return timestamp * 1000000
        elif unit == "ns":
            return timestamp * 1000000000
        else:
            return timestamp
    except Exception as e:
        logger.error(f"Failed to convert datetime to timestamp: {e}")
        return 0


def interval_timestamps(
    start_time: Union[str, datetime], end_time: Union[str, datetime], interval: str
) -> List[int]:
    """
    获取时间区间内的所有时间戳

    Args:
        start_time: 开始时间
        end_time: 结束时间
        interval: 时间间隔(1m/3m/5m/15m/30m/1h/2h/4h/6h/8h/12h/1d/3d/1w/1M)

    Returns:
        List[int]: 时间戳列表
    """
    try:
        # 转换为datetime
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

        # 解析间隔
        interval_map = {
            "m": "minutes",
            "h": "hours",
            "d": "days",
            "w": "weeks",
            "M": "months",
        }

        unit = interval[-1]
        value = int(interval[:-1])

        if unit not in interval_map:
            raise ValueError(f"Invalid interval: {interval}")

        # 生成时间戳
        timestamps = []
        current = start_time

        while current <= end_time:
            timestamps.append(datetime_to_timestamp(current))
            kwargs = {interval_map[unit]: value}
            current += timedelta(**kwargs)

        return timestamps
    except Exception as e:
        logger.error(f"Failed to get interval timestamps: {e}")
        return []


def parse_timeframe(timeframe: str) -> int:
    """
    解析时间周期

    Args:
        timeframe: 时间周期字符串(1m/3m/5m/15m/30m/1h/2h/4h/6h/8h/12h/1d/3d/1w/1M)

    Returns:
        int: 分钟数
    """
    try:
        unit = timeframe[-1]
        value = int(timeframe[:-1])

        if unit == "m":
            return value
        elif unit == "h":
            return value * 60
        elif unit == "d":
            return value * 1440
        elif unit == "w":
            return value * 10080
        elif unit == "M":
            return value * 43200
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")
    except Exception as e:
        logger.error(f"Failed to parse timeframe: {e}")
        return 0
