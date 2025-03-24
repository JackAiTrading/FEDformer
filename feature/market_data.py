"""
市场数据存储模块

这个模块负责管理和存储市场数据。
主要功能：
- 数据存储和读取
- 数据格式转换
- 数据缓存管理
"""

import pandas as pd
from typing import Optional, Dict
from datetime import datetime
import os
import json

from utils.logger import Logger

logger = Logger.get_logger()


class MarketData:
    """市场数据存储"""
    
    def __init__(self, base_dir: str):
        """
        初始化存储器
        
        Args:
            base_dir: 基础目录
        """
        self.base_dir = base_dir

        # 创建基础目录
        os.makedirs(base_dir, exist_ok=True)
