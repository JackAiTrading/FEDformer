"""
向量存储模块 - 使用 Chroma 存储和检索市场状态向量
"""

import os
import numpy as np
import chromadb
from chromadb.config import Settings
from typing import Dict, List, Any, Optional, Union
from utils.logger import Logger

logger = Logger.get_logger()

class VectorStore:
    """向量存储类，用于存储和检索市场状态向量"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化向量存储
        
        Args:
            config: 配置信息
        """
        self.config = config
        
        # 创建向量存储目录
        self.vector_dir = os.path.join(config['root_dir'], 'vector_store')
        os.makedirs(self.vector_dir, exist_ok=True)
        
        # 初始化 Chroma 客户端
        self.client = chromadb.PersistentClient(
            path=self.vector_dir,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # 创建或获取集合
        self.market_states = self.client.get_or_create_collection(
            name="market_states",
            metadata={"description": "市场状态向量"}
        )
        
        self.trade_patterns = self.client.get_or_create_collection(
            name="trade_patterns",
            metadata={"description": "交易模式向量"}
        )
        
        self.trade_decisions = self.client.get_or_create_collection(
            name="trade_decisions",
            metadata={"description": "交易决策记录"}
        )
        
        logger.info(f"向量存储初始化完成: {self.vector_dir}")
    
    def add_market_state(self, state_id: str, state_vector: np.ndarray, 
                         metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        添加市场状态向量
        
        Args:
            state_id: 状态ID
            state_vector: 状态向量
            metadata: 元数据
        """
        if metadata is None:
            metadata = {}
            
        self.market_states.add(
            ids=[state_id],
            embeddings=[state_vector.tolist()],
            metadatas=[metadata]
        )
    
    def query_similar_states(self, query_vector: np.ndarray, n_results: int = 5) -> Dict[str, Any]:
        """
        查询相似的市场状态
        
        Args:
            query_vector: 查询向量
            n_results: 返回结果数量
            
        Returns:
            相似状态列表
        """
        results = self.market_states.query(
            query_embeddings=[query_vector.tolist()],
            n_results=n_results
        )
        return results
    
    def add_trade_pattern(self, pattern_id: str, pattern_vector: np.ndarray, 
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        添加交易模式向量
        
        Args:
            pattern_id: 模式ID
            pattern_vector: 模式向量
            metadata: 元数据
        """
        if metadata is None:
            metadata = {}
            
        self.trade_patterns.add(
            ids=[pattern_id],
            embeddings=[pattern_vector.tolist()],
            metadatas=[metadata]
        )
    
    def record_trade_decision(self, decision_id: str, state_vector: np.ndarray, 
                              action: int, reward: float,
                              metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        记录交易决策
        
        Args:
            decision_id: 决策ID
            state_vector: 状态向量
            action: 执行的动作
            reward: 获得的奖励
            metadata: 元数据
        """
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "action": action,
            "reward": reward,
            "timestamp": metadata.get("timestamp", "")
        })
        
        self.trade_decisions.add(
            ids=[decision_id],
            embeddings=[state_vector.tolist()],
            metadatas=[metadata]
        )
    
    def query_similar_decisions(self, state_vector: np.ndarray, 
                               n_results: int = 5) -> Dict[str, Any]:
        """
        查询相似的交易决策
        
        Args:
            state_vector: 状态向量
            n_results: 返回结果数量
            
        Returns:
            相似决策列表
        """
        results = self.trade_decisions.query(
            query_embeddings=[state_vector.tolist()],
            n_results=n_results
        )
        return results