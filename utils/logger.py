"""
日志管理模块

这个模块提供了统一的日志管理功能，支持将日志同时输出到文件和控制台。
主要功能包括：
- 日志格式化
- 文件日志
- 控制台日志
- 日志级别管理

使用示例：
```python
from utils.logger import Logger

logger = Logger.get_logger()
logger.info('Starting trading...')
```

主要组件：
- Logger: 日志管理类
  - 配置日志格式和输出
  - 管理日志文件
  - 提供统一的日志接口
"""

import logging
from datetime import datetime
import os

class Logger:
    """日志管理类"""
    
    _logger = None
    
    @classmethod
    def get_logger(cls):
        """获取日志器单例"""
        if cls._logger is None:
            cls._logger = cls.setup_logger()
        return cls._logger
    
    @staticmethod
    def setup_logger(name: str = None, 
                    level: int = logging.INFO,
                    log_dir: str = "resource/logs"):
        """设置日志器"""
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        logger = logging.getLogger(name or __name__)
        logger.setLevel(level)
        
        # 如果已经有处理器，不再添加
        if logger.handlers:
            return logger
        
        # 文件处理器
        log_file = os.path.join(log_dir, f'trading2_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
