"""
币安数据收集器模块

这个模块负责从币安交易所收集市场数据。
主要功能：
- K线数据收集
- 实时价格订阅
- 交易深度数据收集
"""

import pandas as pd
from datetime import datetime
from typing import Optional, List
from binance.client import Client
from binance.exceptions import BinanceAPIException

from utils.logger import Logger

logger = Logger.get_logger()

class MarketDataBinance:
    """币安数据收集器"""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        初始化数据收集器
        
        Args:
            api_key: API密钥
            api_secret: API密钥
        """
        self.client = Client(api_key, api_secret)
        
    def get_klines(
            self,
            symbol: str,
            interval: str,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            limit: int = 500
        ) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: 时间间隔
            start_time: 开始时间
            end_time: 结束时间
            limit: 数据条数
            
        Returns:
            pd.DataFrame: K线数据
        """
        try:
            # 准备参数
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            if start_time:
                params["startTime"] = int(start_time.timestamp() * 1000)
            if end_time:
                params["endTime"] = int(end_time.timestamp() * 1000)
                
            # 获取数据
            klines = self.client.get_klines(**params)
            
            # 转换为DataFrame
            df = pd.DataFrame(
                klines,
                columns=[
                    'timestamp', 'open', 'high', 'low', 'close',
                    'volume', 'close_time', 'quote_volume',
                    'trades', 'taker_base_volume', 'taker_quote_volume',
                    'ignore'
                ]
            )
            
            # 处理时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            # 转换数值类型
            numeric_columns = [
                'open', 'high', 'low', 'close', 'volume',
                'quote_volume', 'taker_base_volume', 'taker_quote_volume'
            ]
            df[numeric_columns] = df[numeric_columns].astype(float)
            
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Failed to get klines: {e}")
            return pd.DataFrame()
            
    def get_recent_trades(
            self,
            symbol: str,
            limit: int = 512
        ) -> pd.DataFrame:
        """
        获取最近的交易
        
        Args:
            symbol: 交易对
            limit: 数据条数
            
        Returns:
            pd.DataFrame: 交易数据
        """
        try:
            trades = self.client.get_recent_trades(
                symbol=symbol,
                limit=limit
            )
            
            df = pd.DataFrame(trades)
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Failed to get recent trades: {e}")
            return pd.DataFrame()
            
    def get_order_book(
            self,
            symbol: str,
            limit: int = 100
        ) -> dict:
        """
        获取订单簿数据
        
        Args:
            symbol: 交易对
            limit: 深度
            
        Returns:
            dict: 订单簿数据
        """
        try:
            depth = self.client.get_order_book(
                symbol=symbol,
                limit=limit
            )
            return depth
            
        except BinanceAPIException as e:
            logger.error(f"Failed to get order book: {e}")
            return {}
