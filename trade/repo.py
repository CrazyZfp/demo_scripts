import requests
import json
from psycopg2.pool import SimpleConnectionPool
from model import Quote, sohu_convert
from typing import List, Dict
from json_util import convert_object

pg_pool = SimpleConnectionPool(user="postgres",
                               password="iindeed",
                               host="127.0.0.1",
                               port="5432",
                               database="astock",
                               minconn=1,
                               maxconn=4)

insert_sql = """INSERT INTO stock_history(code, date_day, quote) VALUES {}
ON CONFLICT (code, date_day) DO NOTHING;
"""

select_sql = """SELECT code,quote FROM stock_history WHERE code IN ({}) {} ORDER BY id ASC;
"""


def save(code, quotes:List[Quote]):

    vals = ','.join(f'''('{code}','{q.date}'::DATE,'{q.to_json_str()}' )'''
                    for q in quotes)

    with pg_pool.getconn() as conn, conn.cursor() as cursor:
        cursor.execute(insert_sql.format(vals))
        conn.commit()


def query(*codes, start_date=None, end_date=None)-> Dict[str, List[Quote]]:
    codes_sql = ','.join(f"'{code}'" for code in codes)
    day_sql = ''
    if start_date:
        day_sql += f" AND date_day >= '{start_date}' "
    if end_date:
        day_sql += f" AND date_day <= '{end_date}' "

    quote_map = {}
    with pg_pool.getconn() as conn, conn.cursor() as cursor:
        cursor.execute(select_sql.format(codes_sql, day_sql))
        while True:
            row = cursor.fetchone()
            if not row:
                return quote_map
            if row[0] not in quote_map:
                quote_map[row[0]] = []
            quote_map[row[0]].append(convert_object(row[1], Quote))



def sohu_stock(stock: str, start_date: str, end_date: str):
    sohu_url = f"https://q.stock.sohu.com/hisHq?code={stock}&start={start_date.replace('-','')}&end={end_date}&stat=0&order=A&period=d&callback=historySearchHandler&rt=jsonp"
    resp = requests.get(url=sohu_url)

    prefix = 'historySearchHandler(['
    postfix = '])'
    json_body = json.loads(resp.text[len(prefix):(-len(postfix) - 1)])

    save(stock[3:], list(sohu_convert(sq) for sq in json_body.get('hq')))


if __name__ == '__main__':
    # sohu_stock('cn_300191', '20200101', '20230120')
    # sohu_stock('cn_600103', '20200101', '20230120')
    # sohu_stock('cn_600854', '20200101', '20230120')
    rows = query('603650', start_date='2020-01-02', end_da='2020-01-30')
    # print(rows)