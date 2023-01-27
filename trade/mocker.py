import redis
from repo import query
from model import MockTrading, Quote
from strategy import Strategy
from json_util import convert_list
import json
from strategy import BollingStrategy
from typing import List

pool = redis.ConnectionPool(host='localhost',
                            port=6379,
                            db=8,
                            decode_responses=True,
                            max_connections=5)
r = redis.Redis(
    connection_pool=pool,
    charset="utf-8",
    decode_responses=True,
)

key_format = '{}:{}>{}'


def cache_init(*codes, start_date, end_date):
    codes_to_query = set()
    for code in codes:
        key = key_format.format(code, start_date, end_date)
        res = r.expire(key, 3600)
        if not res:
            codes_to_query.add(code)

    if codes_to_query:
        quote_map = query(*codes_to_query,
                          start_date=start_date,
                          end_date=end_date)
        for code, quotes in quote_map.items():
            key = key_format.format(code, start_date, end_date)
            r.setex(key, 3600, json.dumps(list(q.to_json() for q in quotes)))


def launch(*codes,
           start_date,
           end_date,
           strategy: Strategy,
           open_cash: float = 100000):

    cache_init(*codes, start_date=start_date, end_date=end_date)

    mt_map = {}
    for code in codes:
        mt = MockTrading(code, start_date, end_date, open_cash)
        mt_map[code] = mt

        key = key_format.format(code, start_date, end_date)

        quotes = convert_list(json.loads(r.get(key)), List[Quote])

        strategy.assets = mt.current_assets
        strategy.quotes = quotes
        strategy.trading_logs = mt.trading_logs
        strategy.calcute_indices()
        for sr in strategy.evaluate():
            if sr:
                mt.make_trading(*sr)

    return mt_map


if __name__ == '__main__':
    mt_map = launch('300191','600103','600854','603650',
           start_date='2020-01-01',
           end_date='2023-01-18',
           strategy=BollingStrategy())
    print(mt_map)
