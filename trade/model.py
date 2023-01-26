from typing import List
from json_util import JSONable, convert_object
import copy


class Quote(JSONable):
    date: str
    open: float
    close: float
    fluctuation: float  # 涨跌幅
    rate: float  # 涨跌幅率, 单位为 %
    lowest: float
    highest: float
    volume: int  # 成交量, 单位手
    turnover: float  # 成交额, 单位万
    turnover_rate: float  # 换手率, 单位为%


def sohu_convert(sq) -> Quote:
    q = Quote()
    q.date = sq[0]
    q.open = float(sq[1])
    q.close = float(sq[2])
    q.fluctuation = float(sq[3])
    q.rate = float(sq[4][:-1])
    q.lowest = float(sq[5])
    q.highest = float(sq[6])
    q.volume = int(sq[7]) * 100
    q.turnover = float(sq[8]) * 10000
    q.turnover_rate = float(sq[9][:-1])
    return q


class TradingLog:
    date: str
    direction: int  # -1 买进 / 1 卖出
    volume: int
    price: float
    cash_change: float


class Position:
    code: str
    volume: int
    avg_price: float

    def __init__(self, code: str):
        self.code = code
        self.volume = 0
        self.avg_cost = 0

    def update(self, direction, volume, price):
        temp = direction * volume
        self.avg_cost = (self.volume * self.avg_cost -
                         temp * price) / (self.volume - temp)
        self.volume -= temp


class Assets:
    cash: float
    position: Position

    def __init__(self, cash: float, position: Position):
        self.cash = cash
        self.position = position

    def update(self, direction: int, volume: int, price: float) -> float:
        cash_change = volume * direction * price
        self.cash += cash_change
        self.position.update(direction, volume, price)
        return cash_change


class MockTrading:
    code: str
    open_assets: Assets  # 期初资产
    current_assets: Assets  # 当前资产
    start_date: str
    end_date: str
    quotes: List[Quote]  # 区间行情
    trading_logs: List[TradingLog]  # 交易记录

    def __init__(self, code, start_date, end_date, open_cash):
        self.code = code
        self.start_date = start_date
        self.end_date = end_date

        self.open_assets = Assets(cash=open_cash, position=Position(code))
        self.current_assets = copy.deepcopy(self.open_assets)
        self.trading_logs = []
        self.quotes = []

    def add_quote(self, quote:Quote):
        self.quotes.append(quote)

    def make_trading(self, direction: int, volume: int, price: float,
                     date: str):
        t_log = TradingLog()
        t_log.date = date
        t_log.direction = direction
        t_log.volume = volume
        t_log.price = price
        t_log.cash_change = volume * direction * price
        self.trading_logs.append(t_log)
