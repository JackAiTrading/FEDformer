from agents.client_interface import ClientInterface

"""
多智能体管理器模块

该模块实现了多智能体系统，用于协调多个单智能体环境，
实现更复杂的交易策略和决策过程。
"""
import datetime

from typing import Dict, Any
from stable_baselines3 import PPO, A2C, SAC
from stable_baselines3.common.vec_env import DummyVecEnv
from envs.env_trading_transformer_v2 import EnvTradingTransformerV2
from agents.agent_utils import (
    interpret_trend,
    interpret_position,
    interpret_execution,
    final_action,
)

from feature.feature import Feature
from utils import Logger

logger = Logger.get_logger()


class AgentMulti:
    """
    多智能体管理器

    协调多个单智能体环境，实现复杂的交易策略和决策过程。
    包含三个主要智能体：趋势预测、仓位管理和执行策略。
    """

    def __init__(self, config: Dict[str, Any], feature: Feature, uuid: str = "0"):
        """
        初始化多智能体管理器

        Args:
            config: 配置字典
            feature: 特征数据字典，键为交易对名称
            uuid: 环境ID
        """
        self.config = config
        self.feature: Feature = feature
        self.symbol: str = config["symbol"]
        self.uuid: str = uuid

        # 创建环境
        self.env_trend = self._create_env_trend(feature, self.symbol)
        self.env_position = self._create_env_position(feature, self.symbol)
        self.env_execution = self._create_env_execution(feature, self.symbol)

        # 创建智能体
        self.agent_trend = self._create_agent_trend(self.symbol)
        self.agent_position = self._create_agent_position(self.symbol)
        self.agent_execution = self._create_agent_execution(self.symbol)

        # 交易状态
        self.trading_state = {}

        logger.info(f"多智能体管理器初始化完成，管理交易对: {self.symbol}")

    def _create_env_trend(self, feature: Feature, symbol: str):
        """
        创建趋势预测环境

        Args:
            feature: 特征数据
            symbol: 交易对名称

        Returns:
            趋势预测环境
        """
        # 复制配置并修改为趋势预测环境的配置
        trend_config = self.config.copy()
        trend_config["symbol"] = symbol
        trend_config["env_type"] = "trend"

        # 创建环境
        env = EnvTradingTransformerV2(trend_config, feature, uuid=f"trend_{symbol}")
        return env

    def _create_env_position(
        self, feature: Feature, symbol: str
    ) -> EnvTradingTransformerV2:
        """
        创建仓位管理环境

        Args:
            feature: 特征数据
            symbol: 交易对名称

        Returns:
            仓位管理环境
        """
        # 复制配置并修改为仓位管理环境的配置
        position_config = self.config.copy()
        position_config["symbol"] = symbol
        position_config["env_type"] = "position"

        # 创建环境
        env = EnvTradingTransformerV2(
            position_config, feature, uuid=f"position_{symbol}"
        )
        return env

    def _create_env_execution(
        self, feature: Feature, symbol: str
    ) -> EnvTradingTransformerV2:
        """
        创建执行策略环境

        Args:
            feature: 特征数据
            symbol: 交易对名称

        Returns:
            执行策略环境
        """
        # 复制配置并修改为执行策略环境的配置
        execution_config = self.config.copy()
        execution_config["symbol"] = symbol
        execution_config["env_type"] = "execution"

        # 创建环境
        env = EnvTradingTransformerV2(
            execution_config, feature, uuid=f"execution_{symbol}"
        )
        return env

    def _create_agent_trend(self, symbol: str) -> A2C:
        """
        创建趋势预测智能体

        Args:
            symbol: 交易对名称

        Returns:
            趋势预测智能体
        """
        # 使用A2C算法，适合趋势预测任务
        env = DummyVecEnv([lambda: self.env_trend])
        agent = A2C(
            "MultiInputPolicy",
            env,
            learning_rate=0.0005,
            n_steps=64,
            gamma=0.99,
            verbose=1,
            tensorboard_log=f"{self.config['tensorboard_log']}/trend_{symbol}",
        )
        return agent

    def _create_agent_position(self, symbol: str) -> PPO:
        """
        创建仓位管理智能体

        Args:
            symbol: 交易对名称

        Returns:
            仓位管理智能体
        """
        # 使用PPO算法，适合仓位管理任务
        env = DummyVecEnv([lambda: self.env_position[symbol]])
        agent = PPO(
            "MultiInputPolicy",
            env,
            learning_rate=0.0003,
            n_steps=1024,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            verbose=1,
            tensorboard_log=f"{self.config['tensorboard_log']}/position_{symbol}",
        )
        return agent

    def _create_agent_execution(self, symbol: str) -> SAC:
        """
        创建执行策略智能体

        Args:
            symbol: 交易对名称

        Returns:
            执行策略智能体
        """
        # 使用SAC算法，适合执行策略任务
        env = DummyVecEnv([lambda: self.env_execution[symbol]])
        agent = SAC(
            "MultiInputPolicy",
            env,
            learning_rate=0.0003,
            buffer_size=100000,
            batch_size=256,
            gamma=0.99,
            tau=0.005,
            verbose=1,
            tensorboard_log=f"{self.config['tensorboard_log']}/execution_{symbol}",
        )
        return agent

    def train(self, total_timesteps: int = 100000):
        """
        训练所有智能体

        Args:
            total_timesteps: 总训练步数
        """
        logger.info(f"开始训练多智能体系统，总步数: {total_timesteps}")

        # 第一阶段：训练趋势预测智能体
        logger.info("第一阶段：训练趋势预测智能体")
        self.agent_trend.learn(total_timesteps=total_timesteps)

        # 第二阶段：训练仓位管理智能体
        logger.info("第二阶段：训练仓位管理智能体")
        self.agent_position.learn(total_timesteps=total_timesteps)

        # 第三阶段：训练执行策略智能体
        logger.info("第三阶段：训练执行策略智能体")
        self.agent_execution.learn(total_timesteps=total_timesteps)

        logger.info("多智能体系统训练完成")

    def predict(self, market_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        使用多智能体系统进行预测

        Args:
            market_data: 市场数据，包含各交易对的观察数据

        Returns:
            预测结果，包含各交易对的趋势、仓位和执行策略
        """

        # 1. 趋势预测
        trend_action, _ = self.agent_trend.predict(market_data)

        # 2. 仓位管理 - 结合趋势预测结果
        position_data = self._combine_data(market_data, {"trend": trend_action})
        position_action, _ = self.agent_position.predict(position_data)

        # 3. 执行策略 - 结合趋势和仓位结果
        execution_data = self._combine_data(
            position_data, {"position": position_action}
        )
        execution_action, _ = self.agent_execution.predict(execution_data)

        # 整合结果
        results = {
            "trend": interpret_trend(trend_action),
            "position": interpret_position(position_action),
            "execution": interpret_execution(execution_action),
            "final_action": final_action(
                trend_action, position_action, execution_action
            ),
        }

        return results

    def _combine_data(
        self, base_data: Dict[str, Any], additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        组合数据

        Args:
            base_data: 基础数据
            additional_data: 额外数据

        Returns:
            组合后的数据
        """
        combined = base_data.copy()
        for key, value in additional_data.items():
            combined[key] = value
        return combined

    def save_models(self, path: str):
        """
        保存所有模型

        Args:
            path: 保存路径
        """
        date_tag = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # 保存趋势预测模型
        self.agent_trend.save(f"{path}/trend_{self.symbol}_{date_tag}")
        # 保存仓位管理模型
        self.agent_position.save(f"{path}/position_{self.symbol}_{date_tag}")
        # 保存执行策略模型
        self.agent_execution.save(f"{path}/execution_{self.symbol}_{date_tag}")

        logger.info(f"所有模型已保存到 {path}")

    def load_models(self, path: str, date_tag: str):
        """
        加载所有模型

        Args:
            :param path: 模型路径
            :param date_tag: 日期标签
        """
        try:
            # 加载趋势预测模型
            self.agent_trend = A2C.load(f"{path}/trend_{self.symbol}_{date_tag}")
            # 加载仓位管理模型
            self.agent_position = PPO.load(f"{path}/position_{self.symbol}_{date_tag}")
            # 加载执行策略模型
            self.agent_execution = SAC.load(
                f"{path}/execution_{self.symbol}_{date_tag}"
            )
            logger.info(f"成功加载 {self.symbol}_{date_tag} 的模型")
        except Exception as e:
            logger.error(f"加载 {self.symbol}_{date_tag} 模型失败: {str(e)}")

        logger.info(f"所有模型已从 {path} 加载")

    def execute_trades(self, client, predictions: Dict[str, Dict[str, Any]]):
        """
        执行交易

        Args:
            client: 币安客户端
            predictions: 预测结果
        """
        for symbol, prediction in predictions.items():
            final_action = prediction.get("final_action", {})
            action = final_action.get("action", "未知")

            # 获取当前持仓
            position_info = self._get_position_info(client, symbol)
            current_position = position_info.get("position", 0)

            # 执行交易
            if action == "买入" and current_position <= 0:
                self._execute_buy(client, symbol, final_action)
            elif action == "卖出" and current_position >= 0:
                self._execute_sell(client, symbol, final_action)
            elif action == "空仓" and current_position != 0:
                self._execute_close(client, symbol)
            else:
                logger.info(f"{symbol}: 保持当前状态，不执行交易")

    def _get_position_info(self, client, symbol: str) -> Dict[str, Any]:
        """
        获取持仓信息

        Args:
            client: 币安客户端
            symbol: 交易对

        Returns:
            持仓信息
        """
        try:
            positions = client.get_position_risk(symbol=symbol)
            for position in positions:
                if position["symbol"] == symbol:
                    amount = float(position["positionAmt"])
                    entry_price = float(position["entryPrice"])
                    leverage = float(position["leverage"])

                    return {
                        "position": amount,
                        "entry_price": entry_price,
                        "leverage": leverage,
                        "mark_price": float(position["markPrice"]),
                        "unrealized_pnl": float(position["unRealizedProfit"]),
                    }

            return {
                "position": 0,
                "entry_price": 0,
                "leverage": 0,
                "mark_price": 0,
                "unrealized_pnl": 0,
            }
        except Exception as e:
            logger.error(f"获取 {symbol} 持仓信息失败: {str(e)}")
            return {
                "position": 0,
                "entry_price": 0,
                "leverage": 0,
                "mark_price": 0,
                "unrealized_pnl": 0,
            }

    def _execute_buy(self, client, symbol: str, action_info: Dict[str, Any]):
        """
        执行买入操作

        Args:
            client: 币安客户端
            symbol: 交易对
            action_info: 动作信息
        """
        try:
            # 获取账户余额
            balance_info = self._get_account_balance(client)
            available_balance = balance_info.get("available", 0)

            # 获取当前价格
            current_price = self._get_current_price(client, symbol)

            # 计算买入数量
            confidence = action_info.get("confidence", "中")
            position_size = self._calculate_position_size(
                available_balance, current_price, confidence
            )

            # 执行买入
            execution_type = action_info.get("execution", "立即执行")
            if execution_type == "分批执行":
                # 分批买入
                batch_size = position_size / 3
                logger.info(f"{symbol}: 分批买入 - 第1批 {batch_size:.6f}")
                client.place_market_order(
                    symbol=symbol, side="BUY", quantity=batch_size
                )

                # 后续批次在实际应用中可以通过定时任务执行
                logger.info(f"{symbol}: 分批买入 - 剩余批次将在后续执行")
            else:
                # 立即买入
                logger.info(f"{symbol}: 立即买入 {position_size:.6f}")
                client.place_market_order(
                    symbol=symbol, side="BUY", quantity=position_size
                )

            # 更新交易状态
            self.trading_state[symbol] = {
                "action": "买入",
                "price": current_price,
                "size": position_size,
                "time": self._get_current_time(),
            }

        except Exception as e:
            logger.error(f"执行 {symbol} 买入操作失败: {str(e)}")

    def _execute_sell(self, client, symbol: str, action_info: Dict[str, Any]):
        """
        执行卖出操作

        Args:
            client: 币安客户端
            symbol: 交易对
            action_info: 动作信息
        """
        try:
            # 获取账户余额
            balance_info = self._get_account_balance(client)
            available_balance = balance_info.get("available", 0)

            # 获取当前价格
            current_price = self._get_current_price(client, symbol)

            # 计算卖出数量
            confidence = action_info.get("confidence", "中")
            position_size = self._calculate_position_size(
                available_balance, current_price, confidence
            )

            # 执行卖出
            execution_type = action_info.get("execution", "立即执行")
            if execution_type == "分批执行":
                # 分批卖出
                batch_size = position_size / 3
                logger.info(f"{symbol}: 分批卖出 - 第1批 {batch_size:.6f}")
                client.place_market_order(
                    symbol=symbol, side="SELL", quantity=batch_size
                )

                # 后续批次在实际应用中可以通过定时任务执行
                logger.info(f"{symbol}: 分批卖出 - 剩余批次将在后续执行")
            else:
                # 立即卖出
                logger.info(f"{symbol}: 立即卖出 {position_size:.6f}")
                client.place_market_order(
                    symbol=symbol, side="SELL", quantity=position_size
                )

            # 更新交易状态
            self.trading_state[symbol] = {
                "action": "卖出",
                "price": current_price,
                "size": position_size,
                "time": self._get_current_time(),
            }

        except Exception as e:
            logger.error(f"执行 {symbol} 卖出操作失败: {str(e)}")

    def _execute_close(self, client, symbol: str):
        """
        执行平仓操作

        Args:
            client: 币安客户端
            symbol: 交易对
        """
        try:
            # 获取当前持仓
            position_info = self._get_position_info(client, symbol)
            current_position = position_info.get("position", 0)

            if current_position == 0:
                logger.info(f"{symbol}: 当前无持仓，无需平仓")
                return

            # 确定平仓方向
            side = "SELL" if current_position > 0 else "BUY"
            quantity = abs(current_position)

            # 执行平仓
            logger.info(f"{symbol}: 平仓 {quantity:.6f}")
            client.place_market_order(
                symbol=symbol, side=side, quantity=quantity, reduce_only=True
            )

            # 更新交易状态
            self.trading_state[symbol] = {
                "action": "平仓",
                "price": self._get_current_price(client, symbol),
                "size": quantity,
                "time": self._get_current_time(),
            }

        except Exception as e:
            logger.error(f"执行 {symbol} 平仓操作失败: {str(e)}")

    def _get_account_balance(self, client: ClientInterface) -> Dict[str, float]:
        """
        获取账户余额

        Args:
            client: 币安客户端

        Returns:
            账户余额信息
        """
        try:
            balance_info = client.get_balance()
            for asset in balance_info:
                if asset["asset"] == "USDT":
                    return {
                        "total": float(asset["balance"]),
                        "available": float(asset["availableBalance"]),
                    }

            return {"total": 0, "available": 0}
        except Exception as e:
            logger.error(f"获取账户余额失败: {str(e)}")
            return {"total": 0, "available": 0}

    def _get_current_price(self, client, symbol: str) -> float:
        """
        获取当前价格

        Args:
            client: 币安客户端
            symbol: 交易对

        Returns:
            当前价格
        """
        try:
            mark_price = client.get_mark_price(symbol=symbol)
            if isinstance(mark_price, dict):
                return float(mark_price["markPrice"])
            else:
                for item in mark_price:
                    if item["symbol"] == symbol:
                        return float(item["markPrice"])
            return 0
        except Exception as e:
            logger.error(f"获取 {symbol} 当前价格失败: {str(e)}")
            return 0

    def _calculate_position_size(
        self, available_balance: float, current_price: float, confidence: str
    ) -> float:
        """
        计算仓位大小

        Args:
            available_balance: 可用余额
            current_price: 当前价格
            confidence: 信心水平

        Returns:
            仓位大小
        """
        # 根据信心水平确定仓位比例
        confidence_ratio = {
            "高": 0.3,  # 高信心使用30%资金
            "中": 0.2,  # 中等信心使用20%资金
            "低": 0.1,  # 低信心使用10%资金
        }.get(confidence, 0.1)

        # 计算仓位大小
        position_value = available_balance * confidence_ratio
        position_size = position_value / current_price

        # 四舍五入到6位小数
        return round(position_size, 6)

    def _get_current_time(self) -> str:
        """
        获取当前时间

        Returns:
            当前时间字符串
        """
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_trading_summary(self) -> Dict[str, Any]:
        """
        获取交易摘要

        Returns:
            交易摘要
        """
        return {"symbols": self.symbols, "trading_state": self.trading_state}
