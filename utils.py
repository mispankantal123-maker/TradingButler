"""
Utility Functions
Helper functions for trading operations, risk management, and system utilities
"""

try:
    import MetaTrader5 as mt5
except ImportError:
    # Fallback for development environment only
    import mock_mt5 as mt5
import numpy as np
from datetime import datetime, time
from typing import Optional, Tuple
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def validate_symbol(symbol: str) -> bool:
    """
    Validate if symbol is available and can be traded
    
    Args:
        symbol: Trading symbol (e.g., 'XAUUSD')
        
    Returns:
        True if symbol is valid and tradeable
    """
    try:
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Symbol {symbol} not found")
            return False
        
        # Check if symbol is visible in Market Watch
        if not symbol_info.visible:
            # Try to add symbol to Market Watch
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to add {symbol} to Market Watch")
                return False
        
        # Check if symbol allows trading
        if not symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
            logger.warning(f"Symbol {symbol} has restricted trading mode")
        
        logger.info(f"Symbol {symbol} validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Symbol validation error for {symbol}: {e}")
        return False

def get_spread_points(symbol: str, ask: float, bid: float) -> int:
    """
    Calculate spread in points for given symbol
    
    Args:
        symbol: Trading symbol
        ask: Ask price
        bid: Bid price
        
    Returns:
        Spread in points
    """
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return 0
        
        # Calculate spread in points
        spread = (ask - bid) / symbol_info.point
        return int(round(spread))
        
    except Exception as e:
        logger.error(f"Spread calculation error: {e}")
        return 0

def calculate_lot_size(risk_percent: float, sl_distance_points: float, symbol: str) -> float:
    """
    Calculate optimal lot size based on risk percentage
    
    Args:
        risk_percent: Risk percentage of account balance
        sl_distance_points: Stop loss distance in points
        symbol: Trading symbol
        
    Returns:
        Calculated lot size
    """
    try:
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            return 0.01  # Default minimum lot
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return 0.01
        
        # Calculate risk amount in account currency
        risk_amount = account_info.balance * (risk_percent / 100)
        
        # Calculate pip value for 1 lot
        if symbol_info.profit_mode == mt5.SYMBOL_CALC_MODE_FOREX:
            # For forex pairs
            tick_value = symbol_info.trade_tick_value
            tick_size = symbol_info.trade_tick_size
            point_value = tick_value * (symbol_info.point / tick_size)
        else:
            # For other instruments (like XAUUSD)
            point_value = symbol_info.trade_tick_value * (symbol_info.point / symbol_info.trade_tick_size)
        
        # Calculate lot size
        if point_value > 0 and sl_distance_points > 0:
            lot_size = risk_amount / (sl_distance_points * point_value)
        else:
            lot_size = 0.01
        
        # Round to symbol's lot step
        lot_step = symbol_info.volume_step
        lot_size = round(lot_size / lot_step) * lot_step
        
        # Ensure lot size is within limits
        min_lot = symbol_info.volume_min
        max_lot = symbol_info.volume_max
        
        lot_size = max(min_lot, min(lot_size, max_lot))
        
        logger.info(f"Calculated lot size: {lot_size} for risk {risk_percent}% and SL {sl_distance_points} points")
        return lot_size
        
    except Exception as e:
        logger.error(f"Lot size calculation error: {e}")
        return 0.01

def check_trading_session() -> bool:
    """
    Check if current time is within allowed trading sessions
    Currently allows London open and NY overlap periods
    
    Returns:
        True if within trading session
    """
    try:
        now = datetime.now().time()
        
        # London session: 08:00 - 17:00 GMT
        london_start = time(8, 0)
        london_end = time(17, 0)
        
        # NY session: 13:00 - 22:00 GMT (overlaps with London 13:00-17:00)
        ny_start = time(13, 0)
        ny_end = time(22, 0)
        
        # Check if in London session
        in_london = london_start <= now <= london_end
        
        # Check if in NY session
        in_ny = ny_start <= now <= ny_end
        
        # Allow trading during either session
        return in_london or in_ny
        
    except Exception as e:
        logger.error(f"Trading session check error: {e}")
        return True  # Default to allow trading if check fails

def format_price(price: float, symbol: str) -> str:
    """
    Format price according to symbol's decimal places
    
    Args:
        price: Price value
        symbol: Trading symbol
        
    Returns:
        Formatted price string
    """
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return f"{price:.5f}"
        
        digits = symbol_info.digits
        return f"{price:.{digits}f}"
        
    except Exception as e:
        logger.error(f"Price formatting error: {e}")
        return f"{price:.5f}"

def calculate_atr_levels(symbol: str, atr_value: float, current_price: float, 
                        is_buy: bool, risk_multiple: float = 1.5) -> Tuple[float, float]:
    """
    Calculate stop loss and take profit levels based on ATR
    
    Args:
        symbol: Trading symbol
        atr_value: Current ATR value
        current_price: Current market price
        is_buy: True for buy orders, False for sell orders
        risk_multiple: Risk/reward ratio
        
    Returns:
        Tuple of (stop_loss, take_profit)
    """
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return current_price, current_price
        
        # Convert ATR to price difference
        atr_price = atr_value
        
        if is_buy:
            stop_loss = current_price - atr_price
            take_profit = current_price + (atr_price * risk_multiple)
        else:
            stop_loss = current_price + atr_price
            take_profit = current_price - (atr_price * risk_multiple)
        
        # Round to symbol's tick size
        tick_size = symbol_info.trade_tick_size
        stop_loss = round(stop_loss / tick_size) * tick_size
        take_profit = round(take_profit / tick_size) * tick_size
        
        return stop_loss, take_profit
        
    except Exception as e:
        logger.error(f"ATR levels calculation error: {e}")
        return current_price, current_price

def get_account_currency() -> str:
    """
    Get account base currency
    
    Returns:
        Account currency code (e.g., 'USD')
    """
    try:
        account_info = mt5.account_info()
        if account_info is None:
            return "USD"  # Default
        
        return account_info.currency
        
    except Exception as e:
        logger.error(f"Account currency error: {e}")
        return "USD"

def is_market_open(symbol: str) -> bool:
    """
    Check if market is open for given symbol
    
    Args:
        symbol: Trading symbol
        
    Returns:
        True if market is open
    """
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return False
        
        # Get current time
        current_time = datetime.now()
        
        # Simple check - market is generally open on weekdays
        # More sophisticated checks would involve session times
        weekday = current_time.weekday()
        
        # Monday = 0, Sunday = 6
        # Market typically closed on weekends
        if weekday >= 5:  # Saturday or Sunday
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Market open check error: {e}")
        return True  # Default to open if check fails

def calculate_pip_value(symbol: str, lot_size: float) -> float:
    """
    Calculate pip value for given symbol and lot size
    
    Args:
        symbol: Trading symbol
        lot_size: Position size in lots
        
    Returns:
        Pip value in account currency
    """
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return 0.0
        
        # Calculate pip value
        if symbol_info.profit_mode == mt5.SYMBOL_CALC_MODE_FOREX:
            tick_value = symbol_info.trade_tick_value
            tick_size = symbol_info.trade_tick_size
            pip_value = (tick_value / tick_size) * symbol_info.point * lot_size
        else:
            # For CFDs, metals, etc.
            pip_value = symbol_info.trade_tick_value * (symbol_info.point / symbol_info.trade_tick_size) * lot_size
        
        return pip_value
        
    except Exception as e:
        logger.error(f"Pip value calculation error: {e}")
        return 0.0

def setup_logging_directory() -> Path:
    """
    Setup logging directory and return path
    
    Returns:
        Path to logs directory
    """
    try:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        return logs_dir
        
    except Exception as e:
        logger.error(f"Logging directory setup error: {e}")
        return Path(".")

def get_telegram_config() -> dict:
    """
    Get Telegram configuration from environment variables
    
    Returns:
        Dictionary with Telegram bot token and chat ID
    """
    return {
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', '8365734234:AAH2uTaZPDD47Lnm3y_Tcr6aj3xGL-bVsgk'),
        'chat_id': os.getenv('TELEGRAM_CHAT_ID', '5061106648')
    }

def send_telegram_message(message: str) -> bool:
    """
    Send message via Telegram (if configured)
    
    Args:
        message: Message to send
        
    Returns:
        True if message sent successfully
    """
    try:
        import requests
        
        config = get_telegram_config()
        if not config['bot_token'] or not config['chat_id']:
            return False
        
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        data = {
            'chat_id': config['chat_id'],
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Telegram message error: {e}")
        return False

def calculate_drawdown(equity_history: list) -> Tuple[float, float]:
    """
    Calculate current and maximum drawdown from equity history
    
    Args:
        equity_history: List of equity values
        
    Returns:
        Tuple of (current_drawdown_percent, max_drawdown_percent)
    """
    try:
        if len(equity_history) < 2:
            return 0.0, 0.0
        
        equity_array = np.array(equity_history)
        
        # Calculate running maximum (peak)
        running_max = np.maximum.accumulate(equity_array)
        
        # Calculate drawdown
        drawdown = (equity_array - running_max) / running_max * 100
        
        current_drawdown = drawdown[-1]
        max_drawdown = np.min(drawdown)
        
        return abs(current_drawdown), abs(max_drawdown)
        
    except Exception as e:
        logger.error(f"Drawdown calculation error: {e}")
        return 0.0, 0.0

def validate_trade_parameters(symbol: str, lot_size: float, sl_points: float, 
                            tp_points: float) -> bool:
    """
    Validate trade parameters before order execution
    
    Args:
        symbol: Trading symbol
        lot_size: Position size
        sl_points: Stop loss in points
        tp_points: Take profit in points
        
    Returns:
        True if parameters are valid
    """
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return False
        
        # Check lot size limits
        if lot_size < symbol_info.volume_min or lot_size > symbol_info.volume_max:
            logger.error(f"Invalid lot size: {lot_size}")
            return False
        
        # Check lot step
        lot_step = symbol_info.volume_step
        if abs(lot_size % lot_step) > 1e-8:
            logger.error(f"Lot size not aligned with step: {lot_size}, step: {lot_step}")
            return False
        
        # Check minimum SL/TP distance
        stops_level = symbol_info.trade_stops_level
        if sl_points < stops_level or tp_points < stops_level:
            logger.error(f"SL/TP too close: SL={sl_points}, TP={tp_points}, min={stops_level}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Trade parameter validation error: {e}")
        return False
