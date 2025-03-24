"""
单交易对交易环境
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, Tuple

from agents.manager_position import ManagerPosition
from feature.feature import COLUMNS, Feature
from utils import Logger

logging = Logger.get_logger()


class EnvTradingBase(gym.Env):
    """
    单交易对交易环境
    """

    def __init__(self, config: dict[str, any], feat: Feature, uuid: str = "0"):
        super().__init__()

        self.uuid: str = uuid
        self.feat: Feature = feat

        # 获取交易配置
        self.symbol: str = config['symbol']

        # 基本配置
        self.window_size: int = config['window_size']
        self.max_position_size: float = config['max_position_size']
        self.position_scaling: float = config['position_scaling']
        self.normalize: bool = config['normalize']
        self.log_interval:int = config['log_interval'] if config.get('log_interval') else 100

        # 初始资金
        self.initial_balance: float = config['initial_balance']

        # 计算最大技术指标窗口
        self.max_indicator_window: int = self.feat.max_indicator_window()

        # 计算起始位置
        self.min_start_pos: int = int((self.max_indicator_window * 15) + (self.window_size * 15))

        # 1m总步数
        self.total_step: int = self.feat.len()

        # 观察空间
        self.observation_space: spaces.Dict = spaces.Dict({
            '1m': spaces.Box(low=-np.inf, high=np.inf,
                             shape=(self.window_size, len(COLUMNS)), dtype=np.float32),
            '15m': spaces.Box(low=-np.inf, high=np.inf,
                              shape=(self.window_size, len(COLUMNS)), dtype=np.float32),
            # [side, size, entry_price, unrealized_pnl, holding_time]
            'state': spaces.Box(low=-np.inf, high=np.inf, shape=(7,), dtype=np.float32)
        })

        # 动作空间: [0: 不确定, 1: 看多, 2: 看空]
        self.action_space = spaces.Discrete(3)

        # 当前步数
        self.current_step: int = self.min_start_pos
        self.position: ManagerPosition = ManagerPosition()  # 初始化持仓对象
        self.balance: float = self.initial_balance  # 初始化账户余额

        # 初始化统计信息
        self.trades: int = 0  # 总交易次数
        self.win: int = 0  # 胜利交易次数
        self.lose: int = 0  # 失败交易次数
        self.total_pnl: float = 0  # 总盈亏
        self.max_balance: float = 0  # 最大资金
        self.min_balance: float = 0  # 最小资金
        self.max_drawdown: float = 0  # 最大回撤

    def reset(self, seed=None, options=None):
        """重置环境"""
        # 重置随机数种子
        if seed is not None:
            np.random.seed(seed)

        # 重置状态
        self.current_step = self.min_start_pos  # 重置当前步数
        self.balance = self.initial_balance  # 重置账户余额
        self.position.reset()  # 重置持仓

        # 重置统计信息
        self.trades = 0
        self.win = 0
        self.lose = 0
        self.total_pnl = 0.0
        self.max_balance = 0.0  # 最大资金
        self.min_balance = 0.0  # 最小资金
        self.max_drawdown = 0.0  # 最大回撤

        # 获取初始观察
        observation, info = self._observation()
        return observation, info

    def step(self, action: int) -> Tuple[dict[str, np.ndarray], float, bool, bool, dict]:
        pass

    def _step_trade(self, action: int, current_price, old_value, new_value: float) -> Tuple[bool, float]:
        pass

    def _current_price(self) -> float:
        """获取当前价格"""
        return self.feat.current_price(self.current_step)

    def _close(self, close_price: float) -> float:
        """平仓"""
        # 更新账户余额
        realized_pnl, self.balance = self.position.close(close_price, self.balance)
        return realized_pnl

    def _open(self, available_balance: float, side: int) -> bool:
        """开多 side = 1 / 开空 side =-1 """
        # 获取当前价格
        current_price = self._current_price()
        position_size = available_balance / current_price
        ok, self.balance = self.position.open(current_price, position_size, self.balance, side)
        return ok

    def _observation(self, *args) -> tuple[Dict[str, np.ndarray],Dict[str, np.ndarray]]:
        """获取当前观察"""
        pass
