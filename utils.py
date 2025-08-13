
"""
Utility Functions
Helper functions for trading operations, risk management, and system utilities
"""

import MetaTrader5 as mt5
import numpy as np
from datetime import datetime, time
from typing import Optional, Tuple
import logging
import os
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

def calculate_lot_size(risk_percent: float, sl_distance_points: float, symbol: str) -> float:
    """Calculate lot size based on risk percentage and stop loss distance"""
    try:
        account_info = mt5.account_info()
        if account_info is None:
            return 0.01
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return 0.01
        
        # Calculate risk amount in account currency
        risk_amount = account_info.balance * (risk_percent / 100)
        
        # Calculate value per point
        if symbol_info.trade_contract_size > 0:
            value_per_point = symbol_info.trade_tick_value
        else:
            value_per_point = 1.0
        
        # Calculate lot size
        lot_size = risk_amount / (sl_distance_points * value_per_point)
        
        # Round to valid lot size
        lot_step = symbol_info.volume_step
        lot_size = round(lot_size / lot_step) * lot_step
        
        # Ensure within min/max limits
        lot_size = max(symbol_info.volume_min, min(lot_size, symbol_info.volume_max))
        
        return lot_size
        
    except Exception as e:
        logger.error(f"Error calculating lot size: {e}")
        return 0.01

def check_trading_session() -> bool:
    """Check if current time is within trading session"""
    try:
        current_time = datetime.now().time()
        
        # London session: 08:00 - 17:00 GMT
        london_start = time(8, 0)
        london_end = time(17, 0)
        
        # New York session: 13:00 - 22:00 GMT
        ny_start = time(13, 0)
        ny_end = time(22, 0)
        
        # Check if within trading sessions
        in_london = london_start <= current_time <= london_end
        in_ny = ny_start <= current_time <= ny_end
        
        return in_london or in_ny
        
    except Exception as e:
        logger.error(f"Error checking trading session: {e}")
        return False

def format_price(price: float, digits: int = 5) -> str:
    """Format price to specified decimal places"""
    return f"{price:.{digits}f}"

def validate_symbol(symbol: str) -> bool:
    """Validate if symbol is available for trading"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return False
        
        # Check if symbol is visible and tradeable
        if not symbol_info.visible:
            # Try to add symbol to Market Watch
            if not mt5.symbol_select(symbol, True):
                return False
        
        return symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL
        
    except Exception as e:
        logger.error(f"Error validating symbol {symbol}: {e}")
        return False

def get_spread_points(symbol: str, ask: float, bid: float) -> float:
    """Calculate spread in points"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return 999.0
        
        spread = (ask - bid) / symbol_info.point
        return spread
        
    except Exception as e:
        logger.error(f"Error calculating spread: {e}")
        return 999.0

def calculate_atr_levels(atr: float, current_price: float, symbol: str) -> Tuple[float, float]:
    """Calculate ATR-based support and resistance levels"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return current_price, current_price
        
        atr_points = atr / symbol_info.point
        
        support = current_price - (atr_points * symbol_info.point)
        resistance = current_price + (atr_points * symbol_info.point)
        
        return support, resistance
        
    except Exception as e:
        logger.error(f"Error calculating ATR levels: {e}")
        return current_price, current_price

def send_telegram_message(message: str) -> bool:
    """Send message to Telegram (optional feature)"""
    try:
        # Telegram configuration (optional)
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not telegram_token or not chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

def check_margin_requirement(symbol: str, lot_size: float, order_type: int) -> bool:
    """Check if there's sufficient margin for the trade"""
    try:
        account_info = mt5.account_info()
        symbol_info = mt5.symbol_info(symbol)
        
        if account_info is None or symbol_info is None:
            return False
        
        # Calculate required margin
        required_margin = lot_size * symbol_info.trade_contract_size
        
        # Check available margin
        available_margin = account_info.margin_free
        
        return available_margin >= required_margin
        
    except Exception as e:
        logger.error(f"Error checking margin requirement: {e}")
        return False

def get_symbol_specifications(symbol: str) -> dict:
    """Get comprehensive symbol specifications"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {}
        
        return {
            'name': symbol_info.name,
            'digits': symbol_info.digits,
            'point': symbol_info.point,
            'volume_min': symbol_info.volume_min,
            'volume_max': symbol_info.volume_max,
            'volume_step': symbol_info.volume_step,
            'trade_tick_size': symbol_info.trade_tick_size,
            'trade_tick_value': symbol_info.trade_tick_value,
            'trade_stops_level': symbol_info.trade_stops_level,
            'trade_contract_size': symbol_info.trade_contract_size
        }
        
    except Exception as e:
        logger.error(f"Error getting symbol specifications: {e}")
        return {}
