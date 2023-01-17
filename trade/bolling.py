import pandas as pd
import numpy as np

def boll_bands(data, ndays,k):
    ma = pd.Series(np.round(data['Close'].rolling(ndays).mean(), 2), name=f'MA{ndays}')  # 计算nday均线
    # pandas.std() 默认是除以n-1 的，即是无偏的，如果想和numpy.std() 一样有偏，需要加上参数ddof=0
    # 此处添加ddof的原因是wind和yahoo的计算均采用的有偏值进行的计算
    std = pd.Series(np.round(data['Close'].rolling(ndays).std(ddof=0), 2))  # 计算nday标准差，有偏
    b1 = ma + (k * std)  # 此处的2就是Standard Deviations
    B1 = pd.Series(b1, name='up')
    data = data.join(ma)  # 上边不写name 这里报错
    data = data.join(B1)

    b2 = ma - (k * std)
    B2 = pd.Series(b2, name='low')
    data = data.join(B2)

    data['percent']= abs((data['Close'] - ma)/std)

    return data


if __name__ == '__main__':
	# pandas调用yahoo财经的股票数据，此处以纳斯达克指数为例计算
    data = pd.Series([100,45,67,8,99,99,76,32,45,66], name='Close')
    data = pd.DataFrame(data)  # 得到的数据中index直接就是Date
    n = 5
    k= 2

    bb = boll_bands(data, n,k)
    print(bb.loc[:, ['low', 'up', 'percent', 'Close', f'MA{n}']])