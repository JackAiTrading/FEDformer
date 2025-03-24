import numpy as np
from collections import deque
from scipy.signal import argrelextrema


def get_lows(data: np.array, order=5):
    """
    计算最低点 Get lows
    :param data:
    :param order:
    :return:
    """
    low_idx = argrelextrema(data, np.less, order=order)[0]
    # 最后段
    last_idx = low_idx[-1]
    # last_val = data[last_idx]
    data2 = data[last_idx + 1:]

    # max_idx = price.shape[0] - 1
    # print("max_idx :", max_idx)
    # print("last idx/val:", last_idx, last_val)

    last_idx2 = None
    last_val2 = None
    for idx, val in enumerate(np.nditer(data2)):
        idx2 = idx + last_idx + 1
        if last_val2 is None:
            last_idx2 = idx2
            last_val2 = val
            # print(" init: idx2", idx2, " value", value)
        if val < last_val2:
            last_idx2 = idx2
            last_val2 = val
            # print(idx2, val)

    # print(" last: idx2", last_idx2, " val2", last_val2, " idx:", last_idx, " val", last_val)
    # print("last_idx2 - last_idx", last_idx2 - last_idx)
    if last_idx2 - last_idx >= 3:
        low_idx = np.append(low_idx, last_idx2)
        # print(" last: idx2", last_idx2, " val2", last_val2)

    return low_idx


def get_highs(data: np.array, order=5):
    """
    计算个股高点 Get highs
    :param data:
    :param order:
    :return:
    """
    high_idx = argrelextrema(data, np.greater, order=order)[0]
    # 最后段
    last_idx = high_idx[-1]
    # last_val = data[last_idx]
    data2 = data[last_idx + 1:]

    # max_idx = price.shape[0] - 1
    # print("max_idx :", max_idx)
    # print("last idx/val:", last_idx, last_val)

    last_idx2 = None
    last_val2 = None
    for idx, val in enumerate(np.nditer(data2)):
        idx2 = idx + last_idx + 1
        if last_val2 is None:
            last_idx2 = idx2
            last_val2 = val
            # print(" init: idx2", idx2, " value", value)
        if val > last_val2:
            last_idx2 = idx2
            last_val2 = val
        # print(idx2, val)
    # print(" last: idx2", last_idx2, " val2", last_val2, " idx:", last_idx, " val", last_val)
    # print("last_idx2 - last_idx", last_idx2 - last_idx)
    if last_idx2 - last_idx >= 3:
        high_idx = np.append(high_idx, last_idx2)
        # print(" last: idx2", last_idx2, " val2", last_val2)
    return high_idx


def get_higher_lows(data: np.array, order=5, K=2):
    """
    发现价格模式中连续较高的低点。
     不得超过要确认的值的宽度参数指示的周期数。
      K 决定需要有多少个连续低点更高。
    """
    # Get lows
    low_idx = argrelextrema(data, np.less, order=order)[0]
    lows = data[low_idx]
    # Ensure consecutive lows are higher than previous lows
    extrema = []
    ex_deque = deque(maxlen=K)
    for i, idx in enumerate(low_idx):
        if i == 0:
            ex_deque.append(idx)
            continue
        if lows[i] < lows[i - 1]:
            ex_deque.clear()

        ex_deque.append(idx)
        if len(ex_deque) == K:
            extrema.append(ex_deque.copy())

    return extrema


def get_lower_highs(data: np.array, order=5, K=2):
    """
    发现价格模式中连续较低的高点。
     不得超过要确认的值的宽度参数指示的周期数。
     K 决定需要降低多少个连续高点。
    """
    # Get highs
    high_idx = argrelextrema(data, np.greater, order=order)[0]
    highs = data[high_idx]
    # Ensure consecutive highs are lower than previous highs
    extrema = []
    ex_deque = deque(maxlen=K)
    for i, idx in enumerate(high_idx):
        if i == 0:
            ex_deque.append(idx)
            continue
        if highs[i] > highs[i - 1]:
            ex_deque.clear()

        ex_deque.append(idx)
        if len(ex_deque) == K:
            extrema.append(ex_deque.copy())

    return extrema


def get_higher_highs(data: np.array, order=5, K=2):
    """
    在价格模式中发现连续的高点。
      不得超过宽度所指示的周期数待确认值的参数。
      K决定了有多少个连续的高点需要更高。
    """
    # Get highs
    high_idx = argrelextrema(data, np.greater, order=order)[0]
    highs = data[high_idx]
    # Ensure consecutive highs are higher than previous highs
    extrema = []
    ex_deque = deque(maxlen=K)
    for i, idx in enumerate(high_idx):
        if i == 0:
            ex_deque.append(idx)
            continue
        if highs[i] < highs[i - 1]:
            ex_deque.clear()

        ex_deque.append(idx)
        if len(ex_deque) == K:
            extrema.append(ex_deque.copy())

    return extrema


def get_lower_lows(data: np.array, order=5, K=2):
    """
    发现价格模式中连续较低的低点。
     不得超过要确认的值的宽度参数指示的周期数。
     K 决定需要降低多少个连续低点。
    """
    # Get lows
    low_idx = argrelextrema(data, np.less, order=order)[0]
    lows = data[low_idx]
    # Ensure consecutive lows are lower than previous lows
    extrema = []
    ex_deque = deque(maxlen=K)
    for i, idx in enumerate(low_idx):
        if i == 0:
            ex_deque.append(idx)
            continue
        if lows[i] > lows[i - 1]:
            ex_deque.clear()

        ex_deque.append(idx)
        if len(ex_deque) == K:
            extrema.append(ex_deque.copy())

    return extrema


def get_hh_index(data: np.array, order=5, K=2):
    extrema = get_higher_highs(data, order, K)
    idx = np.array([i[-1] + order for i in extrema])
    return idx[np.where(idx < len(data))]


def get_lh_index(data: np.array, order=5, K=2):
    extrema = get_lower_highs(data, order, K)
    idx = np.array([i[-1] + order for i in extrema])
    return idx[np.where(idx < len(data))]


def get_ll_index(data: np.array, order=5, K=2):
    extrema = get_lower_lows(data, order, K)
    idx = np.array([i[-1] + order for i in extrema])
    return idx[np.where(idx < len(data))]


def get_hl_index(data: np.array, order=5, K=2):
    extrema = get_higher_lows(data, order, K)
    idx = np.array([i[-1] + order for i in extrema])
    return idx[np.where(idx < len(data))]
