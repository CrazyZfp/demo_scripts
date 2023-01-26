from model import Quote, Assets, TradingLog
from typing import List, Tuple
import pandas as pd
from bolling import boll_bands, bb_percent_calculate


class Strategy:
    quotes: List[Quote]
    assets: Assets
    trading_logs: List[TradingLog]

    def calcute_indices(self):
        pass

    def execute(self) -> Tuple[int, int, float, str]:
        pass


class BollingStrategy(Strategy):
    n: int
    k: int

    def __init__(self, n:int= 15, k:int=2) -> None:
        super().__init__()
        self.n = n
        self.k = k

    def calcute_indices(self):
        close_list = []
        date_list = []
        for q in self.quotes:
            close_list.append(q.close)
            date_list.append(q.date)

        df = pd.Series(close_list, name='Close')
        df = pd.DataFrame(df)  # 得到的数据中index直接就是Date

        date = pd.Series(date_list, name='date')
        df = df.join(date)

        date = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        df = boll_bands(df, self.n, self.k)
        self.df = bb_percent_calculate(df, self.n, self.k)

    def execute(self) -> Tuple[int, int, float, str]:
        return super().execute()