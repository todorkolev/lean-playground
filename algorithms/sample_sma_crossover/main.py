# region imports
from AlgorithmImports import *
# endregion


class SmaCrossoverAlgorithm(QCAlgorithm):
    """Simple Moving Average Crossover Strategy.

    Buys when the fast SMA crosses above the slow SMA.
    Sells when the fast SMA crosses below the slow SMA.
    """

    def initialize(self):
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2023, 12, 31)
        self.set_cash(100_000)

        self.symbol = self.add_equity("SPY", Resolution.DAILY).symbol

        self.fast_sma = self.sma(self.symbol, 10, Resolution.DAILY)
        self.slow_sma = self.sma(self.symbol, 30, Resolution.DAILY)

        self.set_warm_up(30, Resolution.DAILY)

    def on_data(self, data: Slice):
        if self.is_warming_up:
            return

        if not data.contains_key(self.symbol):
            return

        if self.fast_sma.current.value > self.slow_sma.current.value:
            if not self.portfolio[self.symbol].is_long:
                self.set_holdings(self.symbol, 1.0)
        elif self.fast_sma.current.value < self.slow_sma.current.value:
            if self.portfolio[self.symbol].is_long:
                self.liquidate(self.symbol)

        self.plot("SMA", "Fast", self.fast_sma.current.value)
        self.plot("SMA", "Slow", self.slow_sma.current.value)
