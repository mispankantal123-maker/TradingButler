"""
Mock MetaTrader5 module for demo purposes
Simulates MT5 API functionality with realistic market data
"""

import random
import time
from datetime import datetime, timedelta
from typing import NamedTuple, Optional, List
import numpy as np

# Constants (matching real MT5 constants)
TIMEFRAME_M1 = 1
TIMEFRAME_M5 = 5
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
TRADE_ACTION_DEAL = 1
ORDER_TIME_GTC = 0
ORDER_FILLING_IOC = 2
TRADE_RETCODE_DONE = 10009
SYMBOL_TRADE_MODE_FULL = 0
SYMBOL_CALC_MODE_FOREX = 0

class AccountInfo(NamedTuple):
    login: int = 12345678
    trade_mode: int = 0
    balance: float = 10000.0
    equity: float = 10000.0
    margin: float = 0.0
    margin_free: float = 10000.0
    profit: float = 0.0
    currency: str = "USD"

class SymbolInfo(NamedTuple):
    name: str = "XAUUSD"
    visible: bool = True
    trade_mode: int = SYMBOL_TRADE_MODE_FULL
    volume_min: float = 0.01
    volume_max: float = 100.0
    volume_step: float = 0.01
    digits: int = 5
    point: float = 0.00001
    trade_tick_value: float = 0.1
    trade_tick_size: float = 0.00001
    trade_stops_level: int = 10
    profit_mode: int = SYMBOL_CALC_MODE_FOREX

class TickInfo(NamedTuple):
    time: int
    bid: float
    ask: float
    last: float
    volume: int = 1

class TradeResult(NamedTuple):
    retcode: int = TRADE_RETCODE_DONE
    deal: int = 123456
    order: int = 123456
    volume: float = 0.01
    price: float = 2000.0
    comment: str = "Done"
    request_id: int = 1

class Position(NamedTuple):
    ticket: int
    time: int
    type: int
    magic: int
    identifier: int
    reason: int
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    swap: float
    profit: float
    symbol: str
    comment: str
    external_id: str = ""

# Global state
_is_initialized = False
_current_price = 2000.0
_price_direction = 1
_positions = []
_last_error = (0, "Success")

def initialize(path: str = "") -> bool:
    """Initialize MT5 connection"""
    global _is_initialized
    _is_initialized = True
    return True

def shutdown():
    """Shutdown MT5 connection"""
    global _is_initialized
    _is_initialized = False

def last_error() -> tuple:
    """Get last error"""
    return _last_error

def account_info() -> Optional[AccountInfo]:
    """Get account information"""
    if not _is_initialized:
        return None
    return AccountInfo()

def symbol_info(symbol: str) -> Optional[SymbolInfo]:
    """Get symbol information"""
    if not _is_initialized or symbol not in ["XAUUSD", "XAUUSDm", "XAUUSDc"]:
        return None
    return SymbolInfo(name=symbol)

def symbol_select(symbol: str, enable: bool) -> bool:
    """Select symbol in Market Watch"""
    return symbol in ["XAUUSD", "XAUUSDm", "XAUUSDc"]

def symbol_info_tick(symbol: str) -> Optional[TickInfo]:
    """Get current tick"""
    global _current_price, _price_direction
    
    if not _is_initialized or symbol not in ["XAUUSD", "XAUUSDm", "XAUUSDc"]:
        return None
    
    # Simulate price movement
    change = random.uniform(-0.5, 0.5) * _price_direction
    _current_price += change
    
    # Ensure price stays in realistic range
    if _current_price < 1900:
        _current_price = 1900
        _price_direction = 1
    elif _current_price > 2100:
        _current_price = 2100
        _price_direction = -1
    
    # Random direction change
    if random.random() < 0.1:
        _price_direction *= -1
    
    spread = random.uniform(0.3, 0.8)
    bid = _current_price
    ask = _current_price + spread
    
    return TickInfo(
        time=int(time.time()),
        bid=bid,
        ask=ask,
        last=_current_price,
        volume=random.randint(1, 100)
    )

def copy_rates_from_pos(symbol: str, timeframe: int, start_pos: int, count: int) -> Optional[np.ndarray]:
    """Get historical rates"""
    if not _is_initialized:
        return None
    
    # Generate realistic OHLCV data
    rates = []
    base_time = int(time.time()) - (count * timeframe * 60)
    
    for i in range(count):
        # Generate realistic OHLC data around current price
        close = _current_price + random.uniform(-10, 10)
        open_price = close + random.uniform(-2, 2)
        high = max(open_price, close) + random.uniform(0, 3)
        low = min(open_price, close) - random.uniform(0, 3)
        
        rate = {
            'time': base_time + (i * timeframe * 60),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'tick_volume': random.randint(50, 500),
            'spread': random.randint(3, 8),
            'real_volume': 0
        }
        rates.append(tuple(rate.values()))
    
    # Convert to structured array like real MT5
    dtype = [
        ('time', 'i8'), ('open', 'f8'), ('high', 'f8'), 
        ('low', 'f8'), ('close', 'f8'), ('tick_volume', 'i8'),
        ('spread', 'i4'), ('real_volume', 'i8')
    ]
    return np.array(rates, dtype=dtype)

def order_send(request: dict) -> TradeResult:
    """Send trading order"""
    global _positions
    
    if not _is_initialized:
        return TradeResult(retcode=2, comment="Not initialized")
    
    # Simulate order execution
    success_rate = 0.95  # 95% success rate
    if random.random() > success_rate:
        return TradeResult(retcode=10015, comment="Invalid request")
    
    # Create position if successful
    if request.get("action") == TRADE_ACTION_DEAL:
        position = Position(
            ticket=random.randint(100000, 999999),
            time=int(time.time()),
            type=request.get("type", ORDER_TYPE_BUY),
            magic=request.get("magic", 0),
            identifier=random.randint(100000, 999999),
            reason=0,
            volume=request.get("volume", 0.01),
            price_open=request.get("price", _current_price),
            sl=request.get("sl", 0.0),
            tp=request.get("tp", 0.0),
            price_current=_current_price,
            swap=0.0,
            profit=random.uniform(-10, 10),
            symbol=request.get("symbol", "XAUUSD"),
            comment=request.get("comment", "")
        )
        _positions.append(position)
    
    return TradeResult(
        retcode=TRADE_RETCODE_DONE,
        volume=request.get("volume", 0.01),
        price=request.get("price", _current_price)
    )

def positions_get(symbol: str = "") -> Optional[List[Position]]:
    """Get open positions"""
    if not _is_initialized:
        return None
    
    if symbol:
        return [pos for pos in _positions if pos.symbol == symbol]
    return _positions

def history_deals_get(date_from: datetime, date_to: datetime) -> Optional[List]:
    """Get historical deals"""
    return []

def history_orders_get(date_from: datetime, date_to: datetime) -> Optional[List]:
    """Get historical orders"""
    return []