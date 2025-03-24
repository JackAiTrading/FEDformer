"""
币安客户端模块

这个模块提供了与币安交易所交互的接口。
主要功能：
- 市场数据获取
- 订单管理
- 账户信息查询
- WebSocket实时数据
- 期货交易
"""

import json
import uuid
from datetime import datetime
from time import sleep, time_ns
from typing import Optional, Dict, List, Any

import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.um_futures import UMFutures
from binance.enums import (
    ORDER_TYPE_MARKET,
    ORDER_TYPE_LIMIT,
    TIME_IN_FORCE_GTC,
    SIDE_SELL,
    SIDE_BUY
)
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient

from agents.client_interface import ClientInterface
from utils.logger import Logger

logger = Logger.get_logger()


class ClientBinance(ClientInterface):
    """币安客户端"""

    def __init__(self, config: Dict[str, any] = None):
        """
        初始化 客户端

        Args:
            :param config 配制
        """
        super().__init__(config=config)

        # binance配置
        self.api_key = config['binance']['api_key']
        self.api_secret = config['binance']['api_secret']
        self.testnet = config['binance']['testnet']

        # 基础配置
        self.window_size = config['window_size']

        # 合约客户端
        self.futures_client = UMFutures(key=self.api_key,secret=self.api_secret,testnet=self.testnet)

        # WebSocket客户端
        self.ws_client = None
        self.listen_key = None

        # 交易配置
        self.default_leverage = config['leverage']  # 默认杠杆
        self.default_margin_type = config['margin_type']  # 默认保证金类型 ISOLATED/CROSSED

    def init_websocket(self, message_handler=None):
        """
        初始化WebSocket连接
        
        Args:
            message_handler: 消息处理函数
        """
        if message_handler:
            self.ws_client = UMFuturesWebsocketClient(
                on_message=message_handler
            )
        else:
            self.ws_client = UMFuturesWebsocketClient(
                on_message=self._default_message_handler
            )

    @staticmethod
    def _default_message_handler(self, _, message):
        """默认WebSocket消息处理"""
        logger.debug(f"Received message: {message}")

    def subscribe_kline(self, symbol: str, interval: str, callback=None):
        """
        订阅K线数据
        
        Args:
            symbol: 交易对
            interval: 时间间隔
            callback: 回调函数
        """
        if not self.ws_client:
            self.init_websocket(callback)
        self.ws_client.KLine(
            symbol=symbol,
            interval=interval
        )

    def get_listen_key(self) -> str:
        """
        获取WebSocket listenKey
        
        Returns:
            str: listenKey
        """
        try:
            response = self.futures_client.new_listen_key()
            self.listen_key = response['listenKey']
            return self.listen_key
        except Exception as e:
            logger.error(f"Failed to get listen key: {e}")
            return ""

    def keep_alive_listen_key(self):
        """延长listenKey有效期"""
        if self.listen_key:
            try:
                self.futures_client.renew_listen_key(
                    listenKey=self.listen_key
                )
                logger.info(f"Successfully renewed listen key: {self.listen_key}")
            except Exception as e:
                logger.error(f"Failed to renew listen key: {e}")

    def set_leverage(self, symbol: str, leverage: int):
        """
        设置杠杆倍数
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数
        """
        try:
            self.futures_client.change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            logger.info(f"Set leverage to {leverage}x for {symbol}")
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")

    def set_margin_type(self, symbol: str, margin_type: str):
        """
        设置保证金类型
        
        Args:
            symbol: 交易对
            margin_type: 保证金类型 (ISOLATED/CROSSED)
        """
        try:
            self.futures_client.change_margin_type(
                symbol=symbol,
                marginType=margin_type
            )
            logger.info(f"Set margin type to {margin_type} for {symbol}")
        except Exception as e:
            logger.error(f"Failed to set margin type: {e}")

    def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取持仓风险
        
        Args:
            symbol: 交易对
            
        Returns:
            List[Dict]: 持仓风险信息
        """
        try:
            return self.futures_client.get_position_risk(symbol=symbol)
        except Exception as e:
            logger.error(f"Failed to get position risk: {e}")
            return []

    def get_account_info(self) -> Dict:
        """
        获取账户信息
        
        Returns:
            Dict: 账户信息
        """
        try:
            return self.futures_client.account()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {}

    def get_balance(self) -> List[Dict]:
        """
        获取账户余额
        
        Returns:
            List[Dict]: 余额信息
        """
        try:
            return self.futures_client.balance()
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return []

    def place_market_order(
            self,
            symbol: str,
            side: str,
            quantity: float,
            reduce_only: bool = False
    ) -> Dict:
        """
        下市价单
        
        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            quantity: 数量
            reduce_only: 是否只减仓
            
        Returns:
            Dict: 订单信息
        """
        try:
            return self.futures_client.new_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity,
                reduceOnly=reduce_only
            )
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            return {}

    def place_limit_order(
            self,
            symbol: str,
            side: str,
            quantity: float,
            price: float,
            time_in_force: str = TIME_IN_FORCE_GTC,
            reduce_only: bool = False
    ) -> Dict:
        """
        下限价单
        
        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            quantity: 数量
            price: 价格
            time_in_force: 有效期
            reduce_only: 是否只减仓
            
        Returns:
            Dict: 订单信息
        """
        try:
            return self.futures_client.new_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=time_in_force,
                quantity=quantity,
                price=price,
                reduceOnly=reduce_only
            )
        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            return {}

    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """
        取消订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            Dict: 取消结果
        """
        try:
            return self.futures_client.cancel_order(
                symbol=symbol,
                orderId=order_id
            )
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return {}

    def cancel_all_orders(self, symbol: str) -> List[Dict]:
        """
        取消所有订单
        
        Args:
            symbol: 交易对
            
        Returns:
            List[Dict]: 取消结果
        """
        try:
            return self.futures_client.cancel_open_orders(
                symbol=symbol
            )
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return []

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取未完成订单
        
        Args:
            symbol: 交易对
            
        Returns:
            List[Dict]: 订单列表
        """
        try:
            return self.futures_client.get_open_orders(symbol=symbol)
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []

    def get_order(self, symbol: str, order_id: int) -> Dict:
        """
        获取订单信息
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            Dict: 订单信息
        """
        try:
            return self.futures_client.get_order(
                symbol=symbol,
                orderId=order_id
            )
        except Exception as e:
            logger.error(f"Failed to get order: {e}")
            return {}

    def get_all_orders(
            self,
            symbol: str,
            limit: int = 500,
            start_time: Optional[int] = None,
            end_time: Optional[int] = None
    ) -> List[Dict]:
        """
        获取所有订单
        
        Args:
            symbol: 交易对
            limit: 返回数量限制
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Dict]: 订单列表
        """
        try:
            params = {
                'symbol': symbol,
                'limit': limit
            }
            if start_time:
                params['startTime'] = start_time
            if end_time:
                params['endTime'] = end_time

            return self.futures_client.get_all_orders(**params)
        except Exception as e:
            logger.error(f"Failed to get all orders: {e}")
            return []

    def get_klines(
            self,
            symbol: str,
            interval: str,
            limit: int = 500,
            start_time: Optional[int] = None,
            end_time: Optional[int] = None
    ) -> List[List]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: 时间间隔
            limit: 返回数量限制
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[List]: K线数据
        """
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            if start_time:
                params['startTime'] = start_time
            if end_time:
                params['endTime'] = end_time

            return self.futures_client.klines(**params)
        except Exception as e:
            logger.error(f"Failed to get klines: {e}")
            return []

    def get_mark_price(self, symbol: Optional[str] = None) -> Dict:
        """
        获取标记价格
        
        Args:
            symbol: 交易对
            
        Returns:
            Dict: 标记价格信息
        """
        try:
            return self.futures_client.mark_price(symbol=symbol)
        except Exception as e:
            logger.error(f"Failed to get mark price: {e}")
            return {} if symbol else []

    def get_funding_rate(
            self,
            symbol: str,
            limit: int = 100,
            start_time: Optional[int] = None,
            end_time: Optional[int] = None
    ) -> List[Dict]:
        """
        获取资金费率历史
        
        Args:
            symbol: 交易对
            limit: 返回数量限制
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Dict]: 资金费率数据
        """
        try:
            params = {
                'symbol': symbol,
                'limit': limit
            }
            if start_time:
                params['startTime'] = start_time
            if end_time:
                params['endTime'] = end_time

            return self.futures_client.funding_rate(**params)
        except Exception as e:
            logger.error(f"Failed to get funding rate: {e}")
            return []

    def close_websocket(self):
        """关闭WebSocket连接"""
        if self.ws_client:
            self.ws_client.stop()
            self.ws_client = None

    def get_symbol_price(self, symbol: str) -> float:
        """
        获取交易对当前价格
        
        Args:
            symbol: 交易对
            
        Returns:
            float: 当前价格
        """
        try:
            ticker = self.spot_client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Failed to get price: {e}")
            return 0.0

    def get_klines_spot(
            self,
            symbol: str,
            interval: str,
            limit: int = 100
    ) -> list:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: 时间间隔
            limit: 数据条数
            
        Returns:
            list: K线数据列表
        """
        try:
            klines = self.spot_client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            return klines
        except BinanceAPIException as e:
            logger.error(f"Failed to get klines: {e}")
            return []

    def place_order(
            self,
            symbol: str,
            side: str,
            type: str,
            quantity: float,
            price: float = None
    ) -> dict:
        """
        下单
        
        Args:
            symbol: 交易对
            side: 买卖方向
            type: 订单类型
            quantity: 数量
            price: 价格（市价单可为None）
            
        Returns:
            dict: 订单信息
        """
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': type,
                'quantity': quantity
            }

            if price is not None:
                params['price'] = price

            return self.futures_client.create_order(**params)
        except BinanceAPIException as e:
            logger.error(f"Failed to place order: {e}")
            return {}

    def cancel_order_spot(self, symbol: str, order_id: str) -> dict:
        """
        取消订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            dict: 取消结果
        """
        try:
            return self.client.cancel_order(
                symbol=symbol,
                orderId=order_id
            )
        except BinanceAPIException as e:
            logger.error(f"Failed to cancel order: {e}")
            return {}

    def get_open_orders_spot(self, symbol: str = None) -> list:
        """
        获取未完成订单
        
        Args:
            symbol: 交易对（可选）
            
        Returns:
            list: 订单列表
        """
        try:
            return self.spot_client.get_open_orders(symbol=symbol)
        except BinanceAPIException as e:
            logger.error(f"Failed to get open orders: {e}")
            return []

    def get_order_status(self, symbol: str, order_id: str) -> dict:
        """
        获取订单状态
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            dict: 订单信息
        """
        try:
            return self.spot_client.get_order(
                symbol=symbol,
                orderId=order_id
            )
        except BinanceAPIException as e:
            logger.error(f"Failed to get order status: {e}")
            return {}

    def get_account(self) -> dict:
        """
        获取账户信息
        
        Returns:
            dict: 账户信息
        """
        try:
            return self.spot_client.get_account()
        except BinanceAPIException as e:
            logger.error(f"Failed to get account info: {e}")
            return {}
