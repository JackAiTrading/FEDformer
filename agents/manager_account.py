"""
账户管理模块

这个模块负责管理交易账户。
主要功能：
- 账户余额管理
- 持仓管理
- 风险控制
"""

from typing import Dict, Optional
from binance.exceptions import BinanceAPIException

from agents.client_interface import ClientInterface
from utils.logger import Logger

logger = Logger.get_logger()

class ManagerAccount:
    """账户管理器"""
    
    def __init__(self, client: ClientInterface):
        """
        初始化账户管理器
        
        Args:
            client: 币安客户端
        """
        self.client: ClientInterface = client

        self.balances = {}
        self.orders = {}
        self.positions = {}
        self.update_account_info()
        
    def update_account_info(self):
        """更新账户信息"""
        try:
            account = self.client.get_account()
            
            # 更新余额
            self.balances = {
                asset['asset']: {
                    'free': float(asset['free']),
                    'locked': float(asset['locked'])
                }
                for asset in account.get('balances', [])
                if float(asset['free']) > 0 or float(asset['locked']) > 0
            }
            
            logger.info("Account info updated")
            
        except BinanceAPIException as e:
            logger.error(f"Failed to update account info: {e}")
            
    def get_balance(self, asset: str) -> Dict[str, float]:
        """
        获取资产余额
        
        Args:
            asset: 资产名称
            
        Returns:
            Dict[str, float]: 余额信息
        """
        return self.balances.get(asset, {'free': 0.0, 'locked': 0.0})
        
    def get_total_balance(self, quote_asset: str = 'USDT') -> float:
        """
        获取总资产价值
        
        Args:
            quote_asset: 计价资产
            
        Returns:
            float: 总资产价值
        """
        total = 0.0
        
        try:
            # 获取所有交易对的最新价格
            prices = {
                symbol['symbol']: float(symbol['price'])
                for symbol in self.client.get_all_tickers()
            }
            
            # 计算每个资产的价值
            for asset, balance in self.balances.items():
                if asset == quote_asset:
                    # 计价资产直接加总
                    total += balance['free'] + balance['locked']
                else:
                    # 其他资产需要转换为计价资产
                    symbol = f"{asset}{quote_asset}"
                    if symbol in prices:
                        asset_value = (balance['free'] + balance['locked']) * prices[symbol]
                        total += asset_value
                        
            return total
            
        except BinanceAPIException as e:
            logger.error(f"Failed to calculate total balance: {e}")
            return 0.0
            
    def check_balance(
            self,
            asset: str,
            amount: float
        ) -> bool:
        """
        检查余额是否足够
        
        Args:
            asset: 资产名称
            amount: 数量
            
        Returns:
            bool: 是否足够
        """
        balance = self.get_balance(asset)
        return balance['free'] >= amount
        
    def calculate_max_order_size(
            self,
            symbol: str,
            side: str,
            price: Optional[float] = None
        ) -> float:
        """
        计算最大可交易数量
        
        Args:
            symbol: 交易对
            side: 买卖方向
            price: 价格（可选）
            
        Returns:
            float: 最大可交易数量
        """
        try:
            # 获取交易对信息
            symbol_info = self.client.get_symbol_info(symbol)
            if not symbol_info:
                return 0.0
                
            # 获取当前价格
            if not price:
                price = float(self.client.get_symbol_price(symbol))
                
            # 获取交易对的基础资产和计价资产
            base_asset = symbol_info['baseAsset']
            quote_asset = symbol_info['quoteAsset']
            
            if side.upper() == 'BUY':
                # 买入时使用计价资产余额
                quote_balance = self.get_balance(quote_asset)['free']
                max_amount = quote_balance / price
            else:
                # 卖出时使用基础资产余额
                max_amount = self.get_balance(base_asset)['free']
                
            # 应用交易对的数量限制
            filters = symbol_info.get('filters', [])
            for f in filters:
                if f['filterType'] == 'LOT_SIZE':
                    min_qty = float(f['minQty'])
                    max_qty = float(f['maxQty'])
                    step_size = float(f['stepSize'])
                    
                    # 调整数量到合法范围
                    max_amount = min(max_amount, max_qty)
                    max_amount = max(max_amount - (max_amount % step_size), min_qty)
                    break
                    
            return max_amount
            
        except BinanceAPIException as e:
            logger.error(f"Failed to calculate max order size: {e}")
            return 0.0
            
    def update_position(self, symbol: str):
        """
        更新持仓信息
        
        Args:
            symbol: 交易对
        """
        try:
            # 获取交易对信息
            symbol_info = self.client.get_symbol_info(symbol)
            if not symbol_info:
                return
                
            base_asset = symbol_info['baseAsset']
            quote_asset = symbol_info['quoteAsset']
            
            # 获取持仓数量
            base_balance = self.get_balance(base_asset)['free']
            quote_balance = self.get_balance(quote_asset)['free']
            
            # 获取当前价格
            price = float(self.client.get_symbol_price(symbol))
            
            # 更新持仓信息
            self.positions[symbol] = {
                'base_amount': base_balance,
                'quote_amount': quote_balance,
                'price': price,
                'value': base_balance * price
            }
            
        except BinanceAPIException as e:
            logger.error(f"Failed to update position: {e}")
            
    def get_position(self, symbol: str) -> Dict:
        """
        获取持仓信息
        
        Args:
            symbol: 交易对
            
        Returns:
            Dict: 持仓信息
        """
        return self.positions.get(symbol, {
            'base_amount': 0.0,
            'quote_amount': 0.0,
            'price': 0.0,
            'value': 0.0
        })
