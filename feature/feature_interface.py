import pandas as pd
import talib as ta
from sklearn.preprocessing import MinMaxScaler

from utils import singleton

from typing import Dict

# 指标列
COLUMNS = [
    # 基础数据
    'open', 'high', 'low', 'close',
    'volume', 'quote_volume',
    'taker_buy_volume', 'taker_buy_quote_volume',

    # 趋势指标
    'ma5', 'ma10', 'ma20', 'ma60',
    'ema12', 'ema26',

    # MACD
    'macd', 'macd_signal', 'macd_hist',

    # RSI
    'rsi6', 'rsi12', 'rsi24',

    # 动量指标
    'cci20', 'cci50',

    # 资金流量指标
    'mfi',

    # 量比（5日平均）
    'vr',

    # 布林带
    'boll_upper', 'boll_middle', 'boll_lower',

    # KDJ
    'k', 'd', 'j',  # 随机指标（%K 14日，%D 3日）
]

# 内存-特征缓存类型
CacheTypeMemory: str = "memory"

# 文件-特征缓存类型
CacheTypeFile: str = "file"

# SQLite-特征缓存类型
CacheTypeSqlite: str = "sqlite"


@singleton
class Feature:
    def __init__(self, config: Dict[str, any] = None):
        """
        初始化特征收集器
        :param config: 配置
        """
        self.symbol: str = config['symbol']  # 交易对
        self.months: int = config['months']  # 读取最近多少月份 数据
        self.df_1m: pd.DataFrame = pd.DataFrame()
        self.df_15m: pd.DataFrame = pd.DataFrame()
        # 最大技术指标窗口
        self.indicator_window_max: int = config['indicator_window_max']  # 指标窗口最大值
        self.cache_dir: str = config['cache_dir']  # 缓存目录
        self.cache_type: str = config['cache_type']  # 缓存类型
        return

    def load_1m_15m(self, symbol: str, config: dict[str, any]):
        """ 加载历史数据 """
        months = config['months']
        data_dir = config['data_dir']
        self.cache_dir = config['cache_dir']
        self.symbol = symbol
        self.months = months
        self.df_1m = load_csv(symbol=self.symbol, timeframe="1m", months=months, root_path=data_dir)
        self.df_15m = load_csv(symbol=self.symbol, timeframe="15m", months=months, root_path=data_dir)
        # 添加技术指标
        self.df_1m = self.add_indicators(self.df_1m)
        self.df_15m = self.add_indicators(self.df_15m)
        return

    def len(self):
        """ 获取数据长度 """
        return len(self.df_1m)

    def current_price(self, current_step: int) -> float:
        """ 获取当前价格 """
        return self.df_1m['close'].iloc[current_step]

    def max_indicator_window(self):
        """ 获取最大技术指标窗口 """
        return self.window_start

    def observation(self, current_step: int, window_size: int) -> Dict[str, pd.DataFrame]:
        """ 获取当前状态 """
        # 计算起始和结束索引
        start_idx, end_idx = current_step - window_size, current_step

        # logging.info(f"Getting 1m features: {start_idx} -> {end_idx}")
        # 使用共享缓存计算1m数据
        # cache_key_1m = f"1m_{start_idx}_{end_idx}"
        # if cache_key_1m in _shared_cache_1m:
        #     # logging.info(f"1m cache hit: {cache_key_1m}")
        #     f_1m = _shared_cache_1m[cache_key_1m]
        # else:
        #     # logging.info(f"1m cache miss: {cache_key_1m}")
        #     f_1m = self.calc_feature(start_idx=start_idx, current_step=end_idx)
        #     _shared_cache_1m[cache_key_1m] = f_1m
        #     # logging.info(f"1m features calculated and cached")
        f_1m = self.calc_feature(start_idx=start_idx, current_step=end_idx)

        # 计算15m的索引
        current_step_15m = current_step // 15
        start_idx_15m, end_idx_15m = current_step_15m - window_size, current_step_15m

        # logging.info(f"Getting 15m features: {start_idx_15m} -> {end_idx_15m}")
        # 使用共享缓存计算15m数据
        # cache_key_15m = f"15m_{start_idx_15m}_{end_idx_15m}_{current_step}"
        # if cache_key_15m in _shared_cache_15m:
        #     # logging.info(f"15m cache hit: {cache_key_15m}")
        #     f_15m = _shared_cache_15m[cache_key_15m]
        # else:
        #     # logging.info(f"15m cache miss: {cache_key_15m}")
        #     f_15m = self.calc_feature_15m(start_idx=start_idx_15m, current_step=end_idx_15m, step_1m=current_step)
        #     _shared_cache_15m[cache_key_15m] = f_15m
        #     # logging.info(f"15m features calculated and cached")

        f_15m = self.calc_feature_15m(start_idx=start_idx_15m, current_step=end_idx_15m, step_1m=current_step)

        # 返回数据
        return {'1m': f_1m, '15m': f_15m}

    def calc_feature(self, start_idx, current_step: int) -> pd.DataFrame:
        """
        获取当前状态

        Returns:
            当前状态的字典，包含1m和15m的特征和指标数据，以及持仓状态
        """
        try:
            # 获取当前时间窗口的数据
            # 'open', 'high', 'low', 'close',
            # 'volume', 'quote_volume', 'taker_buy_volume', 'taker_buy_quote_volume',
            df = self.df_1m
            df_window: pd.DataFrame = df.iloc[start_idx:current_step]
            df_f: pd.DataFrame = df_window[COLUMNS]
            # df_i: pd.DataFrame = df_window[INDICATOR_COLUMNS]

            # print(f"Data shapes - df: {df.shape}, df_window: {df_window.shape}, df_f: {df_f.shape} ")

            # 检查是否有NaN值
            if df_f.isna().any().any():
                raise ValueError(
                    f"NaN values detected in features or indicators 1m start_idx:{start_idx} current_step:{current_step}")

            # 归一化
            df_f = self.calc_normalize(df_f)
            return df_f
        except Exception as e:
            print(f"Error getting observation: {str(e)}")
            print(f"Start index: {start_idx}, Current step: {current_step}")
            print(f"Window size: {current_step - start_idx}")
            raise

    def calc_feature_15m(self, start_idx, current_step, step_1m: int) -> pd.DataFrame:
        """
        获取当前状态

        Returns:
            当前状态的字典，包含1m和15m的特征和指标数据，以及持仓状态
        """
        try:
            # 获取当前时间窗口的数据
            # 'open', 'high', 'low', 'close',
            # 'volume', 'quote_volume', 'taker_buy_volume', 'taker_buy_quote_volume',
            # print(f"start_idx: {start_idx}, current_step: {current_step}, step_1m: {step_1m}")
            rem = step_1m % 15
            df = self.df_15m
            df_window: pd.DataFrame = df.iloc[start_idx:current_step]
            if rem > 0:
                df_window_1m = self.df_1m.iloc[step_1m - rem:step_1m]
                df_window2 = df_window.copy()

                open_value = df_window_1m.iloc[0]['open']
                high_value = df_window_1m.loc[df_window_1m['high'].idxmax()]['high']
                low_value = df_window_1m.loc[df_window_1m['low'].idxmin()]['low']
                close_value = df_window_1m.iloc[-1]['close']
                count = df_window_1m['count'].sum()
                volume_sum = df_window_1m['volume'].sum()
                quote_volume_sum = df_window_1m['quote_volume'].sum()
                taker_buy_volume_sum = df_window_1m['taker_buy_volume'].sum()
                taker_buy_quote_volume_sum = df_window_1m['taker_buy_quote_volume'].sum()
                summary_row = {
                    'open': open_value,
                    'high': high_value,
                    'low': low_value,
                    'close': close_value,
                    'volume': volume_sum / rem * 15,
                    'count': count / rem * 15,
                    'quote_volume': quote_volume_sum / rem * 15,
                    'taker_buy_volume': taker_buy_volume_sum / rem * 15,
                    'taker_buy_quote_volume': taker_buy_quote_volume_sum / rem * 15
                }
                # 将字典转化为 DataFrame
                summary_df = pd.DataFrame([summary_row])
                df_window2 = pd.concat([df_window2, summary_df], ignore_index=True)
                df_window2 = self.add_indicators(df_window2)
                df_window0 = pd.concat([df_window[1:], df_window2[-1:]], ignore_index=True)
                df_f: pd.DataFrame = df_window0[COLUMNS]
                # df_i: pd.DataFrame = df_window0[INDICATOR_COLUMNS]
                # print(f"Data shapes - df: {df.shape}, df_window: {df_window.shape}, df_f: {df_f.shape}")
                # 检查是否有NaN值
                if df_f.isna().any().any():
                    raise ValueError(
                        f"NaN values detected in features or indicators 15m start_idx:{start_idx} current_step:{current_step}")
                # 归一化
                df_f = self.calc_normalize(df_f)
                return df_f
            else:
                df_f: pd.DataFrame = df_window[COLUMNS]
                # df_i: pd.DataFrame = df_window[INDICATOR_COLUMNS]
                # print(
                #     f"Data shapes - df: {df.shape}, df_window: {df_window.shape}, df_f: {df_f.shape}")
                # 检查是否有NaN值
                if df_f.isna().any().any():
                    raise ValueError(
                        f"NaN values detected in features or indicators start_idx:{start_idx} current_step:{current_step}")
                # 归一化
                df_f = self.calc_normalize(df_f)
                return df_f
        except Exception as e:
            print(f"Error getting observation: {str(e)}")
            print(f"Start index: {start_idx}, Current step: {current_step}")
            print(f"Window size: {current_step - start_idx}")
            raise

    @staticmethod
    def calc_normalize(f: pd.DataFrame) -> pd.DataFrame:
        # 假设 df 是你的 DataFrame
        f0 = f.copy()
        columns_price = ['open', 'high', 'low', 'close',
                         'ma5', 'ma10', 'ma20', 'ma60',
                         'ema12', 'ema26', ]
        scaler_price = MinMaxScaler(feature_range=(0, 1))
        data = f0[columns_price].values.flatten().reshape(-1, 1)
        normalized_data = scaler_price.fit_transform(data)
        f0[columns_price] = normalized_data.reshape(f0[columns_price].shape)

        f1 = f0.copy()
        columns_0_1 = ['volume',
                       'quote_volume', 'taker_buy_volume', 'taker_buy_quote_volume', ]
        scaler_0_1 = MinMaxScaler(feature_range=(0, 1))
        f1[columns_0_1] = scaler_0_1.fit_transform(f1[columns_0_1])

        f2 = f1.copy()
        columns_neg_1_1 = [
            'boll_upper', 'boll_middle', 'boll_lower',
            # 动量指标
            'rsi6', 'rsi12', 'rsi24',  # 相对强弱指数（14日）
            'macd', 'macd_signal', 'macd_hist',  # MACD（默认12,26,9）
            # 'roc',  # 变动率（10日）
            # 'cmo',  # 钱德动量摆动指标（14日）
            'cci20', 'cci50',  # 商品通道指数（20日）
            'mfi',  # 资金流量指标（14日）
            # 'willr',  # 威廉指标（14日）

            # 波动率指标
            # 'natr',  # 归一化平均真实范围（14日）

            # 成交量指标
            # 'obv',  # 能量潮
            # 'ad',  # 累积/分配线
            # 'adosc',  # 震荡指标（3,10日）
            'vr',  # 量比（5日平均）

            # 趋势强度指标
            # 'adx',  # 平均趋向指标（14日）
            # 'dx',  # 动向指标（14日）
            # 'dmi_plus',  # DMI+
            # 'dmi_minus',  # DMI-

            # 阳光指标
            # 'aroon_down', 'aroon_up',

            # 市场情绪指标
            'k', 'd', 'j',  # 随机指标（%K 14日，%D 3日）
        ]
        scaler_neg_1_1 = MinMaxScaler(feature_range=(-1, 1))
        f2[columns_neg_1_1] = scaler_neg_1_1.fit_transform(f[columns_neg_1_1])
        return f2

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加技术指标"""
        # 复制数据以避免警告
        df = df.copy()

        # 价格数据
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values

        # 1. 简单移动平均线
        df['ma5'] = ta.SMA(close, timeperiod=5)
        df['ma10'] = ta.SMA(close, timeperiod=10)
        df['ma20'] = ta.SMA(close, timeperiod=20)
        df['ma60'] = ta.SMA(close, timeperiod=60)

        # 2. 指数移动平均线
        df['ema12'] = ta.EMA(close, timeperiod=12)
        df['ema26'] = ta.EMA(close, timeperiod=26)

        # 3. MACD
        macd, signal, hist = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist

        # 4. RSI
        df['rsi6'] = ta.RSI(close, timeperiod=6)
        df['rsi12'] = ta.RSI(close, timeperiod=12)
        df['rsi24'] = ta.RSI(close, timeperiod=24)

        # 5. 布林带
        upper, middle, lower = ta.BBANDS(close, timeperiod=20)
        df['boll_upper'] = upper
        df['boll_middle'] = middle
        df['boll_lower'] = lower

        # 6. KDJ
        df['k'], df['d'] = ta.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
        df['j'] = 3 * df['k'] - 2 * df['d']

        # 7. Volume Ratio - 量比（5日均量）
        df['vr'] = df['volume'] / df['volume'].rolling(window=5).mean()

        # 9. CCI - 顺势指标
        df['cci20'] = ta.CCI(high, low, close, timeperiod=20)
        df['cci50'] = ta.CCI(high, low, close, timeperiod=50)

        # 10. MFI - 资金流量指标
        df['mfi'] = ta.MFI(high, low, close, volume, timeperiod=14)

        # 最大技术指标窗口
        self.window_start = 60
        return df
