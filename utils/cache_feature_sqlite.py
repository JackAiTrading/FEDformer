import sqlite3
import pickle

from utils.logger import Logger

logger = Logger.get_logger()


class CacheFeatureSQLite:
    """
    使用 SQLite 存储滑动窗口归一化数据的缓存类。
    """

    def __init__(self, k: str = "1m", db_path: str = "resource/cache/normalized_data.db", window_size:int = 512):
        """
        初始化缓存类。

        :param db_path: SQLite 数据库文件路径
        """
        self.db_path: str = db_path
        self.table: str = f"sqlite_cache_{k}_ws{window_size}"
        self.f_s: str = "s"  # start_idx
        self.f_e: str = "e"  # end_idx
        self.f_d: str = "d"  # data
        self.connection = sqlite3.connect(self.db_path)
        self._create_table()

    def _create_table(self):
        """
        创建用于存储窗口数据的表（如果不存在）。
        """
        query = f"CREATE TABLE IF NOT EXISTS `{self.table}` (`{self.f_s}` INTEGER NOT NULL, `{self.f_e}` INTEGER NOT NULL, `{self.f_d}` BLOB NOT NULL, PRIMARY KEY (`{self.f_s}`, `{self.f_e}`));"
        # print(f"sql:{query}")
        self.connection.execute(query)
        self.connection.commit()
        logger.info(f"缓存{self.db_path}表已创建")

    def save(self, start_idx, end_idx, data):
        """
        保存窗口数据到 SQLite。

        :param start_idx: 窗口起始索引
        :param end_idx: 窗口结束索引
        :param data: 要保存的 DataFrame 数据
        """
        # 将 DataFrame 序列化为二进制
        data_blob = pickle.dumps(data)
        query = f"INSERT OR REPLACE INTO `{self.table}` (`{self.f_s}`, `{self.f_e}`, `{self.f_d}`) VALUES (?, ?, ?);"
        # print(f"sql:{query}")
        self.connection.execute(query, (start_idx, end_idx, data_blob))
        self.connection.commit()
        print(f"窗口 {start_idx}-{end_idx} 的数据已存储到缓存")

    def load(self, start_idx, end_idx):
        """
        从 SQLite 加载窗口数据。

        :param start_idx: 窗口起始索引
        :param end_idx: 窗口结束索引
        :return: 缓存的 DataFrame 数据，如果不存在返回 None
        """
        query = f"SELECT `{self.f_d}` FROM `{self.table}` WHERE `{self.f_s}` = ? AND `{self.f_e}` = ?;"
        # print(f"sql:{query}")
        cursor = self.connection.execute(query, (start_idx, end_idx))
        row = cursor.fetchone()
        if row:
            data_blob = row[0]
            return pickle.loads(data_blob)
        return None

    def exists(self, start_idx, end_idx):
        """
        检查指定窗口是否已存在缓存。

        :param start_idx: 窗口起始索引
        :param end_idx: 窗口结束索引
        :return: 布尔值，表示缓存是否存在
        """
        query = f"SELECT 1 FROM `{self.table}` WHERE `{self.f_s}` = ? AND `{self.f_e}` = ?;"
        # print(f"sql:{query}")
        cursor = self.connection.execute(query, (start_idx, end_idx))
        return cursor.fetchone() is not None

    def delete(self, start_idx, end_idx):
        """
        删除指定窗口的数据。

        :param start_idx: 窗口起始索引
        :param end_idx: 窗口结束索引
        """
        query = f"DELETE FROM `{self.table}` WHERE `{self.f_s}` = ? AND `{self.f_e}` = ?;"
        # print(f"sql:{query}")
        self.connection.execute(query, (start_idx, end_idx))
        self.connection.commit()
        print(f"窗口 {start_idx}-{end_idx} 的数据已从缓存中删除")

    def close(self):
        """
        关闭数据库连接。
        """
        self.connection.close()
        print("数据库连接已关闭")
