import const.const
from feature.signal_util import get_higher_highs, get_lower_lows, get_highs, get_lows


def determine_trend(close, order=5):
    """
    判断当前趋势状态
    :param close: 收盘价列表
    :param order: 用于计算高点和低点的周期
    :return: '上升'/'下跌'/'盘整'
    """
    # 获取最近的高点/低点索引
    highs = get_highs(close, order)
    lows = get_lows(close, order)

    # 计算最近高点/低点的距离
    last_high_dist = len(close) - highs[-1] if len(highs) > 0 else 0
    last_low_dist = len(close) - lows[-1] if len(lows) > 0 else 0

    # 趋势判断逻辑
    if len(highs) >= 2 and len(lows) >= 2:
        # 上升趋势条件：连续更高高点且更高低点
        if (close[highs[-1]] > close[highs[-2]] and
                close[lows[-1]] > close[lows[-2]]):
            return '上升'

        # 下跌趋势条件：连续更低低点且更低高点
        if (close[lows[-1]] < close[lows[-2]] and
                close[highs[-1]] < close[highs[-2]]):
            return '下跌'

    # 短期趋势判断（最后3个K线）
    if last_high_dist < last_low_dist:  # 高点更近
        if close[-1] > close[-2] > close[-3]:
            return '上升'
    else:  # 低点更近
        if close[-1] < close[-2] < close[-3]:
            return '下跌'

    return '盘整'


def trend_strength(close, order=5):
    """
    分析趋势强度特征
    :param close: 收盘价列表
    :param order: 用于计算高点和低点的周期
    :return: dict {
        'direction': 方向,
        'strength': 强度(0-100),
        'highs_count': 连续高点数,
        'lows_count': 连续低点数
    }
    """
    # 获取连续模式
    hh = get_higher_highs(close, order, K=3)
    ll = get_lower_lows(close, order, K=3)

    # 计算强度指标
    strength = min(100, (len(hh)*20 + len(ll)*20))  # 每个连续模式贡献20%强度

    return {
        'direction': const.const.Trend.上升.value if len(hh) > len(ll) else const.const.Trend.下跌.value,
        'strength': strength,
        'highs_count': len(hh),
        'lows_count': len(ll)
    }


# 在get_signals_sell_buy中调用
def get_signals_sell_buy(data):
    close = data["close"].values

    # 获取趋势状态
    trend_status = determine_trend(close)

    # 获取趋势强度
    strength_info = trend_strength(close)

    print(f"当前趋势: {trend_status}")
    print(f"趋势强度: {strength_info}")

    # 原有逻辑...
