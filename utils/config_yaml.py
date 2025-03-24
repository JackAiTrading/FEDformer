"""
配置管理模块
"""

import os
import yaml
from dotenv import load_dotenv
from typing import Any, Dict, Optional
from . import singleton


@singleton
class ConfigYaml:
    """配置管理器"""

    def __init__(self, path: str='/config/', custom:str = 'default'):
        """
        初始化配置管理器
        
        Args:
            path: 配置文件路径
            custom: 自定义配置文件名
        """
        self._path: str = path
        self._custom: str = custom

        # 加载配置
        self._config: Dict[str, Any] = self.load()

    def reload(self):
        """重新加载配置"""
        self._config = self.load()

    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        root = os.path.dirname(os.path.abspath(__file__))
        root = os.path.dirname(root)
        base = os.path.join(root, self._path, f'{self._custom}.yaml')
        if not os.path.exists(base):
            base = os.path.join(root, self._path, f'base.yaml')
            if not os.path.exists(base):
                raise FileNotFoundError(f"Config base file not found: {base}")

        custom = os.path.join(root, self._path, f'custom-{self._custom}.yaml')
        if not os.path.exists(custom):
            custom = os.path.join(root, self._path, f'custom-default.yaml')
            if not os.path.exists(custom):
                raise FileNotFoundError(f"Config custom file not found: {custom}")

        with open(base, 'r', encoding='utf-8') as f:
            baseC = yaml.safe_load(f)

        with open(custom, 'r', encoding='utf-8') as f:
            customC = yaml.safe_load(f)

        config = merge(baseC, customC)
        config = replace(config)
        return config

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            value = self._config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def all(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config

def replace(config: Dict[str, Any]) -> Dict[str, Any]:
    # 加载环境变量
    load_dotenv()

    # 替换环境变量
    if 'binance' in config:
        config['binance']['api_key'] = os.getenv('BINANCE_API_KEY', '')
        config['binance']['api_secret'] = os.getenv('BINANCE_API_SECRET', '')
        config['binance']['testnet'] = os.getenv('BINANCE_API_TYPE', '')

    # 根目录
    if 'root_dir' in config:
        config['root_dir'] = os.getenv('ROOT_DIR', '')

    # 钉钉通知配置
    if 'dingding_token' in config:
        config['dingding_token'] = os.getenv('DINGDING_TOKEN', '')

    # 目录替换成绝对路径
    config['tensorboard_log'] = os.path.join(config['root_dir'], config['tensorboard_log'])

    config['log_dir'] = os.path.join(config['root_dir'], config['log_dir'])
    config['cache_dir'] = os.path.join(config['root_dir'], config['cache_dir'])
    config['model_dir'] = os.path.join(config['root_dir'], config['model_dir'])
    config['data_dir'] = os.path.join(config['root_dir'], config['data_dir'])
    config['template_dir'] = os.path.join(config['root_dir'], config['template_dir'])

    return config

def merge(config1: Dict, config2: Dict) -> Dict:
    """
    递归合并配置

    Args:
        config1: 基础配置
        config2: 自定义配置

    Returns:
        Dict: 合并后的配置
    """
    merged = config1.copy()

    for key, value in config2.items():
        if (
                key in merged and
                isinstance(merged[key], dict) and
                isinstance(value, dict)
        ):
            merged[key] = merge(merged[key], value)
        else:
            merged[key] = value

    return merged
