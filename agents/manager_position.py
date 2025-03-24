from const.const import Fee


class ManagerPosition:
    """持仓信息"""

    def __init__(self,
                 side: int = 0,
                 size: float = 0.0,
                 entry_price: float = 0.0,
                 unrealized_pnl: float = 0.0,
                 holding_time: int = 0,
                 max_profit: float = 0.0,
                 max_loss: float = 0.0):
        """
        初始化持仓信息

        Args:
            side: 持仓方向，1为多，-1为空，0为空仓
            size: 持仓大小
            entry_price: 入场价格
            unrealized_pnl: 未实现盈亏
            holding_time: 持仓时间
            max_profit: 最大浮盈
            max_loss: 最大浮亏
        """
        self.side: int = side  # 持仓方向，1为多，-1为空，0为空仓
        self.size: float = size  # 持仓大小
        self.entry_price: float = entry_price  # 入场价格
        self.unrealized_pnl: float = unrealized_pnl  # 未实现盈亏
        self.holding_time: int = holding_time  # 持仓时间
        self.idle_time: int = 0  # 空仓时间
        self.capital: float = 0  # 成本
        self.max_profit: float = max_profit  # 最大浮盈
        self.max_loss: float = max_loss  # 最大浮亏

    def reset(self):
        """重置持仓状态"""
        self.side: int = 0
        self.size: float = 0.0
        self.entry_price: float = 0.0
        self.unrealized_pnl: float = 0.0
        self.holding_time: int = 0
        self.idle_time: int = 0
        self.capital: float = 0
        self.max_profit: float = 0.0
        self.max_loss: float = 0.0

    def update(self, current_price: float):
        """
        更新未实现盈亏

        Args:
            current_price: 当前价格
        """
        if self.side == 0:
            self.size = 0.0
            self.entry_price = 0.0
            self.unrealized_pnl = 0.0
            self.capital = 0
            self.holding_time = 0
            self.idle_time += 1
            return

        self.idle_time = 0
        if self.side == 1:  # 多头
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        else:  # 空头
            self.unrealized_pnl = (self.entry_price - current_price) * self.size

        # 更新持仓时间
        self.holding_time += 1

        # 更新最大浮盈和浮亏
        if self.unrealized_pnl > self.max_profit:
            self.max_profit = self.unrealized_pnl
        elif self.unrealized_pnl < self.max_loss:
            self.max_loss = self.unrealized_pnl

    def open(self, current_price: float, position_size: float, balance: float, side: int) -> (bool, float):
        """开多 side = 1 / 开空 side =-1 """
        if position_size <= 0.0000000001:
            return False, balance
            # raise RuntimeError(f"Error in current_price:{current_price} position_size:{position_size} balance:{balance} side:{side}")
        # 计算开仓金额
        amount = position_size * current_price

        # 计算手续费
        commission = Fee.commission(amount)

        # 检查余额
        if balance < commission + amount:
            return False, balance

        # 更新账户余额
        balance = balance - commission - amount

        # 更新持仓信息
        self.side = side
        self.size = position_size
        self.entry_price = current_price
        self.capital = amount+commission
        self.unrealized_pnl = 0.0
        self.holding_time = 1
        self.idle_time = 0

        self.max_profit = 0.0
        self.max_loss = 0.0
        return True, balance

    def close(self, current_price: float, balance: float) -> (float, float):
        """平仓"""
        # 计算平仓金额
        amount = self.size * current_price

        # 计算平仓盈亏
        if self.side == 1:  # 多仓
            realized_pnl = (current_price - self.entry_price) * self.size
        else:  # 空仓
            realized_pnl = (self.entry_price - current_price) * self.size

        # 计算手续费
        commission = Fee.commission(amount)

        # 更新账户余额
        balance = balance + amount - commission
        if balance < 0:
            balance = 0
            realized_pnl = -balance

        # 更新持仓信息
        self.side = 0
        self.size = 0
        self.entry_price = 0
        self.unrealized_pnl = 0
        self.capital = 0
        self.holding_time = 0
        self.idle_time = 1

        self.max_profit = 0.0
        self.max_loss = 0.0

        return realized_pnl, balance

    # 计算手续费
    def commission(self, current_price: float):
        if self.side == 0 or self.size == 0:
            return 0
        amount = self.size * current_price  # 计算平仓金额
        return Fee.commission(amount)
