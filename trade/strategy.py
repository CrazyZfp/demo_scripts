from model import Quote, Assets, TradingLog
from constants import Confidence, Direction, Trend
from typing import List, Tuple, Iterator
import pandas as pd
from bolling import boll_bands, bb_percent_calculate
from indices import BollingPercent


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
        idx = BollingPercent()
        idx.dataframe_init(self.quotes)
        self.df = idx.traverse_cal()

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
            elif cur_trend == Trend.UP and self.df.iloc[[idx - 1
                                                         ]].p_avg3.item() < -1:
                yield Direction.BUY, Confidence.HIGH, row.close, row.date
            else:
                yield Direction.SELL, Confidence.HIGH, row.close, row.date
            pre_trend = cur_trend