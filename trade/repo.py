import requests
import json
from psycopg2.pool import SimpleConnectionPool
from model import Quote, sohu_convert, tushare_convert
from typing import List, Dict, Tuple
from json_util import convert_object
from isecret import tushare_token
import re
import time

stock_code_re = re.compile('\d{6}')

# 导入tushare
import tushare as ts
# 初始化pro接口
pro = ts.pro_api(tushare_token)

pg_pool = SimpleConnectionPool(user="postgres",
                               password="iindeed",
                               host="127.0.0.1",
                               port="5432",
                               database="astock",
                               minconn=1,
                               maxconn=4)

insert_sql = """INSERT INTO quote_history_{}(code, date_day, quote, asset_type) VALUES {}
ON CONFLICT (code, date_day) DO UPDATE quote=EXCLUDED.quote;
"""

select_sql = """SELECT code,quote FROM quote_history_{} WHERE code IN ({}) {} ORDER BY code ASC, date_day ASC;
"""


def get_tab_suffix(code):
    return stock_code_re.search(code).group()[-1:]


def save(code, quotes: List[Quote], asset_type: int = 0):

    tab_suffix = get_tab_suffix(code)

    vals = ','.join(f'''('{code}','{q.date}'::DATE,'{q.to_json_str()}',{asset_type})'''
                    for q in quotes)

    def save_in_conn(cursor, conn):
        cursor.execute(insert_sql.format(tab_suffix, vals))
        conn.commit()

    conn_execute(save_in_conn)


def conn_execute(fn):
    conn = None
    try:
        conn = pg_pool.getconn()
        with conn.cursor() as cursor:
            fn(cursor, conn)
    except Exception as e:
        print(f"db exception: {e}")
    finally:
        if conn:
            pg_pool.putconn(conn)


def query(*codes, start_date=None, end_date=None) -> Dict[str, List[Quote]]:
    tab_codes_sql_map = {}
    for code in codes:
        suffix = get_tab_suffix(code)
        if suffix not in tab_codes_sql_map:
            tab_codes_sql_map[suffix] = f"'{code}'"
        else:
            tab_codes_sql_map[suffix] += f",'{code}'"

    day_sql = ''
    if start_date:
        day_sql += f" AND date_day >= '{start_date}' "
    if end_date:
        day_sql += f" AND date_day <= '{end_date}' "

    quote_map = {}

    def query_in_conn(cursor, *args):
        for suffix, codes_sql in tab_codes_sql_map.items():
            cursor.execute(select_sql.format(suffix, codes_sql, day_sql))
            while True:
                row = cursor.fetchone()
                if not row:
                    break
                if row[0] not in quote_map:
                    quote_map[row[0]] = []
                quote_map[row[0]].append(convert_object(row[1], Quote))

    conn_execute(query_in_conn)
    return quote_map


def sohu_stock(stock: str, start_date: str, end_date: str):
    sohu_url = f"https://q.stock.sohu.com/hisHq?code={stock}&start={start_date.replace('-','')}&end={end_date}&stat=0&order=A&period=d&callback=historySearchHandler&rt=jsonp"
    resp = requests.get(url=sohu_url)

    prefix = 'historySearchHandler(['
    postfix = '])'
    json_body = json.loads(resp.text[len(prefix):(-len(postfix) - 1)])

    save(stock[3:], list(sohu_convert(sq) for sq in json_body.get('hq')))


def stock_list(offset: int = 0,
               limit: int = 20,
               market: str = '主板') -> Tuple[List[str], int]:
    """
    :param market: 主板/创业板/科创板
    """
    df = pro.stock_basic(
        **{
            "ts_code": "",
            "name": "",
            "exchange": "",  # 交易所 SSE上交所 SZSE深交所 HKEX港交所
            "market": market,
            "is_hs": "",  # 是否沪深港通标的，N否 H沪股通 S深股通
            "list_status": "L",  # L上市 D退市 P暂停上市
            "limit": limit,
            "offset": offset
        },
        fields=[
            "ts_code",  # TS代码. 605555.SH	
            "symbol",  # 股票代码. 605555
            "name",
            "area",
            "industry",
            "market",
            "list_date"  # 上市日期
        ])

    return df.ts_code.to_list(), offset + limit


def tushare_stock(stock: str, start_date: str, end_date: str):
    df = ts.pro_bar(ts_code=stock,
                    adj='qfq',
                    asset='E',
                    freq='D',
                    start_date=start_date,
                    end_date=end_date)
    if df is None:
        print(f'no data of {stock} in {start_date}~{end_date}')
        return
    quotes = []
    for _, row in df[::-1].iterrows():
        quotes.append(tushare_convert(row))
    save(stock, quotes)


if __name__ == '__main__':
    limit = 100
    offset = 0
    next = True
    # while next:
    # print(f'batch starting... offset={offset}, limit={limit}')
    # stocks, offset = stock_list(offset=offset, limit=limit)
    # if len(stocks) < limit:
    # next = False
    stocks = ['516010.SH']
    for stock in stocks:
        print(f"getting stock: {stock} ...")
        tushare_stock(stock, '20120101', '20230206')
        print(f"saved!")
        # print('suspend 10s ...')
        # time.sleep(10)
    # r = query('000001.SZ', '000002.SZ', start_date='20200101',end_date='20200110')
    # print(r)

    # tushare_stock('300191.SZ', '20200101', '20230120')
    # tushare_stock('cn_600103', '20200101', '20230120')
    # tushare_stock('cn_600854', '20200101', '20230120')
    # rows = query('603650', start_date='2020-01-02', end_da='2020-01-30')
    # print(rows)