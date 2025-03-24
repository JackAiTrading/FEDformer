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
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod
from binance.enums import (
    ORDER_TYPE_MARKET,
    ORDER_TYPE_LIMIT,
    TIME_IN_FORCE_GTC,
    SIDE_SELL,
    SIDE_BUY
)


class ClientInterface(ABC):
    """币安客户端"""

    def __init__(self, config: Dict[str, any] = None):
        """
        初始化 客户端

        Args:
            :param config 配制
        """
        # 基础配置
        self._config = config

    @abstractmethod
    def init_websocket(self, message_handler=None):
        """
        初始化WebSocket连接

        Args:
            message_handler: 消息处理函数
        """
        pass

    @abstractmethod
    def subscribe_kline(self, symbol: str, interval: str, callback=None):
        """
        订阅K线数据

        Args:
            symbol: 交易对
            interval: 时间间隔
            callback: 回调函数
        """
        pass

    @abstractmethod
    def get_listen_key(self) -> str:
        """
        获取WebSocket listenKey

        Returns:
            str: listenKey
        """
        pass

    @abstractmethod
    def keep_alive_listen_key(self):
        """延长listenKey有效期"""
        pass

    @abstractmethod
    def set_leverage(self, symbol: str, leverage: int):
        """
        设置杠杆倍数

        Args:
            symbol: 交易对
            leverage: 杠杆倍数
        """
        pass

    @abstractmethod
    def set_margin_type(self, symbol: str, margin_type: str):
        """
        设置保证金类型

        Args:
            symbol: 交易对
            margin_type: 保证金类型 (ISOLATED/CROSSED)
        """
        pass

    @abstractmethod
    def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取持仓风险

        Args:
            symbol: 交易对

        Returns:
            List[Dict]: 持仓风险信息
        """
        pass

    @abstractmethod
    def get_account_info(self) -> Dict:
        """
        获取账户信息

        Returns:
            Dict: 账户信息
        """
        pass

    @abstractmethod
    def get_balance(self) -> List[Dict]:
        """
        获取账户余额

        Returns:
            List[Dict]: 余额信息
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """
        取消订单

        Args:
            symbol: 交易对
            order_id: 订单ID

        Returns:
            Dict: 取消结果
        """
        pass

    @abstractmethod
    def cancel_all_orders(self, symbol: str) -> List[Dict]:
        """
        取消所有订单

        Args:
            symbol: 交易对

        Returns:
            List[Dict]: 取消结果
        """
        pass

    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取未完成订单

        Args:
            symbol: 交易对

        Returns:
            List[Dict]: 订单列表
        """
        pass

    @abstractmethod
    def get_order(self, symbol: str, order_id: int) -> Dict:
        """
        获取订单信息

        Args:
            symbol: 交易对
            order_id: 订单ID

        Returns:
            Dict: 订单信息
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_mark_price(self, symbol: Optional[str] = None) -> Dict:
        """
        获取标记价格

        Args:
            symbol: 交易对

        Returns:
            Dict: 标记价格信息
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def close_websocket(self):
        """关闭WebSocket连接"""
        pass

    @abstractmethod
    def get_symbol_price(self, symbol: str) -> float:
        """
        获取交易对当前价格

        Args:
            symbol: 交易对

        Returns:
            float: 当前价格
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def place_order(
            self,
            symbol: str,
            side: str,
            type2: str,
            quantity: float,
            price: float = None
    ) -> dict:
        """
        下单

        Args:
            symbol: 交易对
            side: 买卖方向
            type2: 订单类型
            quantity: 数量
            price: 价格（市价单可为None）

        Returns:
            dict: 订单信息
        """
        pass

    @abstractmethod
    def cancel_order_spot(self, symbol: str, order_id: str) -> dict:
        """
        取消订单

        Args:
            symbol: 交易对
            order_id: 订单ID

        Returns:
            dict: 取消结果
        """
        pass

    @abstractmethod
    def get_open_orders_spot(self, symbol: str = None) -> list:
        """
        获取未完成订单

        Args:
            symbol: 交易对（可选）

        Returns:
            list: 订单列表
        """
        pass

    @abstractmethod
    def get_order_status(self, symbol: str, order_id: str) -> dict:
        """
        获取订单状态

        Args:
            symbol: 交易对
            order_id: 订单ID

        Returns:
            dict: 订单信息
        """
        pass

    @abstractmethod
    def get_account(self) -> dict:
        """
        获取账户信息

        Returns:
            dict: 账户信息
        """
        pass
