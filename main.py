"""
多智能体交易系统示例

该脚本展示了如何使用多智能体管理器进行交易。
"""
import argparse
import os
import sys
from typing import Dict

import yaml
import time
from datetime import datetime

from agents.agent_multi import AgentMulti
from agents.client_binance import ClientBinance
from agents.client_interface import ClientInterface
from agents.client_simulation import ClientSimulation
from utils import Logger
from utils.config_yaml import ConfigYaml
from feature.feature import Feature

logger = Logger.get_logger()

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='交易机器人')
    parser.add_argument('--mode', type=str, default='train',
                        choices=['train', 'validate', 'predict', 'test'],
                        help='运行模式: train/validate/predict/test')
    parser.add_argument('--path', type=str, default='./config/',
                        help='配置文件路径')
    parser.add_argument('--custom', type=str, default='default',
                        help='自定义配置文件名，如custom-default.yaml')

    args = parser.parse_args()

    # 加载配置
    logger.info(f"Loading config from path：{args.path} custom: {args.custom} mode: {args.mode}")
    config = ConfigYaml(args.path,args.custom).all()

    # 加载特征
    feature = Feature(config=config)

    # 创建多智能体管理器
    manager = AgentMulti(config=config, feature= feature)

    # 运行模式
    if args.mode == 'train':
        logger.info("开始训练模型...")
        manager.train(total_timesteps=config.get('total_timesteps', 100000))

        # 保存模型
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  'models', f"multi_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(model_path, exist_ok=True)
        manager.save_models(model_path)
        logger.info(f"模型保存到 {model_path}")
    else:
        # 加载已有模型
        model_path = config.get('model_path')
        if model_path:
            logger.info(f"加载模型从 {model_path}...")
            manager.load_models(model_path)
        else:
            logger.warning("未指定模型路径，将使用未训练的模型")

    # 初始化币安客户端
    if args.mode == 'predict':
        # 实时交易模式
        api_key = config.get('api_key', '')
        api_secret = config.get('api_secret', '')
        testnet = config.get('testnet', True)

        if not api_key or not api_secret:
            logger.error("未提供API密钥，无法进行实时交易")
            return

        client: ClientInterface = get_client(config=config)

        # 设置杠杆和保证金类型
        for symbol in config['symbols']:
            client.set_leverage(symbol=symbol, leverage=config.get('leverage', 1))
            client.set_margin_type(symbol=symbol, margin_type=config.get('margin_type', 'ISOLATED'))

        # 实时交易循环
        try:
            while True:
                # 获取市场数据
                market_data = {}
                for symbol in config['symbols']:
                    # 获取K线数据
                    klines_1m = client.get_klines(
                        symbol=symbol,
                        interval='1m',
                        limit=config['window_size']
                    )
                    klines_15m = client.get_klines(
                        symbol=symbol,
                        interval='15m',
                        limit=config['window_size']
                    )

                    # 处理数据为模型可接受的格式
                    market_data[symbol] = {
                        '1m': process_klines(klines_1m),
                        '15m': process_klines(klines_15m)
                    }

                # 预测交易动作
                predictions = manager.predict(market_data)
                logger.info(f"预测结果: {predictions}")

                # 执行交易
                manager.execute_trades(client, predictions)

                # 获取交易摘要
                summary = manager.get_trading_summary()
                logger.info(f"交易摘要: {summary}")

                # 等待下一个交易周期
                sleep_time = config.get('trading_interval', 60)
                logger.info(f"等待 {sleep_time} 秒后进行下一次交易...")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("用户中断，退出交易")
        except Exception as e:
            logger.error(f"交易过程中发生错误: {str(e)}")
    else:
        # 回测模式
        logger.info("开始回测...")
        backtest_results = run_backtest(manager, config)
        logger.info(f"回测结果: {backtest_results}")

def get_client(config: Dict[str, any]):
    """
    获取 客户端

    Args:
        config: 配置字典

    Returns:
        币安客户端实例
    """
    if config is None:
        config = {}
    trading_mode = config.get("trading_mode", "simulation")
    if trading_mode == "binance":
        return ClientBinance(config=config)
    return ClientSimulation(config=config)

def run_backtest(manager, config):
    """运行回测"""
    import pandas as pd
    from datetime import datetime, timedelta

    logger.info("加载回测数据...")

    # 回测参数
    start_date = config.get('backtest_start_date', '2023-01-01')
    end_date = config.get('backtest_end_date', '2023-12-31')
    initial_balance = config.get('initial_balance', 10000)

    # 回测结果
    results = {
        'balance': initial_balance,
        'trades': [],
        'pnl': [],
        'equity_curve': []
    }

    # 获取交易对
    symbol = config['symbol']

    # 加载历史数据
    historical_data = load_historical_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        data_dir=config['data_dir']
    )

    # 回测循环
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

    while current_date <= end_datetime:
        # 获取当前日期的市场数据
        market_data = {}
        for symbol in config['symbols']:
            market_data[symbol] = get_market_data_for_date(
                historical_data[symbol],
                current_date,
                config['window_size']
            )

        # 预测交易动作
        predictions = manager.predict(market_data)

        # 模拟交易执行
        trades, pnl = simulate_trades(predictions, historical_data, current_date, results['balance'])

        # 更新结果
        results['balance'] += pnl
        results['trades'].extend(trades)
        results['pnl'].append(pnl)
        results['equity_curve'].append({
            'date': current_date.strftime('%Y-%m-%d'),
            'balance': results['balance']
        })

        # 移动到下一个交易日
        current_date += timedelta(days=1)

    # 计算回测指标
    results['metrics'] = calc_backtest_metrics(results)

    return results

def simulate_trades(predictions, historical_data, date, balance):
    """模拟交易执行"""
    trades = []
    total_pnl = 0

    for symbol, prediction in predictions.items():
        action = prediction.get('final_action', {}).get('action', '未知')

        if action in ['买入', '卖出']:
            # 模拟交易执行
            price = get_price_for_date(historical_data[symbol], date)
            size = calc_position_size(balance, price, prediction)

            trade = {
                'symbol': symbol,
                'action': action,
                'price': price,
                'size': size,
                'date': date.strftime('%Y-%m-%d')
            }
            trades.append(trade)

            # 计算盈亏
            next_day_price = get_price_for_date(historical_data[symbol], date + timedelta(days=1))
            if next_day_price > 0:
                if action == '买入':
                    pnl = (next_day_price - price) * size
                else:
                    pnl = (price - next_day_price) * size
                total_pnl += pnl

    return trades, total_pnl

def get_price_for_date(historical_data, date):
    """获取指定日期的价格"""
    # 实现获取指定日期价格的逻辑
    # 这里简化处理，实际应用中需要根据具体数据格式进行处理
    data = historical_data[historical_data['date'] == date.strftime('%Y-%m-%d')]
    if len(data) > 0:
        return data['close'].values[0]
    return 0

def calc_position_size(balance, price, prediction):
    """计算仓位大小"""
    confidence = prediction.get('final_action', {}).get('confidence', '中')

    # 根据信心水平确定仓位比例
    confidence_ratio = {
        '高': 0.3,  # 高信心使用30%资金
        '中': 0.2,  # 中等信心使用20%资金
        '低': 0.1   # 低信心使用10%资金
    }.get(confidence, 0.1)

    # 计算仓位大小
    position_value = balance * confidence_ratio
    position_size = position_value / price if price > 0 else 0

    return position_size

def calc_backtest_metrics(results):
    """计算回测指标"""
    import numpy as np

    # 提取数据
    equity_curve = [item['balance'] for item in results['equity_curve']]
    pnl = results['pnl']

    # 计算指标
    total_return = (equity_curve[-1] / equity_curve[0] - 1) * 100 if equity_curve[0] > 0 else 0

    # 计算最大回撤
    max_drawdown = 0
    peak = equity_curve[0]
    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100 if peak > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)

    # 计算夏普比率
    returns = np.diff(equity_curve) / equity_curve[:-1]
    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if len(returns) > 0 and np.std(returns) > 0 else 0

    # 计算胜率
    win_trades = sum(1 for p in pnl if p > 0)
    total_trades = len(pnl)
    win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0

    return {
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'win_rate': win_rate,
        'total_trades': total_trades
    }

if __name__ == "__main__":
    main()