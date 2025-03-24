from typing import Dict, List, Tuple, Any, Optional

from const.const import Trend, Position, Execution


def interpret_trend(action: Trend) -> str:
    """
    解释趋势预测动作

    Args:
        action: 趋势预测动作

    Returns:
        趋势解释
    """
    trend_map = {
        Trend.Sideways: "震荡",
        Trend.Up: "上涨",
        Trend.Down: "下跌"
    }
    return trend_map.get(action, "未知<震荡>")


def interpret_position(position: Position) -> str:
    """
    解释仓位管理动作

    Args:
        position: 仓位管理动作

    Returns:
        仓位解释
    """
    position_map = {
        Position.Empty: "空仓",
        Position.Long: "持多",
        Position.Short: "持空"
    }
    return position_map.get(position, "未知<空仓>")


def interpret_execution(action: int) -> str:
    """
    解释执行策略动作

    Args:
        action: 执行策略动作

    Returns:
        执行策略解释
    """
    execution_map = {
        0: "立即执行",
        1: "等待",
        2: "分批执行"
    }
    return execution_map.get(action, "未知<立即>")


def final_action(trend: Trend, position: Position, execution: int) -> Dict[str, Any]:
    """
    获取最终交易动作

    Args:
        trend: 趋势预测动作
        position: 仓位管理动作
        execution: 执行策略动作

    Returns:
        最终交易动作
    """
    # 根据三个智能体的输出综合决策
    if position == Position.Empty:  # 空仓
        return {"action": "空仓", "reason": "仓位管理建议空仓"}

    if position == Position.Long:  # 持多
        if trend == Trend.Up:  # 上涨
            confidence = "高" if execution == Execution.Immediate else "中"
            return {
                "action": "买入",
                "confidence": confidence,
                "execution": interpret_execution(execution),
                "reason": "趋势向上，仓位管理建议持多"
            }
        else:
            return {
                "action": "观望",
                "reason": "趋势不明确，但仓位管理建议持多"
            }

    if position == Position.Long:  # 持空
        if trend == Trend.Down:  # 下跌
            confidence = "高" if execution == Execution.Immediate else "中"
            return {
                "action": "卖出",
                "confidence": confidence,
                "execution": interpret_execution(execution),
                "reason": "趋势向下，仓位管理建议持空"
            }
        else:
            return {
                "action": "观望",
                "reason": "趋势不明确，但仓位管理建议持空"
            }

    return {"action": "未知", "reason": "无法确定交易动作"}
