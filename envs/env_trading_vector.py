"""
基于向量存储的交易环境
"""

import numpy as np
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

from envs.env_trading_base import EnvTradingBase
from feature.vector_store import VectorStore
from utils.logger import Logger

logger = Logger.get_logger()

class EnvTradingVector(EnvTradingBase):
    """基于向量存储的交易环境"""
    
    def __init__(self, config: Dict[str, Any], feat, uuid: int = 0):
        """
        初始化环境
        
        Args:
            config: 配置信息
            feat: 特征对象
            uuid: 环境ID
        """
        super().__init__(config, feat, uuid)
        
        # 初始化向量存储
        self.vector_store = VectorStore(config)
        logger.info("向量存储交易环境初始化完成")
    
    def _get_state_vector(self) -> np.ndarray:
        """
        获取当前状态的向量表示
        
        Returns:
            状态向量
        """
        # 获取当前观察
        obs = self._get_observation()
        
        # 将观察转换为向量
        # 这里简化处理，实际应用中可能需要更复杂的向量化方法
        state_vector = np.concatenate([
            obs['1m'].flatten(),
            obs['15m'].flatten(),
            obs['state'].flatten()
        ])
        
        return state_vector
    
    def step(self, action: int) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """
        执行一步交易
        
        Args:
            action: 动作
            
        Returns:
            观察, 奖励, 是否结束, 是否截断, 信息
        """
        # 获取当前状态向量
        state_vector = self._get_state_vector()
        
        # 执行基础环境的step
        obs, reward, done, truncated, info = super().step(action)
        
        # 记录交易决策
        decision_id = f"{self.uuid}_{self.current_step}_{uuid.uuid4().hex[:8]}"
        self.vector_store.record_trade_decision(
            decision_id=decision_id,
            state_vector=state_vector,
            action=action,
            reward=reward,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "price": self._current_price(),
                "position": self.position.side,
                "balance": self.balance,
                "step": self.current_step
            }
        )
        
        # 查询相似的历史决策
        similar_decisions = self.vector_store.query_similar_decisions(
            state_vector=state_vector,
            n_results=3
        )
        
        # 将相似决策信息添加到info中
        if similar_decisions and len(similar_decisions['ids']) > 0:
            info['similar_decisions'] = {
                'ids': similar_decisions['ids'][0],
                'metadatas': similar_decisions['metadatas'][0]
            }
        
        return obs, reward, done, truncated, info
    
    def reset(self, seed: Optional[int] = None) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        重置环境
        
        Args:
            seed: 随机种子
            
        Returns:
            初始观察, 信息
        """
        obs, info = super().reset(seed)
        
        # 获取初始状态向量并存储
        state_vector = self._get_state_vector()
        state_id = f"{self.uuid}_init_{uuid.uuid4().hex[:8]}"
        
        self.vector_store.add_market_state(
            state_id=state_id,
            state_vector=state_vector,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "step": self.current_step,
                "is_initial": True
            }
        )
        
        return obs, info