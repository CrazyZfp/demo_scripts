import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


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


def draw_figure(df, n):
    ax = df.plot(y=['low', 'up', 'Close', f'MA{n}'], x_compat=True)

    ax2 = ax.twinx()
    ax2.bar(x=df.index, height=df.percent, color=(0.5, 0.5, 0.5, 0.2))

    plt.show()


def df_init():
    df = pd.Series([100, 45, 67, 8, 99, 99, 76, 32, 45, 66], name='Close')
    df = pd.DataFrame(df)  # 得到的数据中index直接就是Date

    date = pd.date_range(start='2020-09-09', periods=10, name='date')
    df['date'] = date
    df.set_index('date', inplace=True)
    return df


def bb_percent_calculate(bb, n):
    bb['percent'] = abs((bb['Close'] - bb[f'MA{n}']) / bb[f'std{n}'])
    return bb


def main():
    n = 5
    k = 2

    df = df_init()
    df = boll_bands(df, n, k)
    df = bb_percent_calculate(df, n)
    print(df.loc[:, ['low', 'up', 'percent', 'Close', f'MA{n}']])

    draw_figure(df, n)


if __name__ == '__main__':
    main()