import pandas as pd

df = pd.DataFrame(pd.Series([1,2,3], name='Close'))  # 得到的数据中index直接就是Date
# df = df.join(pd.Series([1,2,3], name='Close'))
df = df.join(pd.Series([1,2,3], name='Close2'))
print(df)