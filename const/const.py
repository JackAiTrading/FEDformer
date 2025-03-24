# 常量
import decimal
from enum import Enum

# 常量
KLine: str = "kline"

# K线的时间段（单位：nanoseconds） 3秒
IntervalSecondKLine1m: int = 3_000_000_000

# K线的时间段（单位：nanoseconds） 30秒
IntervalSecondKLine5m: int = 30_000_000_000

# 订单最少间隔（单位：nanoseconds）50秒
IntervalSecondOrder50s: int = 50_000_000_000

# 开仓最高保证金比例
PositionMarginRate: float = 0.8

# 合约类型倍数
PositionContractMultiplier: float = 25

# 开仓最低保证金
PositionMarginMin: float = 10

# 开仓最大保证金
PositionMarginMax: float = 10000

USDT: str = "USDT"  # USDT
BTC: str = "BTC"  # BTC
ETH: str = "ETH"  # ETH
SOL: str = "SOL"  # SOLANA


# 交易对
class Symbols(Enum):
    ETHUSDT: str = "ETHUSDT"
    BTCUSDT: str = "BTCUSDT"

    def has(self):
        """是否包含"""
        return self in [Symbols.ETHUSDT, Symbols.BTCUSDT]


class Trend(Enum):
    """趋势"""
    Up: int = 1  # 上涨
    Down: int = 2  # 下跌
    Sideways: int = 0  # 横盘


class Position(Enum):
    """ 持仓状态 """
    Empty: int = 0  # 无
    Long: int = 1  # 看多 持仓(全仓)
    Short: int = 2  # 看空 持仓(全仓)


# 持仓方向 Str
class PositionStr(Enum):
    """ 持仓状态 """
    Empty: str = "EMPTY"  # 无
    SHORT: str = "SHORT"  # 空
    LONG: str = "LONG"  # 多


class Execution(Enum):
    """ 执行策略动作 """
    Immediate: int = 0  # 立即执行
    Wait: int = 1  # 等待
    Batch: int = 2  # 分批执行


class Fee:
    """手续费"""

    # 现货手续费 0.1000%/0.1000%
    MakerSpot = 0.001  # 挂单手续费 0.1000%
    TakerSpot = 0.001  # 吃单手续费 0.1000%
    # 合约手续费 0.0200%/0.0500%
    Maker = 0.0002  # 挂单手续费 0.0200%
    Taker = 0.0005  # 吃单手续费 0.0500%

    @staticmethod
    def commission(amount: float) -> float:
        """计算币安手续费"""
        # 这里假设都是吃单
        commission = amount * Fee.Taker
        return commission


# 买卖方向 Int
class Action(Enum):
    """Actions Enum"""

    Stop: int = 0  # 停
    Buy: int = 1  # 买
    Sell: int = 2  # 卖


class ActionStr(Enum):
    """Trading ActionStr Enum"""

    stop: str = "stop"  # 停
    buy: str = "buy"  # 买
    sell: str = "sell"  # 卖
    none: str = "none"  # 无


# 买卖方向 Int
class ActionAI(Enum):
    """Actions Enum"""
    # 0-持有，1-买多，2-做空, 3-持多平仓 4-持空平仓
    AI_HOLD: int = 0
    AI_OPEN_LONG: int = 1
    AI_OPEN_SHORT: int = 2
    AI_CLOSE_LONG: int = 3
    AI_CLOSE_SHORT: int = 4
