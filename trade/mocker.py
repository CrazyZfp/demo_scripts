import redis
from repo import query
from model import MockTrading, Quote
from strategy import Strategy
from json_util import convert_object

pool = redis.ConnectionPool(host='localhost',
                            port=6379,
                            db=8,
                            max_connections=5)
r = redis.Redis(connection_pool=pool)

key_format = '{}:{}>{}'


def cache_init(*codes, start_date, end_date):
    codes_to_query = set()
    for code in codes:
        key = key_format.format(code, start_date, end_date)
        res = r.expire(key, 3600)
        if res == '0':
            codes_to_query.add(code)

    if codes_to_query:
        quote_map = query(*codes_to_query,
                          start_date=start_date,
                          end_date=end_date)
        for code, quotes in quote_map.items():
            key = key_format.format(code, start_date, end_date)
            r.rpush(key, *list(quote.to_json_str() for quote in quotes))


def launch(*codes,
           start_date,
           end_date,
           strategy: Strategy,
           open_cash: float = 10000):

    cache_init(codes, start_date, end_date)

    mt_map = {}
    for code in codes:
        mt = MockTrading(code, start_date, end_date, open_cash)
        mt_map[code] = mt

        key = key_format.format(code, start_date, end_date)
        quotes = list(convert_object(q, Quote) for q in r.lrange(key, 0 , 10000))

        strategy.assets = mt.current_assets
        strategy.quotes = quotes
        strategy.trading_logs = mt.trading_logs
        sr = strategy.execute()
        if not sr:
            mt.make_trading(*sr)

    return mt_map


if __name__ == '__main__':
    launch()