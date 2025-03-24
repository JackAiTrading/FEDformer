import os
import portalocker
import pickle
import hashlib
import threading
from typing import Any, Optional
import time

class CacheFeatureFile:
    """
    基于文件系统的缓存管理器，支持高并发访问
    """
    _instances = {}
    _lock = threading.Lock()

    def __init__(self, cache_dir: str, prefix: str = "cache", subdir_length: int = 3):
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
    def get_instance(cls, cache_dir: str, prefix: str = "cache", subdir_length: int = 3) -> 'CacheFeatureFile':
        """
        获取缓存管理器实例（单例模式）
        """
        key = f"{cache_dir}_{prefix}_{subdir_length}"
        if key not in cls._instances:
            with cls._lock:
                if key not in cls._instances:
                    cls._instances[key] = cls(cache_dir, prefix, subdir_length)
        return cls._instances[key]

    def _get_cache_key(self, *args, **kwargs) -> str:
        """
        生成缓存键
        """
        # 将所有参数转换为字符串并连接
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = "_".join(key_parts)
        
        # 使用MD5生成固定长度的键
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> str:
        """
        获取缓存文件路径
        """
        # 使用缓存键的前几个字符作为子目录名
        subdir = cache_key[:self.subdir_length]
        subdir_path = os.path.join(self.cache_dir, subdir)
        os.makedirs(subdir_path, exist_ok=True)
        return os.path.join(subdir_path, f"{self.prefix}_{cache_key}.pkl")

    def get(self,t="15m", start=0, end=0, step_1m=0,  *args, **kwargs) -> Optional[Any]:
        """
        获取缓存数据
        """
        cache_key = f"{start}_{end}_{step_1m}_{t}"
        cache_path = self._get_cache_path(cache_key)
        
        try:
            if os.path.exists(cache_path):
                # 大小是否小于10字节
                if os.path.getsize(cache_path) < 10:
                    # 看是否大于10秒
                    if time.time() - os.path.getmtime(cache_path) < 10:
                        os.remove(cache_path)
                    return None
                with open(cache_path, 'rb') as f:
                    # 加锁
                    portalocker.lock(f, portalocker.LOCK_SH)  # 共享锁（读锁）
                    try:
                        data = pickle.load(f)
                        return data
                    except :
                        return None
                    finally:
                        portalocker.unlock(f) # 解锁
        except (OSError, pickle.PickleError) as e:
            print(f"Error reading cache: {e} 88 f:{cache_path}")
            # 如果读取失败，删除可能损坏的缓存文件
            try:
                if time.time() - os.path.getmtime(cache_path) < 10:
                    os.remove(cache_path)
            except OSError:
                pass
            return None
        except Exception as e:
            if os.path.getsize(cache_path) < 10: # 看是否大于10秒
                if time.time() - os.path.getmtime(cache_path) < 10:
                    os.remove(cache_path)
            print(f"Error reading cache: {e} 99 f:{cache_path}")
        return None

    def set(self, value: Any, t="15m", start=0, end=0, step_1m=0, *args, **kwargs) -> None:
        """
        设置缓存数据
        """
        # cache_key = self._get_cache_key(*args, **kwargs)
        cache_key = f"{start}_{end}_{step_1m}_{t}"
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'wb') as f:
                # 加锁
                portalocker.lock(f, portalocker.LOCK_EX)  # 独占锁（写锁）
                try:
                    pickle.dump(value, f)
                    f.flush()  # 确保数据写入磁盘
                finally:
                    # 解锁
                    portalocker.unlock(f)
        except (OSError, pickle.PickleError) as e:
            # 如果写入失败，删除可能损坏的缓存文件
            try:
                if time.time() - os.path.getmtime(cache_path) < 10:
                    os.remove(cache_path)
            except OSError:
                pass
        except Exception as e:
            if os.path.getsize(cache_path) < 10: # 看是否大于10秒
                if time.time() - os.path.getmtime(cache_path) < 10:
                    os.remove(cache_path)
            print(f"Error writing cache: {e} 112 f:{cache_path}")

    def clear(self) -> None:
        """
        清除所有缓存数据
        """
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
        except OSError as e:
            print(f"Error clearing cache: {e}")

    def clear_expired(self, max_age_seconds: int) -> None:
        """
        清除过期的缓存文件
        
        Args:
            max_age_seconds: 缓存文件的最大年龄（秒）
        """
        try:
            current_time = time.time()
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    if file.endswith('.pkl'):
                        file_path = os.path.join(root, file)
                        if current_time - os.path.getmtime(file_path) > max_age_seconds:
                            try:
                                os.remove(file_path)
                            except OSError:
                                pass
                # 删除空目录
                for dirV in dirs:
                    dir_path = os.path.join(root, dirV)
                    try:
                        os.rmdir(dir_path)
                    except OSError:
                        # 目录不为空或其他错误，跳过
                        pass
        except OSError as e:
            print(f"Error clearing expired cache: {e}")
