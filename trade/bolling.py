import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dtm
import requests
import json


def boll_bands(df, n, k):
    ma = pd.Series(np.round(df['Close'].rolling(n).mean(), 2), name=f'MA{n}')
    df = df.join(ma)

    # pandas.std() 默认是除以n-1 的，即是无偏的，如果想和numpy.std() 一样有偏，需要加上参数ddof=0
    # 此处添加ddof的原因是wind和yahoo的计算均采用的有偏值进行的计算
    std = pd.Series(np.round(df['Close'].rolling(n).std(ddof=0), 2),
                    name=f'std{n}')
    df = df.join(std)

    b_up = pd.Series(ma + (k * std), name='up')
    df = df.join(b_up)

    b_low = pd.Series(ma - (k * std), name='low')
    df = df.join(b_low)

    return df


def sohu_stock(stock: str, start_date: str, end_date: str):
    sohu_url = f"https://q.stock.sohu.com/hisHq?code={stock}&start={start_date.replace('-','')}&end={end_date}&stat=0&order=A&period=d&callback=historySearchHandler&rt=jsonp"
    resp = requests.get(url=sohu_url)

    prefix = 'historySearchHandler(['
    postfix = '])'
    json_body = json.loads(resp.text[len(prefix):(-len(postfix) - 1)])

    date_list = []
    close_list = []
    for dhq in json_body.get('hq'):
        date_list.append(dhq[0])
        close_list.append(float(dhq[2]))

    return date_list, close_list


def df_init(start_date: str, days: int, stock: str):
    sd = dtm.datetime.strptime(start_date, '%Y-%m-%d').date()
    ed = sd + dtm.timedelta(days=(days - 1))
    if ed > dtm.date.today():
        ed = dtm.date.today()
    end_date = dtm.datetime.strftime(ed, '%Y%m%d')

    date_list, close_list = sohu_stock(stock, start_date, end_date)
    df = pd.Series(close_list, name='Close')
    df = pd.DataFrame(df)  # 得到的数据中index直接就是Date

    date = pd.Series(date_list, name='date')
    df = df.join(date)

    date = pd.to_datetime(df['date'])
    # date = pd.date_range(start=start_date, periods=days, name='date')
    # df['date'] = date
    df.set_index('date', inplace=True)
    return df


def draw_figure(df: pd.DataFrame, n):
    ax = df.plot(y=['low', 'up', 'Close', f'MA{n}'], x_compat=True)
    # ax.set_zorder(10)

    ax2 = ax.twinx()
    # ax2.bar(x=df.index, height=df.p_diff, color=(0.5, 0.5, 0.5,0.3))
    ax2.bar(x=df.index, height=df.percent, color=(0, 1, 0, 0.3), zorder=5)
    # ax2.bar(x=df.index, height=df.log, color=(0, 0, 1, 0.3))
    ax2.bar(x=df.index, height=df.p_avg2,color=(1, 0, 0, 0.3),  zorder = 5)
    # ax2.bar(x=df.index, height=df.p_avg3,  zorder = 5)
    # ax2.bar(x=df.index, height=df.p_avg4,  zorder = 5)

    plt.grid()
    plt.show()


def bb_percent_calculate(bb, n, k):
    bb['percent'] = (bb['Close'] - bb[f'MA{n}']) / (bb[f'std{n}'] * k)

    # diff = bb.Close - bb[f'MA{n}']
    # bb['log'] = (diff/ np.abs(diff)) *  np.abs(np.log2(1 / np.abs(bb['percent'])))
    bb['p_avg2'] = pd.Series(np.round(bb['percent'].rolling(7).mean(), 2),
                             name='p_avg2')
    # bb['p_avg3'] = pd.Series(np.round(bb['percent'].rolling(3).mean(), 2),
    #                          name='p_avg3')
    # bb['p_avg4'] = pd.Series(np.round(bb['percent'].rolling(4).mean(), 2),
    #                          name='p_avg4')
    # bb['p_diff'] = bb['percent'] - bb['percent'].shift(1)
    return bb


def main():
    bb_n = 15
    bb_k = 2
    start_date = '2022-07-10'
    days = 2500
    stock = 'cn_603650'

    df = df_init(start_date, days, stock)
    df = boll_bands(df, bb_n, bb_k)
    df = bb_percent_calculate(df, bb_n, bb_k)

    draw_figure(df, bb_n)


if __name__ == '__main__':
    main()