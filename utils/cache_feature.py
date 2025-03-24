import os
import threading

class CacheFeature:
    """
    基于文件系统的缓存管理器，支持高并发访问
    """
    _instances = {}
    _lock = threading.Lock()

    def __init__(self, cache_dir: str, prefix: str = "cache", subdir_length: int = 3,
                 fred: str = "1m", db_path: str = "resource/cache/normalized_data.db", window_size:int = 512):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
            prefix: 缓存文件前缀
            subdir_length: 用于创建子目录的缓存键前缀长度
        """
        self.cache_dir = cache_dir
        self.prefix = prefix
        self.subdir_length = subdir_length
        os.makedirs(cache_dir, exist_ok=True)

    @classmethod
    def get_instance(cls, cache_dir: str, prefix: str = "cache", subdir_length: int = 3) -> 'CacheFeature':
        """
        获取缓存管理器实例（单例模式）
        """
        key = f"{cache_dir}_{prefix}_{subdir_length}"
        if key not in cls._instances:
            with cls._lock:
                if key not in cls._instances:
                    cls._instances[key] = cls(cache_dir, prefix, subdir_length)
        return cls._instances[key]