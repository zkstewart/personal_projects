#! python3
import os, ccxt, pickle, re
from copy import deepcopy
# import sqlite3

class BTCMarket:
    ## TBD: Round volume and prices to precision limit
    _precision = 4

    def __init__(self, publicKey=None, privateKey=None):
        # Instantiate market class
        if publicKey != None and privateKey != None:
            self.BTCMarket = ccxt.btcmarkets({'apiKey': publicKey,
                'secret': privateKey, 'timeout': 30000, 'enableRateLimit': True})
        else:
            self.BTCMarket = ccxt.btcmarkets()

        # Note available currencies for trading
        self._pairs = [market["symbol"] for market in self.BTCMarket.fetch_markets()]
        self._currencies = list(set([pair.split("/")[1] for pair in self._pairs]))

        # Note logged in status
        if publicKey == None or privateKey == None:
            self._loggedIn = False
        else:
            self._loggedIn = True
    
    def _is_valid_pair(self, pair):
        if not pair.upper() in self._pairs:
            print("unknown pair {0}".format(pair))
            return False
        else:
            return True
    
    def _is_valid_cost(self, currency, cost):
        balance = self.balance(currency)
        if balance == None: # This shouldn't ever occur
            return False
        
        freeBalance = balance["free"]
        if freeBalance > cost:
            return False
        else:
            return True
    
    def is_valid_currency(self, currency):
        if not currency in self._currencies:
            print("unknown currency {0}".format(currency))
            return False
        else:
            return True
    
    def ticker(self, pair="BTC/AUD"):
        valid = self._is_valid_pair(pair)
        if valid:
            return self.BTCMarket.fetch_ticker(pair)
    
    def order_book(self, pair="BTC/AUD"):
        valid = self._is_valid_pair(pair)
        if valid:
            return self.BTCMarket.fetch_order_book(pair)
    
    def balance(self, currency="AUD"):
        if not self._loggedIn:
            return None

        valid = self.is_valid_currency(currency)
        if not valid:
            return None
        else:
            return self.BTCMarket.fetch_balance()[currency]
    
    def limit_buy(self, volume, price, pair="BTC/AUD"):
        if not self._loggedIn:
            return None

        # Validate pair
        valid = self._is_valid_pair(pair)
        if not valid:
            return None
        
        # Validate that account can afford this
        currency = pair.split("/")[1]
        cost = volume * price
        valid = self._is_valid_cost(currency, cost)
        if not valid:
            return None
        
        # Place buy order
        self.BTCMarket.create_limit_buy_order(pair, volume, price) # IMPORTANT: Validate argument orders

    def limit_sell(self, volume, price, pair="BTC/AUD"):
        if not self._loggedIn:
            return None

        # Validate pair
        valid = self._is_valid_pair(pair)
        if not valid:
            return None
        
        # Validate that volume exists in account to sell
        currency = pair.split("/")[0]
        valid = self._is_valid_cost(currency, volume)
        if not valid:
            return None
        
        # Place sell order
        self.BTCMarket.create_limit_sell_order(pair, volume, price) # IMPORTANT: Validate argument orders
    
    def market_buy(self, volume, pair="BTC/AUD"):
        price = self.ticker()["ask"]
        self.limit_buy(volume, price, pair)
    
    def market_sell(self, volume, pair="BTC/AUD"):
        price = self.ticker()["bid"]
        self.limit_buy(volume, price, pair)

# class CryptoSQLDB:
#     def __init__(self, fileName):
#         if os.path.isfile(fileName):
#             newDB = False
#         else:
#             newDB = True
        
#         self._db = sqlite3.connect(fileName)
#         self._cursor = self._db.cursor()
#         self.tableName = "cryptodb"
#         self.columns = ["date", "time", "coin", "qty", "price", "type",
#             "partner_col"]

#         if newDB == True:
#             self._cursor.execute('''CREATE TABLE cryptodb (date text, time text, coin text,
#                 qty real, price real, type text, partner_col integer)''')

#     def select(self, cmd):
#         #self._cursor.execute(cmd)
#         pass

#     def insert(self):
#         pass

#     def dump_to_tsv(self, fileName):
#         pass
    
#     def exit(self):
#         self._db.commit()
#         self._db.close()

class CryptoPickleDB:
    dateFormat = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
    timeFormat = re.compile(r"^\d{2}:\d{2}:\d{2}$")
    typeOptions = ["buy", "sell"]

    def __init__(self, fileName):
        self._fileName = fileName
        self.columns = ["date", "time", "coin", "qty", "price", "type"]
        
        if os.path.isfile(fileName):
            self.openBuys, self.openSells, self.closedBuys, \
                self.closedSells = pickle.load(open(self._fileName, "rb"))
        else:
            self.openBuys = []
            self.openSells = []
            self.closedBuys = []
            self.closedSells = []
    
    def _is_valid_row(self, row):
        try:
            # Validate that row has correct contents number
            assert len(row) == len(self.columns)
            date, time, coin, qty, price, type = row

            # Validate that row contents are correct type
            assert CryptoPickleDB.dateFormat.match(date) != None
            assert CryptoPickleDB.timeFormat.match(time) != None
            # Can't validate coin without access to market object
            assert type(qty) == float
            assert type(price) == float
            assert type in CryptoPickleDB.typeOptions
            return True
        except:
            return False
    
    def _find_open_buy(self, row):
        index = [index for index in range(len(self.openBuys)) if self.openBuys[index] == row]
        if index == []:
            return None
        else:
            return index[0]

    def _find_open_sell(self, row):
        index = [index for index in range(len(self.openSells)) if self.openSells[index] == row]
        if index == []:
            return None
        else:
            return index[0]
    
    def write_open_buy(self, row):
        valid = self._is_valid_row(row)
        if not valid:
            return None

    def write_open_sell(self, row):
        valid = self._is_valid_row(row)
        if not valid:
            return None

    def close_buy(self, row):
        # Validate row format
        valid = self._is_valid_row(row)
        if not valid:
            return None
        
        # Validate that this exists as an open buy
        index = self._find_open_buy(row)
        if index == None: # This should be a larger error, or an unnecessary validation
            return None
        
        # Move row to closed buys data storage
        self.closedBuys(deepcopy(row))
        del self.openBuys[index]

    def close_sell(self, row):
        valid = self._is_valid_row(row)
        if not valid:
            return None
        
        # Validate that this exists as an open sell
        index = self._find_open_sell(row)
        if index == None: # This should be a larger error, or an unnecessary validation
            return None
        
        # Move row to closed buys data storage
        self.closedSells(deepcopy(row))
        del self.openSells[index]

    def dump_to_tsv(self, fileName):
        pass
    
    def exit(self):
        pickle.dump([self.openBuys, self.openSells, self.closedBuys, self.closedSells], \
            open(self._fileName, "wb"))

class CryptoBot:
    def __init__(self, market, db):
        self.market = market
        self.db = db
    
    def limit_buy(self, volume, price, pair="BTC/AUD"):
        result = self.market.limit_buy(volume, price, pair)
        if result == None:
            return None
        else:
            pass
            ## TBD: Obtain data of recent buys/sells from btcmarkets from testing
            #["date", "time", "coin", "qty", "price", "type"]
            #self.db.write_open_buy()

    def limit_sell(self, volume, price, pair="BTC/AUD"):
        result = self.market.limit_sell(volume, price, pair)
        if result == None:
            return None
        else:
            pass
            ## TBD: Obtain data of recent buys/sells from btcmarkets from testing
            #["date", "time", "coin", "qty", "price", "type"]
            #self.db.write_open_buy()

    def market_buy(self):
        pass

    def market_sell(self):
        pass

    def run_strategy(self):
        pass


# GOAL: Obtain top cryptocurrency coin global prices over time

# GOAL: Obtain the main 500 stocks global prices over time

# GOAL: Perform recent news article sentiment analysis (e.g., bear/bull prediction)

# GOAL: Obtain exchange-specific market depth (i.e., for btcmarkets)

# GOAL: Obtain US, China, AU dollar performance metrics

# GOAL: Identify whale activity

# GOAL: Global economic activities (unemployment rate, economic prosperity indices for US, China, AU)
