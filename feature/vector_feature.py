"""
向量特征提取模块
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer
from torch import Tensor

from utils.logger import Logger

logger = Logger.get_logger()

class VectorFeature:
    """向量特征提取类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化向量特征提取器
        
        Args:
            config: 配置信息
        """
        self.config = config
        
        # 加载预训练模型用于文本向量化
        # 这里使用sentence-transformers，也可以根据需要使用其他模型
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        logger.info("向量特征提取器初始化完成")
    
    def market_to_text(self, df: pd.DataFrame, window: int = 10) -> str:
        """
        将市场数据转换为文本描述
        
        Args:
            df: 市场数据
            window: 窗口大小
            
        Returns:
            文本描述
        """
        # 获取最近的窗口数据
        recent_data = df.iloc[-window:].copy()
        
        # 计算基本统计信息
        price_change = (recent_data['close'].iloc[-1] / recent_data['close'].iloc[0] - 1) * 100
        volume_change = (recent_data['volume'].iloc[-1] / recent_data['volume'].iloc[0] - 1) * 100
        
        # 判断趋势
        trend = "上涨" if price_change > 0 else "下跌"
        
        # 构建文本描述
        text = f"市场在过去{window}个时间单位{trend}了{abs(price_change):.2f}%。"
        text += f"交易量变化了{volume_change:.2f}%。"
        
        # 添加技术指标描述
        if 'rsi' in recent_data.columns:
            rsi = recent_data['rsi'].iloc[-1]
            text += f"RSI指标为{rsi:.2f}，"
            if rsi > 70:
                text += "市场可能超买。"
            elif rsi < 30:
                text += "市场可能超卖。"
            else:
                text += "市场处于中性区域。"
        
        if 'macd' in recent_data.columns and 'macd_signal' in recent_data.columns:
            macd = recent_data['macd'].iloc[-1]
            signal = recent_data['macd_signal'].iloc[-1]
            text += f"MACD为{macd:.2f}，信号线为{signal:.2f}，"
            if macd > signal:
                text += "MACD显示看涨信号。"
            else:
                text += "MACD显示看跌信号。"
        
        return text
    
    def vectorize_market_state(self, df_1m: pd.DataFrame, df_15m: pd.DataFrame) -> Tensor:
        """
        将市场状态向量化
        
        Args:
            df_1m: 1分钟K线数据
            df_15m: 15分钟K线数据
            
        Returns:
            市场状态向量
        """
        # 生成市场文本描述
        text_1m = self.market_to_text(df_1m, window=20)
        text_15m = self.market_to_text(df_15m, window=10)
        
        combined_text = f"1分钟K线: {text_1m} 15分钟K线: {text_15m}"
        
        # 使用预训练模型将文本转换为向量
        vector = self.text_model.encode(combined_text)
        
        return vector
    
    def vectorize_pattern(self, pattern_name: str, pattern_description: str) -> Tensor:
        """
        将交易模式向量化
        
        Args:
            pattern_name: 模式名称
            pattern_description: 模式描述
            
        Returns:
            模式向量
        """
        combined_text = f"{pattern_name}: {pattern_description}"
        vector = self.text_model.encode(combined_text)
        return vector
    
    def vectorize_numerical_features(self, features: np.ndarray) -> np.ndarray:
        """
        将数值特征向量化
        
        Args:
            features: 数值特征数组
            
        Returns:
            向量化后的特征
        """
        # 对于数值特征，可以直接使用或进行归一化处理
        # 这里简单地返回原始特征，实际应用中可能需要更复杂的处理
        return features
    
    def combine_vectors(self, vectors: List[np.ndarray]) -> np.ndarray:
        """
        组合多个向量
        
        Args:
            vectors: 向量列表
            
        Returns:
            组合后的向量
        """
        # 简单的向量拼接
        # 实际应用中可能需要更复杂的组合方法
        return np.concatenate(vectors)
    
    def extract_features(self, df_1m: pd.DataFrame, df_15m: pd.DataFrame, 
                         position_info: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        提取完整的特征向量
        
        Args:
            df_1m: 1分钟K线数据
            df_15m: 15分钟K线数据
            position_info: 持仓信息
            
        Returns:
            特征向量
        """
        # 提取市场状态向量
        market_vector = self.vectorize_market_state(df_1m, df_15m)
        
        # 提取数值特征
        numerical_features = []
        
        # 从1分钟数据中提取关键指标
        if len(df_1m) > 0:
            last_row = df_1m.iloc[-1]
            numerical_features.extend([
                last_row.get('close', 0),
                last_row.get('volume', 0),
                last_row.get('rsi', 50) if 'rsi' in last_row else 50,
                last_row.get('macd', 0) if 'macd' in last_row else 0
            ])
        
        # 从15分钟数据中提取关键指标
        if len(df_15m) > 0:
            last_row = df_15m.iloc[-1]
            numerical_features.extend([
                last_row.get('close', 0),
                last_row.get('volume', 0),
                last_row.get('rsi', 50) if 'rsi' in last_row else 50,
                last_row.get('macd', 0) if 'macd' in last_row else 0
            ])
        
        # 添加持仓信息
        if position_info:
            numerical_features.extend([
                position_info.get('side', 0),
                position_info.get('size', 0),
                position_info.get('entry_price', 0),
                position_info.get('unrealized_pnl', 0),
                position_info.get('holding_time', 0)
            ])
        
        # 向量化数值特征
        numerical_vector = self.vectorize_numerical_features(np.array(numerical_features))
        
        # 组合所有向量
        combined_vector = self.combine_vectors([market_vector, numerical_vector])
        
        return combined_vector