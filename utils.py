
"""
Trading Utilities for MT5 Scalping Bot
Essential functions for position sizing, validation, and market analysis
"""

import logging
from typing import Optional, Tuple
from datetime import datetime, time

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

def calculate_lot_size(risk_percent: float, sl_points: int, symbol: str) -> float:
    """
    Calculate optimal lot size based on risk percentage and stop loss distance
    
    Args:
        risk_percent: Risk percentage of account balance
        sl_points: Stop loss distance in points
        symbol: Trading symbol
    
    Returns:
        Optimal lot size (minimum 0.01, maximum 1.0)
    """
    try:
        if not MT5_AVAILABLE:
            return 0.01  # Demo lot size
        
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            return 0.01
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return 0.01
        
        # Calculate risk amount
        balance = account_info.balance
        risk_amount = balance * (risk_percent / 100.0)
        
        # Calculate pip value (varies by symbol)
        if "XAU" in symbol or "GOLD" in symbol:
            pip_value = 10.0  # $10 per pip for gold
        elif "JPY" in symbol:
            pip_value = 0.1   # Different for JPY pairs
        else:
            pip_value = 1.0   # Standard for major pairs
        
        # Calculate lot size
        if sl_points > 0:
            lot_size = risk_amount / (sl_points * pip_value)
            # Ensure lot size is within acceptable range
            lot_size = max(0.01, min(1.0, round(lot_size, 2)))
        else:
            lot_size = 0.01
        
        return lot_size
        
    except Exception as e:
        logging.error(f"Lot size calculation error: {e}")
        return 0.01

def validate_symbol(symbol: str) -> bool:
    """
    Validate if symbol is available for trading
    
    Args:
        symbol: Symbol to validate
        
    Returns:
        True if symbol is valid and tradeable
    """
    try:
        if not MT5_AVAILABLE:
            # Demo mode - accept common symbols
            return symbol in ["XAUUSD", "XAUUSDm", "XAUUSDc", "EURUSD", "GBPUSD"]
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return False
        
        # Check if symbol is visible and tradeable
        if not symbol_info.visible:
            # Try to select symbol
            if not mt5.symbol_select(symbol, True):
                return False
        
        return symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL
        
    except Exception as e:
        logging.error(f"Symbol validation error: {e}")
        return False

def get_spread_points(symbol: str, ask: float, bid: float) -> int:
    """
    Calculate spread in points
    
    Args:
        symbol: Trading symbol
        ask: Ask price
        bid: Bid price
        
    Returns:
        Spread in points
    """
    try:
        if not MT5_AVAILABLE:
            return 25  # Demo spread
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return 999  # Large spread to prevent trading
        
        spread = (ask - bid) / symbol_info.point
        return int(spread)
        
    except Exception as e:
        logging.error(f"Spread calculation error: {e}")
        return 999

def check_trading_session() -> bool:
    """
    Check if current time is within trading session
    
    Returns:
        True if within trading hours
    """
    try:
        current_time = datetime.now().time()
        
        # London session: 08:00 - 17:00 GMT
        london_start = time(8, 0)
        london_end = time(17, 0)
        
        # New York session: 13:00 - 22:00 GMT
        ny_start = time(13, 0)
        ny_end = time(22, 0)
        
        # Check if in trading session
        in_london = london_start <= current_time <= london_end
        in_ny = ny_start <= current_time <= ny_end
        
        return in_london or in_ny
        
    except Exception as e:
        logging.error(f"Session check error: {e}")
        return False

def format_price(price: float, symbol: str) -> str:
    """
    Format price according to symbol specifications
    
    Args:
        price: Price to format
        symbol: Trading symbol
        
    Returns:
        Formatted price string
    """
    try:
        if "XAU" in symbol or "GOLD" in symbol:
            return f"{price:.2f}"  # Gold - 2 decimal places
        elif "JPY" in symbol:
            return f"{price:.3f}"  # JPY pairs - 3 decimal places
        else:
            return f"{price:.5f}"  # Standard - 5 decimal places
            
    except Exception as e:
        return f"{price:.5f}"

def calculate_atr_levels(high: list, low: list, close: list, period: int = 14) -> Tuple[float, float, float]:
    """
    Calculate ATR-based support and resistance levels
    
    Args:
        high: High prices list
        low: Low prices list
        close: Close prices list
        period: ATR period
        
    Returns:
        Tuple of (current_atr, support_level, resistance_level)
    """
    try:
        if len(high) < period + 1:
            return 0.0, 0.0, 0.0
        
        # Calculate True Range
        tr_list = []
        for i in range(1, len(high)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr = max(tr1, tr2, tr3)
            tr_list.append(tr)
        
        # Calculate ATR
        if len(tr_list) >= period:
            atr = sum(tr_list[-period:]) / period
            current_price = close[-1]
            
            support = current_price - (atr * 1.5)
            resistance = current_price + (atr * 1.5)
            
            return atr, support, resistance
        
        return 0.0, 0.0, 0.0
        
    except Exception as e:
        logging.error(f"ATR calculation error: {e}")
        return 0.0, 0.0, 0.0

def is_market_open() -> bool:
    """
    Check if forex market is open
    
    Returns:
        True if market is open
    """
    try:
        now = datetime.now()
        weekday = now.weekday()
        
        # Market is closed on weekends
        if weekday == 5:  # Saturday
            return False
        elif weekday == 6:  # Sunday
            # Market opens Sunday 22:00 GMT
            return now.hour >= 22
        else:
            # Market is open Monday - Friday
            return True
            
    except Exception as e:
        logging.error(f"Market status check error: {e}")
        return True  # Default to open

def validate_order_parameters(symbol: str, order_type: str, volume: float, 
                            price: float, sl: float, tp: float) -> bool:
    """
    Validate order parameters before execution
    
    Args:
        symbol: Trading symbol
        order_type: Order type (BUY/SELL)
        volume: Lot size
        price: Entry price
        sl: Stop loss price
        tp: Take profit price
        
    Returns:
        True if parameters are valid
    """
    try:
        # Basic validations
        if volume <= 0 or volume > 10:
            return False
        
        if price <= 0 or sl <= 0 or tp <= 0:
            return False
        
        # Check SL/TP direction
        if order_type == "BUY":
            if sl >= price or tp <= price:
                return False
        elif order_type == "SELL":
            if sl <= price or tp >= price:
                return False
        
        # Check minimum distance
        min_distance = 0.0001  # Minimum distance for XAUUSD
        
        if order_type == "BUY":
            if (price - sl) < min_distance or (tp - price) < min_distance:
                return False
        elif order_type == "SELL":
            if (sl - price) < min_distance or (price - tp) < min_distance:
                return False
        
        return True
        
    except Exception as e:
        logging.error(f"Order validation error: {e}")
        return False
