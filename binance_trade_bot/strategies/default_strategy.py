import random
import sys
from datetime import datetime

from binance_trade_bot.auto_trader import AutoTrader


class Strategy(AutoTrader):
    def __init__(self, binance_manager, database, logger, config):
        super().__init__(binance_manager, database, logger, config)
        self.is_initialize_current_coin = False

    def initialize(self):
        super().initialize()

    def scout(self):
        """
        Scout for potential jumps from the current coin to another coin
        """
        if not self.process_current_coin():
            self.logger.info("Variable is_tradeable is False.")
            return 

        all_tickers = self.manager.get_all_market_tickers()

        current_coin = self.db.get_current_coin()
        # Display on the console, the current coin+Bridge, so users can see *some* activity and not think the bot has
        # stopped. Not logging though to reduce log size.
        print(
            f"{datetime.now()} - CONSOLE - INFO - I am scouting the best trades. "
            f"Current coin: {current_coin + self.config.BRIDGE} ",
            end="\r",
        )

        current_coin_price = all_tickers.get_price(current_coin + self.config.BRIDGE)

        if current_coin_price is None:
            self.logger.info("Skipping scouting... current coin {} not found".format(current_coin + self.config.BRIDGE))
            return

        self._jump_to_best_coin(current_coin, current_coin_price, all_tickers)

    def bridge_scout(self):
        current_coin = self.db.get_current_coin()
        if self.manager.get_currency_balance(current_coin.symbol) > self.manager.get_min_notional(
            current_coin.symbol, self.config.BRIDGE.symbol
        ):
            # Only scout if we don't have enough of the current coin
            return
        new_coin = super().bridge_scout()
        if new_coin is not None:
            self.db.set_current_coin(new_coin)

    def process_current_coin(self):
        """
        Decide what is the current coin, and set it up in the DB.
        """
        if not self.is_initialize_current_coin:
            current_coin = self.config.CURRENT_COIN_SYMBOL
            # if we don't have a configuration, we selected a coin at random... Buy it so we can start trading.
            if current_coin == "":
                if self.is_tradeable():
                    current_coin = random.choice(self.config.SUPPORTED_COIN_LIST)
                    self.db.set_current_coin(current_coin)
                    self.logger.info(f"Setting initial coin to {current_coin}")
                    self.logger.info(f"Purchasing {current_coin} to begin trading", True)
                    all_tickers = self.manager.get_all_market_tickers()
                    self.manager.buy_alt(self.db.get_coin(current_coin), self.config.BRIDGE, all_tickers)
                    self.logger.info("Ready to start trading")
                    self.is_initialize_current_coin = True
                    return True
                else:
                    self.db.set_current_coin(self.config.BRIDGE_SYMBOL)
                    self.logger.info("Process Current Coin, Now variable is_tradeable is False.")
                    self.is_initialize_current_coin = True
                    return False
            else:
                if self.is_tradeable():
                    if current_coin not in self.config.SUPPORTED_COIN_LIST:
                        sys.exit("***\nERROR!\nCurrent coin not in SUPPORTED_COIN_LIST\n***")
                    self.db.set_current_coin(current_coin)
                    self.logger.info(f"Setting initial coin to {current_coin}")
                    self.logger.info("Ready to start trading")
                    self.is_initialize_current_coin = True
                    return True
                else:
                    self.logger.info(f"Process Current Coin, Variable is_initialize_current_coin is {False}, Now variable is_tradeable is False, Sell current coin {current_coin}", True)
                    all_tickers = self.manager.get_all_market_tickers()
                    self.manager.sell_alt(self.db.get_coin(current_coin), self.config.BRIDGE, all_tickers)
                    self.db.set_current_coin(self.config.BRIDGE_SYMBOL)
                    self.is_initialize_current_coin = True
                    return False
        else:
            current_coin = self.db.get_current_coin().symbol
            if self.is_tradeable():
                if current_coin == self.config.BRIDGE_SYMBOL:
                    current_coin = random.choice(self.config.SUPPORTED_COIN_LIST)
                    self.db.set_current_coin(current_coin)
                    self.logger.info(f"Setting initial coin to {current_coin}")
                    self.logger.info(f"Purchasing {current_coin} to begin trading", True)
                    all_tickers = self.manager.get_all_market_tickers()
                    self.manager.buy_alt(self.db.get_coin(current_coin), self.config.BRIDGE, all_tickers)
                    self.logger.info("Ready to start trading")
                return True
            else:
                if current_coin != self.config.BRIDGE_SYMBOL:
                    self.logger.info(f"Process Current Coin, Variable is_initialize_current_coin is {True}, Now variable is_tradeable is False, Sell current coin {current_coin}", True)
                    all_tickers = self.manager.get_all_market_tickers()
                    self.manager.sell_alt(self.db.get_coin(current_coin), self.config.BRIDGE, all_tickers)
                    self.db.set_current_coin(self.config.BRIDGE_SYMBOL)
                return False
