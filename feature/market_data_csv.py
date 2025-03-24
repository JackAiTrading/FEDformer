import glob
import requests
import os

import pandas as pd
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from utils.logger import Logger
from .market_data import MarketData

logger = Logger.get_logger()




class MarketDataCSV(MarketData):
    def __init__(self, config:Dict[str,Any]):
        super().__init__(base_dir=config['data_dir'])
        # 币安数据前
        self.data_binance_url = "https://data.binance.vision/data/spot/monthly/klines"


    def down_klines(self, symbol:str, fred:str, months:int = 12)->int:
        """
        下载对应的数据
        Args:
            symbol: 交易对
            fred: k线图时间频率
            months: 从现有开始下载月份

        Returns:
            成功数量

        """
        rs = 0
        end_date_month = datetime.now()
        start_date = end_date_month - relativedelta(months=months)
        current_date = start_date
        while current_date < end_date_month:
            year = current_date.year
            month = current_date.strftime("%m")
            url = f"{self.data_binance_url}/{symbol}/{fred}/{symbol}-{fred}-{year}-{month}.zip"
            try:
                # 下载url
                file_dir = f"{self.base_dir}/{symbol}-{fred}/"
                # 目录是否存在
                if not os.path.exists(file_dir):
                    os.makedirs(file_dir,  exist_ok=True)
                file_csv = f"{self.base_dir}/{symbol}-{fred}/{symbol}-{fred}-{year}-{month}.csv"
                # 文件是否存在
                if os.path.exists(file_csv):
                    print(f"文件已存在:{file_csv}")
                    rs += 1
                    current_date += relativedelta(months=1)
                    continue
                file_zip = f"{self.base_dir}/{symbol}-{fred}/{symbol}-{fred}-{year}-{month}.zip"
                if os.path.exists(file_zip):
                    print(f"文件已存在:{file_zip}")
                    rs += 1
                    current_date += relativedelta(months=1)
                    continue
                rs += 1
                print("下载:", url)
                self.save_file(url, f"{self.base_dir}/{symbol}-{fred}/{symbol}-{fred}-{year}-{month}.zip")
            except Exception as e:
                logger.error(f"下载 {year}-{month} 数据失败: {str(e)}")
            current_date += relativedelta(months=1)
        return rs


    @staticmethod
    def save_file(url, save_path=None):
        # 如果没有指定保存路径，默认使用URL中的文件名
        if save_path is None:
            save_path = url.split('/')[-1]

        try:
            # 发送GET请求
            response = requests.get(url, stream=True)
            # 检查请求是否成功
            response.raise_for_status()

            # 获取文件大小（如果有的话）
            total_size = int(response.headers.get('content-length', 0))

            # 以二进制写入模式打开文件
            with open(save_path, 'wb') as file:
                # 分块下载
                chunk_size = 8192  # 每次下载8KB
                downloaded_size = 0

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # 过滤掉keep-alive新块
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        # 显示下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f'\r下载进度: {progress:.2f}%', end='')

            print(f'\n文件已下载完成: {save_path}')
            return True

        except requests.RequestException as e:
            print(f'下载出错: {e}')
            return False

    def load_csv(self, symbol: str = "BTCUSDT", fred: str = "1m", months: int = 0) -> pd.DataFrame:
        """
        加载指定时间段的数据

        Args:
            symbol: 交易对
            fred: k线图时间频率
            months: 月份数

        Returns:
            pd.DataFrame: 数据
        """
        try:
            base_path = f"{self.base_dir}/{symbol}-{fred}"
            logger.info(f"Base path: {base_path}")

            # 检查目录是否存在
            if not os.path.exists(base_path):
                logger.error(f"Directory does not exist: {base_path}")
                return pd.DataFrame()

            # 获取所有数据文件
            glob_pattern = os.path.join(base_path, f"{symbol}-{fred}-*-*.csv")
            # logger.info(f"Glob pattern: {glob_pattern}")

            files = sorted(glob.glob(glob_pattern))
            logger.info(f"Found {len(files)} files")
            if not files:
                logger.error("No files found matching the pattern")
                # 列出目录内容以供调试
                if os.path.exists(base_path):
                    logger.info(f"Directory contents: {os.listdir(base_path)}")
                return pd.DataFrame()

            # 选择指定数量的月份
            selected_files = files
            if months > 0:
                selected_files = files[-months:]  # 选择最后几个月的数据

            # 加载并合并数据
            dfs = []
            for file in selected_files:
                df = pd.read_csv(file)
                df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
                df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
                dfs.append(df)

            # 检查dfs每行每个字段是否为空或为0，如果为空或为0，填充为上一行本字段的值
            for df in dfs:
                for col in df.columns:
                    # 先处理空值
                    df[col] = df[col].ffill()
                    # 再处理0值
                    mask = df[col] == 0
                    if mask.any():
                        df.loc[mask, col] = None
                        df[col] = df[col].ffill()


            return pd.concat(dfs, ignore_index=True)
        except Exception as e:
            logger.error(f"Failed to load CSV data: {e}")
            return pd.DataFrame()

