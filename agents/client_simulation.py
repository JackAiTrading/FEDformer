
"""
币安模拟客户端模块

这个模块提供了模拟币安交易所交互的接口（用于模拟交易）。
主要功能：
- 模拟市场数据
- 模拟订单管理
- 模拟账户信息
- 交易记录
"""

import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from decimal import Decimal

import pandas as pd
import numpy as np

from agents.client_interface import ClientInterface
from utils.logger import Logger
from const.const import Fee, USDT
from binance.enums import (
    ORDER_TYPE_MARKET,
    ORDER_TYPE_LIMIT,
    TIME_IN_FORCE_GTC,
    SIDE_SELL,
    SIDE_BUY
)

logger = Logger.get_logger()

class ClientSimulation(ClientInterface):
    """币安模拟客户端"""

    def __init__(self,config: Dict[str, any] = None):
        """
        初始化模拟客户端
        
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

        # 交易配置
        self.default_leverage = config['leverage']  # 默认杠杆
        self.default_margin_type = config['margin_type']  # 默认保证金类型 ISOLATED/CROSSED
        
        # 账户状态
        self.balance = config['initial_balance']
        self.positions = {}  # 当前持仓
        self.orders = []     # 订单历史
        self.trades = []     # 交易历史
        
        # 市场数据
        self.market_prices = {}  # 当前市场价格
        self.klines_data = {}    # K线数据缓存
        
        logger.info(f"模拟客户端初始化完成，初始余额: {self.balance} USDT")
        
    def set_leverage(self, symbol: str, leverage: int):
        """设置杠杆倍数"""
        self.leverage = leverage
        logger.info(f"设置 {symbol} 杠杆倍数为 {leverage}x")
        return {'leverage': leverage}
        
    def set_margin_type(self, symbol: str, margin_type: str):
        """设置保证金类型"""
        self.margin_type = margin_type
        logger.info(f"设置 {symbol} 保证金类型为 {margin_type}")
        return {'marginType': margin_type}
        
    def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict]:
        """获取持仓风险"""
        positions = []
        for sym, pos in self.positions.items():
            if symbol is None or sym == symbol:
                positions.append({
                    'symbol': sym,
                    'positionAmt': pos['size'],
                    'entryPrice': pos['entry_price'],
                    'markPrice': self.market_prices.get(sym, pos['entry_price']),
                    'unRealizedProfit': self._calculate_unrealized_pnl(sym),
                    'liquidationPrice': self._calculate_liquidation_price(sym),
                    'leverage': self.leverage,
                    'marginType': self.margin_type
                })
        return positions

    def keep_alive_listen_key(self):
        pass

    def get_listen_key(self) -> str:
        pass

    def subscribe_kline(self, symbol: str, interval: str, callback=None):
        pass

    def init_websocket(self, message_handler=None):
        pass

    def get_klines(self, symbol: str, interval: str, limit: int = 500, start_time: Optional[int] = None,
                   end_time: Optional[int] = None) -> List[List]:
        pass

    def get_mark_price(self, symbol: Optional[str] = None) -> Dict:
        pass

    def get_funding_rate(self, symbol: str, limit: int = 100, start_time: Optional[int] = None,
                         end_time: Optional[int] = None) -> List[Dict]:
        pass

    def close_websocket(self):
        pass

    def get_symbol_price(self, symbol: str) -> float:
        pass

    def get_klines_spot(self, symbol: str, interval: str, limit: int = 100) -> list:
        pass

    def place_order(self, symbol: str, side: str, type2: str, quantity: float, price: float = None) -> dict:
        pass

    def cancel_order_spot(self, symbol: str, order_id: str) -> dict:
        pass

    def get_open_orders_spot(self, symbol: str = None) -> list:
        pass

    def get_order_status(self, symbol: str, order_id: str) -> dict:
        pass

    def get_account(self) -> dict:
        pass

    def cancel_all_orders(self, symbol: str) -> List[Dict]:
        pass
        
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        return {
            'totalWalletBalance': self.balance,
            'totalUnrealizedProfit': self._calculate_total_unrealized_pnl(),
            'totalMarginBalance': self.balance + self._calculate_total_unrealized_pnl(),
            'availableBalance': self._calculate_available_balance(),
            'positions': self.get_position_risk()
        }
        
    def get_balance(self) -> List[Dict]:
        """获取账户余额"""
        return [{
            'asset': USDT,
            'balance': str(self.balance),
            'crossWalletBalance': str(self.balance),
            'crossUnPnl': str(self._calculate_total_unrealized_pnl())
        }]
        
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: bool = False
    ) -> Dict:
        """下市价单"""
        # 获取当前价格
        price = self.market_prices.get(symbol)
        if not price:
            logger.error(f"未找到 {symbol} 的价格数据")
            return {}
            
        # 生成订单ID
        order_id = str(uuid.uuid4())
        
        # 创建订单记录
        order = {
            'orderId': order_id,
            'symbol': symbol,
            'side': side,
            'type': ORDER_TYPE_MARKET,
            'quantity': quantity,
            'price': price,
            'reduceOnly': reduce_only,
            'status': 'FILLED',
            'time': int(datetime.now().timestamp() * 1000)
        }
        
        # 更新持仓
        self._update_position(symbol, side, quantity, price)
        
        # 记录订单和交易
        self.orders.append(order)
        self.trades.append({
            'symbol': symbol,
            'id': str(uuid.uuid4()),
            'orderId': order_id,
            'side': side,
            'price': price,
            'quantity': quantity,
            'commission': self._calculate_commission(price * quantity),
            'time': order['time']
        })
        
        return order
        
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = 'GTC',
        reduce_only: bool = False
    ) -> Dict:
        """下限价单"""
        # 生成订单ID
        order_id = str(uuid.uuid4())
        
        # 创建订单记录
        order = {
            'orderId': order_id,
            'symbol': symbol,
            'side': side,
            'type': ORDER_TYPE_LIMIT,
            'quantity': quantity,
            'price': price,
            'timeInForce': time_in_force,
            'reduceOnly': reduce_only,
            'status': 'NEW',
            'time': int(datetime.now().timestamp() * 1000)
        }
        
        # 记录订单
        self.orders.append(order)
        
        return order
        
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """取消订单"""
        for order in self.orders:
            if str(order['orderId']) == str(order_id) and order['symbol'] == symbol:
                if order['status'] == 'NEW':
                    order['status'] = 'CANCELED'
                    return order
        return {}
        
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """获取未完成订单"""
        return [
            order for order in self.orders
            if (symbol is None or order['symbol'] == symbol) and order['status'] == 'NEW'
        ]
        
    def get_order(self, symbol: str, order_id: int) -> Dict:
        """获取订单信息"""
        for order in self.orders:
            if str(order['orderId']) == str(order_id) and order['symbol'] == symbol:
                return order
        return {}
        
    def get_all_orders(
        self,
        symbol: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict]:
        """获取所有订单"""
        orders = [order for order in self.orders if order['symbol'] == symbol]
        
        if start_time:
            orders = [order for order in orders if order['time'] >= start_time]
        if end_time:
            orders = [order for order in orders if order['time'] <= end_time]
            
        return orders[-limit:]
        
    def update_market_price(self, symbol: str, price: float):
        """更新市场价格"""
        self.market_prices[symbol] = price
        
        # 检查限价单是否可以成交
        self._check_limit_orders(symbol, price)
        
    def _check_limit_orders(self, symbol: str, price: float):
        """检查限价单是否可以成交"""
        for order in self.orders:
            if (order['symbol'] == symbol and 
                order['status'] == 'NEW' and 
                order['type'] == ORDER_TYPE_LIMIT):
                
                if (order['side'] == SIDE_BUY and price <= order['price']) or \
                   (order['side'] == SIDE_SELL and price >= order['price']):
                    # 限价单成交
                    order['status'] = 'FILLED'
                    self._update_position(
                        symbol,
                        order['side'],
                        order['quantity'],
                        order['price']
                    )
                    
                    # 记录成交
                    self.trades.append({
                        'symbol': symbol,
                        'id': str(uuid.uuid4()),
                        'orderId': order['orderId'],
                        'side': order['side'],
                        'price': order['price'],
                        'quantity': order['quantity'],
                        'commission': self._calculate_commission(
                            order['price'] * order['quantity']
                        ),
                        'time': int(datetime.now().timestamp() * 1000)
                    })
        
    def _update_position(self, symbol: str, side: str, quantity: float, price: float):
        """更新持仓信息"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'size': 0,
                'entry_price': 0
            }
            
        position = self.positions[symbol]
        old_size = position['size']
        
        # 更新持仓数量
        if side == SIDE_BUY:
            new_size = old_size + quantity
        else:  # SELL
            new_size = old_size - quantity
            
        # 如果持仓方向改变或持仓为0，重置入场价格
        if (old_size * new_size <= 0) or new_size == 0:
            position['entry_price'] = price if new_size != 0 else 0
        else:
            # 计算新的入场价格（按数量加权平均）
            position['entry_price'] = (
                (abs(old_size) * position['entry_price'] + quantity * price) /
                abs(new_size)
            )
            
        position['size'] = new_size
        
        # 更新余额（扣除手续费）
        commission = self._calculate_commission(price * quantity)
        self.balance -= commission
        
        logger.info(f"更新持仓 {symbol}: 数量={new_size}, 入场价格={position['entry_price']:.2f}")
        
    def _calculate_commission(self, order_value: float) -> float:
        """计算手续费"""
        return order_value * Fee.Taker
        
    def _calculate_unrealized_pnl(self, symbol: str) -> float:
        """计算未实现盈亏"""
        position = self.positions.get(symbol)
        if not position or position['size'] == 0:
            return 0
            
        current_price = self.market_prices.get(symbol, position['entry_price'])
        pnl = (current_price - position['entry_price']) * position['size']
        return pnl
        
    def _calculate_total_unrealized_pnl(self) -> float:
        """计算总未实现盈亏"""
        return sum(self._calculate_unrealized_pnl(symbol) for symbol in self.positions)
        
    def _calculate_available_balance(self) -> float:
        """计算可用余额"""
        used_margin = sum(
            abs(pos['size'] * self.market_prices.get(sym, pos['entry_price'])) / self.leverage
            for sym, pos in self.positions.items()
        )
        return self.balance - used_margin
        
    def _calculate_liquidation_price(self, symbol: str) -> float:
        """计算清算价格"""
        position = self.positions.get(symbol)
        if not position or position['size'] == 0:
            return 0
            
        # 简化的清算价格计算
        maintenance_margin_rate = 0.004  # 维持保证金率
        entry_price = position['entry_price']
        size = position['size']
        
        if size > 0:
            return entry_price * (1 - 1/self.leverage + maintenance_margin_rate)
        else:
            return entry_price * (1 + 1/self.leverage - maintenance_margin_rate)