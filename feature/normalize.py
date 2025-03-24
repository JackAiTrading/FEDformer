import numpy as np


def normalize_features(is_normalize: bool, features: np.ndarray) -> np.ndarray:
    """
    归一化特征

    Args:
        is_normalize: 是否进行归一化
        features: 原始特征

    Returns:
        归一化后的特征
    """
    if not is_normalize:
        return features

    # 使用最小-最大归一化
    min_vals = np.min(features, axis=0, keepdims=True)
    max_vals = np.max(features, axis=0, keepdims=True)

    # 避免除以0
    range_vals = max_vals - min_vals
    range_vals[range_vals == 0] = 1

    normalized = (features - min_vals) / range_vals
    return normalized