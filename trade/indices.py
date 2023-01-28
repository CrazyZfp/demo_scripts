from model import Quote
import json
from typing import List, Type, Set
import pandas as pd
from pandas import DataFrame
import numpy as np
import matplotlib.pyplot as plt



class Index:
    df: DataFrame
    rb_cols: Set[str]
    rb_idxs: List

    def __init__(self, rb_cols: Set[str] = None, rb_idxs: List = None):
        self.df = None
        self.rb_cols = rb_cols or {'date', 'close'}
        self.rb_idxs = rb_idxs or []

    def dataframe_init(self, quotes: List[Quote]):
        col_map = dict((col, []) for col in self.rb_cols)
        for rb_idx in self.rb_idxs:
            for col in rb_idx.rb_cols:
                if col not in col_map:
                    col_map[col] = []
        for q in quotes:
            q_jsn = q.to_json()
            for col, vals in col_map.items():
                vals.append(q_jsn[col])
        self.df = DataFrame(col_map)

    def current_cal(self) -> DataFrame:
        pass

    def draw(self):
        pass

    def traverse_cal(self, df: DataFrame = None) -> DataFrame:
        if df is None:
            df = self.df

        for rb_idx in self.rb_idxs:
            df = rb_idx.traverse_cal(df)

        self.df = df
        self.df = self.current_cal()
        return self.df


class Bolling(Index):
    k: int
    n: int

    def __init__(self, k=2, n=15):
        super().__init__()
        self.k = k
        self.n = n

    def current_cal(self) -> DataFrame:
        df = self.df
        ma = pd.Series(np.round(df.close.rolling(self.n).mean(), 2),
                       name=f'ma{self.n}')
        df = df.join(ma)

        # pandas.std() 默认是除以n-1 的，即是无偏的，如果想和numpy.std() 一样有偏，需要加上参数ddof=0
        std = pd.Series(np.round(df.close.rolling(self.n).std(ddof=0), 2),
                        name=f'std{self.n}')

        b_up = pd.Series(ma + (self.k * std), name='up')
        df = df.join(b_up)

        b_low = pd.Series(ma - (self.k * std), name='low')
        df = df.join(b_low)

        return df


class BollingPercent(Index):

    def __init__(self, n=15, **kwargs):
        self.n = n
        super().__init__(rb_idxs=[Bolling(k=kwargs.get('k', 2), n=n)])

    def current_cal(self) -> DataFrame:
        df = self.df
        df['percent'] = (df.close - df[f'ma{self.n}']) / (df.up -
                                                          df[f'ma{self.n}'])
        df['p_avg3'] = pd.Series(np.round(df['percent'].rolling(3).mean(), 2),
                                 name='p_avg3')
        return df

    def draw(self):
        ax = self.df.plot(y=['low', 'up', 'close', f'ma{self.n}'], x_compat=True)

        ax2 = ax.twinx()
        # ax2.bar(x=self.df.index, height=self.df.percent, color=(0, 1, 0, 0.3), zorder=5)
        ax2.bar(x=self.df.index, height=self.df.p_avg3,color=(1, 0, 0, 0.3),  zorder = 5)

        plt.grid()
        plt.show()

if __name__ == '__main__':
    # 通用配置 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    code = '600103.SH'
    start_date = '2020-01-01'
    end_date = '2023-01-18'

    # 数据预备 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    from mocker import cache_init, r, key_format
    from json_util import convert_list

    cache_init(code, start_date=start_date, end_date=end_date)
    key = key_format.format(code, start_date, end_date)
    quotes: List[Quote] = convert_list(json.loads(r.get(key)), List[Quote])

    # 指标计算 >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    idx_bolling_pct = BollingPercent()
    idx_bolling_pct.dataframe_init(quotes)
    idx_bolling_pct.traverse_cal()
    idx_bolling_pct.draw()