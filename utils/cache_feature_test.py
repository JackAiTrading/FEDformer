import numpy as np
import pandas as pd
from .cache_feature_sqlite  import CacheFeatureSQLite

# 示例数据
data = {
    "rsi": np.random.rand(500),
    "macd": np.random.rand(500),
    "sma_10": np.random.rand(500),
}
df = pd.DataFrame(data)

# 滑动窗口大小
window_size = 512
cache = CacheFeatureSQLite(db_path="cache/normalized_data.db", window_size=window_size)

# 滑动窗口归一化和缓存
for start_idx in range(0, len(df), window_size):
    end_idx = min(start_idx + window_size, len(df))  # 防止越界

    # 检查缓存是否已存在
    if cache.exists(start_idx, end_idx):
        normalized_window = cache.load(start_idx, end_idx)
    else:
        # 提取当前窗口数据
        window_data = df.iloc[start_idx:end_idx]

        # 归一化处理（最小-最大归一化示例）
        normalized_window = (window_data - window_data.min()) / (window_data.max() - window_data.min())

        # 添加到缓存中
        cache.save(start_idx, end_idx, normalized_window)

    # 使用归一化数据（这里仅打印示例）
    print(f"窗口 {start_idx} - {end_idx} 的归一化数据:")
    print(normalized_window.head())

# 关闭数据库连接
cache.close()
