from model import Quote, Assets, TradingLog
from constants import Confidence, Direction, Trend
from typing import List, Tuple, Iterator
import pandas as pd
from bolling import boll_bands, bb_percent_calculate


class Strategy:
    quotes: List[Quote]
    assets: Assets
    trading_logs: List[TradingLog]

    def calcute_indices(self):
        pass

    def evaluate(self) -> Iterator[Tuple[Direction, Confidence, float, str]]:
        """
        :return 交易方向, 置信度, 价格, 日期
        """
        pass


class BollingStrategy(Strategy):
    n: int
    k: int

    def __init__(self, n: int = 15, k: int = 2) -> None:
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

        df = boll_bands(df, self.n, self.k)
        self.df = bb_percent_calculate(df, self.n, self.k)

    def evaluate(self) -> Iterator[Tuple[Direction, Confidence, float, str]]:
        pre_trend: Trend = None
        for idx, row in self.df[self.df.p_avg3.notnull()].iterrows():
            if idx == 0 or self.df.iloc[[idx - 1]].p_avg3.isnull().bool():
                continue
            if row.p_avg3 < self.df.iloc[[idx - 1]].p_avg3.item():
                cur_trend: Trend = Trend.DOWN
            elif row.p_avg3 > self.df.iloc[[idx - 1]].p_avg3.item():
                cur_trend: Trend = Trend.UP
            else:
                cur_trend: Trend = Trend.HORIZONTAL

            if pre_trend is None:
                pass
            elif pre_trend == cur_trend or cur_trend == Trend.HORIZONTAL:
                continue
            elif cur_trend == Trend.UP:
                yield Direction.BUY, Confidence.HIGH if row.p_avg3 < -1 else Confidence.MIDDLE_LOW, row.Close, row.date
            else:
                yield Direction.SELL, Confidence.HIGH, row.Close, row.date
            pre_trend = cur_trend