from typing import List
from json_util import JSONable
import copy
from constants import Direction, Confidence


class Quote(JSONable):
    date: str
    open: float
    close: float
    fluctuation: float  # 涨跌幅
    rate: float  # 涨跌幅率, 单位为 %
    lowest: float
    highest: float
    volume: int  # 成交量, 单位手
    turnover: float  # 成交额
    turnover_rate: float  # 换手率, 单位为%
    pre_close: float  # 前一交易日收盘价


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


def tushare_convert(row) -> Quote:
    q = Quote()
    q.date = row.trade_date
    q.close = row.close
    q.open = row.open
    q.highest = row.high
    q.lowest = row.low
    q.volume = row.vol
    q.turnover = row.amount
    q.fluctuation = row.change
    q.rate = row.pct_chg
    q.pre_close = row.pre_close

    return q


class TradingLog(JSONable):
    date: str
    direction: Direction  # -1 买进 / 1 卖出
    volume: int
    price: float
    cash_change: float
    trade_fee: float
    worth: float  # 交易后总值
    profit: str

    def report(self) -> str:
        return f"""#{self.date} [{self.direction.desc()}] {self.volume}*{self.price} -> {self.cash_change}({self.trade_fee}) 盈亏: {self.profit} 当前: ¥{self.worth}"""


class Position(JSONable):
    code: str
    volume: int
    avg_cost: float
    worth: float

    def __init__(self, code: str):
        self.code = code
        self.volume = 0
        self.avg_cost = 0
        self.worth = None

    def to_json(self):
        return super().to_json()

    def update(self, direction: Direction, volume, amount_fee):
        temp = direction.code() * volume
        old_volume = self.volume
        self.volume -= temp
        if self.volume == 0:
            self.avg_cost = 0
        else:
            self.avg_cost = (old_volume * self.avg_cost -
                              amount_fee) / self.volume

    def calculate_worth(self, close):
        self.worth = round(self.volume * close, 2)

    def report(self) -> str:
        return f"""¥{self.worth}(¥{round(self.avg_cost,2)} * {self.volume}股)"""


class Assets(JSONable):
    cash: float
    position: Position
    worth: float

    def __init__(self, cash: float, position: Position):
        self.cash = cash
        self.position = position
        self.worth = None

    def to_json(self):
        return {
            'cash': self.cash,
            'position': self.position.to_json(),
            'worth': self.cash + self.position.worth
        }

    def update(self, direction: Direction, volume: int, amount_fee: float,
               close: float):
        self.cash += amount_fee
        self.position.update(direction, volume, amount_fee)
        self.calculate_worth(close)

    def calculate_worth(self, close):
        self.position.calculate_worth(close)
        self.worth = round(self.cash + self.position.worth, 2)

    def report(self) -> str:
        return f"""¥{self.worth} = ¥{round(self.cash, 2)} + {self.position.report()}"""


class MockTrading(JSONable):
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
        self.quotes = None


    def add_quote(self, quote: Quote):
        self.quotes.append(quote)

    def trade_fee(self, direction: Direction, amount: float):
        """
        交易费用.  券商手续费(万二五) + 印花税(千一)
        """
        # 券商手续费
        brokers_fee = amount * 0.00025

        if brokers_fee < 5:
            brokers_fee = 5

        # 印花税
        stamp_duty = 0
        if direction == Direction.SELL:
            stamp_duty = amount * 0.001

        return round(brokers_fee + stamp_duty, 4)

    def slippage(self, direction: Direction, price: float):
        """
        滑点. 按 千分之一 计算, 最低 0.01 元
        """
        if price <= 10:
            return -0.01 * direction.code()

        return -0.001 * direction.code() * price

    def make_trading(self, direction: Direction, conf: Confidence,
                     close: float, date: str):

        price = close + self.slippage(direction, close)
        price = round(price, 4)

        if direction == Direction.BUY:
            volume = self.current_assets.cash * conf.code(
            ) // price // 100 * 100
        else:
            volume = self.current_assets.position.volume * conf.code()
            volume = 0 if volume < 100 else volume

        if volume == 0:
            return

        stock_amount = volume * direction.code() * price
        trade_fee = self.trade_fee(direction, abs(stock_amount))

        t_log = TradingLog()
        t_log.date = date
        t_log.direction = direction
        t_log.volume = volume
        t_log.price = price
        t_log.cash_change = round(stock_amount - trade_fee, 4)
        t_log.trade_fee = trade_fee
        self.trading_logs.append(t_log)

        if direction == Direction.BUY:
            t_log.profit = "-"
        else:
            t_log.profit = f"¥{round(t_log.cash_change - volume * self.current_assets.position.avg_cost,2)}"

        self.current_assets.update(direction, volume, t_log.cash_change, close)
        t_log.worth = self.current_assets.worth


    def report(self) -> str:
        close = self.quotes[-1].close
        log_str = '\n'.join(tl.report() for tl in self.trading_logs)
        self.current_assets.calculate_worth(close)
        self.open_assets.calculate_worth(close)

        sell_count = float(0)
        win_count = float(0)
        for tl in self.trading_logs:
            if tl.direction == Direction.BUY:
                continue
            sell_count+=1
            if not tl.profit.startswith("¥-"):
                win_count+=1

        return f"""
========================================================================
                {self.code}: {self.start_date} ~ {self.end_date}
========================================================================
- 交易次数: {len(self.trading_logs)}
- 胜率: {round(100*win_count/sell_count)}%
- 盈利: ¥{round(self.current_assets.worth - self.open_assets.worth,2)}
- 收益率: {round(100*(self.current_assets.worth - self.open_assets.worth)/self.open_assets.worth,2)}%
- β收益率: {round(100*(self.quotes[-1].close - self.quotes[14].close)/ self.quotes[14].close, 2)}%  {round(self.quotes[14].close,2)}[{self.quotes[14].date}]->{round(self.quotes[-1].close,2)}[{self.quotes[-1].date}]
- 期初资产: {self.open_assets.report()}
- 期末资产: {self.current_assets.report()}
------------------------------------------------------------------------
{log_str}
"""