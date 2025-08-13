"""
MT5 Bot Controller
Handles MT5 connection, trading logic, and market data processing
"""

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    import mock_mt5 as mt5
    MT5_AVAILABLE = False
import numpy as np
import pandas as pd
from datetime import datetime, time
import threading
import logging
from typing import Optional, Dict, List, Tuple
import os

from PySide6.QtCore import QObject, Signal, QTimer, QThread

from indicators import TechnicalIndicators
from utils import (
    calculate_lot_size, check_trading_session, format_price,
    validate_symbol, get_spread_points, calculate_atr_levels
)

class BotController(QObject):
    """Main controller for the MT5 trading bot"""
    
    # Signals for GUI updates
    signal_log = Signal(str, str)  # message, level
    signal_status = Signal(str)    # status message
    signal_market_data = Signal(dict)  # market data
    signal_trade_signal = Signal(dict)  # trade signals
    signal_position_update = Signal(list)  # positions list
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Bot state
        self.is_connected = False
        self.is_running = False
        self.shadow_mode = True
        
        # Configuration
        self.config = {
            'symbol': 'XAUUSD',
            'risk_percent': 0.5,
            'max_daily_loss': 2.0,
            'max_trades_per_day': 10,
            'max_spread_points': 50,
            'min_sl_points': 100,
            'risk_multiple': 1.5,
            'ema_periods': {'fast': 9, 'medium': 21, 'slow': 50},
            'rsi_period': 14,
            'atr_period': 14,
            'deviation_points': 20,
            'magic_number': 987654321
        }
        
        # Trading state
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        self.consecutive_losses = 0
        self.max_consecutive_losses = 3
        self.in_cooldown = False
        
        # Market data
        self.current_tick = None
        self.indicators = TechnicalIndicators()
        
        # Timers
        self.market_timer = QTimer()
        self.market_timer.timeout.connect(self.update_market_data)
        
    def connect_mt5(self) -> bool:
        """Connect to MT5 terminal"""
        try:
            if not mt5.initialize():
                error = mt5.last_error()
                self.signal_log.emit(f"Failed to initialize MT5: {error}", "ERROR")
                return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                self.signal_log.emit("Failed to get account info", "ERROR")
                return False
            
            self.is_connected = True
            self.signal_log.emit(f"Connected to MT5 - Account: {account_info.login}", "INFO")
            self.signal_status.emit("Connected")
            
            return True
            
        except Exception as e:
            self.signal_log.emit(f"MT5 connection error: {e}", "ERROR")
            return False
    
    def disconnect_mt5(self):
        """Disconnect from MT5 terminal"""
        try:
            if self.is_running:
                self.stop_bot()
            
            mt5.shutdown()
            self.is_connected = False
            self.signal_log.emit("Disconnected from MT5", "INFO")
            self.signal_status.emit("Disconnected")
            
        except Exception as e:
            self.signal_log.emit(f"Disconnect error: {e}", "ERROR")
    
    def update_config(self, new_config: Dict):
        """Update bot configuration"""
        self.config.update(new_config)
        self.signal_log.emit("Configuration updated", "INFO")
    
    def start_bot(self):
        """Start the trading bot"""
        if not self.is_connected:
            self.signal_log.emit("Not connected to MT5", "ERROR")
            return False
        
        symbol = self.config['symbol']
        if not validate_symbol(symbol):
            self.signal_log.emit(f"Invalid symbol: {symbol}", "ERROR")
            return False
        
        self.is_running = True
        self.signal_log.emit(f"Bot started for {symbol}", "INFO")
        self.signal_status.emit("Running")
        
        # Start market data timer (update every second)
        self.market_timer.start(1000)
        
        return True
    
    def stop_bot(self):
        """Stop the trading bot"""
        self.is_running = False
        self.market_timer.stop()
        self.signal_log.emit("Bot stopped", "INFO")
        self.signal_status.emit("Stopped")
    
    def toggle_shadow_mode(self, enabled: bool):
        """Toggle shadow mode (signals only, no actual trades)"""
        self.shadow_mode = enabled
        mode = "Shadow" if enabled else "Live"
        self.signal_log.emit(f"Mode changed to: {mode}", "INFO")
    
    def update_market_data(self):
        """Update market data and process trading logic"""
        if not self.is_running or not self.is_connected:
            return
        
        try:
            symbol = self.config['symbol']
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return
            
            self.current_tick = tick
            
            # Get spread in points
            spread_points = get_spread_points(symbol, tick.ask, tick.bid)
            
            # Check if spread is acceptable
            if spread_points > self.config['max_spread_points']:
                return
            
            # Get market data for indicators
            m1_data = self.get_timeframe_data(symbol, mt5.TIMEFRAME_M1, 100)
            m5_data = self.get_timeframe_data(symbol, mt5.TIMEFRAME_M5, 100)
            
            if m1_data is None or m5_data is None:
                return
            
            # Calculate indicators
            indicators_m1 = self.calculate_indicators(m1_data)
            indicators_m5 = self.calculate_indicators(m5_data)
            
            # Emit market data signal
            market_data = {
                'symbol': symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': spread_points,
                'time': datetime.fromtimestamp(tick.time),
                'indicators_m1': indicators_m1,
                'indicators_m5': indicators_m5
            }
            self.signal_market_data.emit(market_data)
            
            # Process trading logic
            self.process_trading_logic(market_data)
            
        except Exception as e:
            self.signal_log.emit(f"Market data update error: {e}", "ERROR")
    
    def get_timeframe_data(self, symbol: str, timeframe: int, count: int) -> Optional[pd.DataFrame]:
        """Get historical data for specified timeframe"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting {symbol} data: {e}")
            return None
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate technical indicators for given data"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            
            # EMAs
            ema9 = self.indicators.ema(close, self.config['ema_periods']['fast'])
            ema21 = self.indicators.ema(close, self.config['ema_periods']['medium'])
            ema50 = self.indicators.ema(close, self.config['ema_periods']['slow'])
            
            # RSI
            rsi = self.indicators.rsi(close, self.config['rsi_period'])
            
            # ATR
            atr = self.indicators.atr(high, low, close, self.config['atr_period'])
            
            return {
                'ema9': ema9[-1] if len(ema9) > 0 else None,
                'ema21': ema21[-1] if len(ema21) > 0 else None,
                'ema50': ema50[-1] if len(ema50) > 0 else None,
                'rsi': rsi[-1] if len(rsi) > 0 else None,
                'atr': atr[-1] if len(atr) > 0 else None
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def process_trading_logic(self, market_data: Dict):
        """Main trading logic processor"""
        try:
            # Reset daily counters if new day
            self.reset_daily_counters()
            
            # Check daily limits
            if not self.check_daily_limits():
                return
            
            # Check trading session
            if not check_trading_session():
                return
            
            # Check cooldown
            if self.in_cooldown:
                return
            
            # Get indicators
            indicators_m1 = market_data['indicators_m1']
            indicators_m5 = market_data['indicators_m5']
            
            # Check if all indicators are available
            required_indicators = ['ema9', 'ema21', 'ema50', 'rsi', 'atr']
            if not all(indicators_m1.get(k) is not None for k in required_indicators):
                return
            if not all(indicators_m5.get(k) is not None for k in required_indicators):
                return
            
            # Analyze signals
            signal = self.analyze_trading_signal(market_data, indicators_m1, indicators_m5)
            
            if signal:
                self.signal_trade_signal.emit(signal)
                
                # Execute trade if not in shadow mode
                if not self.shadow_mode:
                    self.execute_trade(signal)
            
        except Exception as e:
            self.signal_log.emit(f"Trading logic error: {e}", "ERROR")
    
    def analyze_trading_signal(self, market_data: Dict, ind_m1: Dict, ind_m5: Dict) -> Optional[Dict]:
        """Analyze market conditions for trading signals"""
        try:
            current_price = market_data['ask']
            
            # M5 Trend Filter
            m5_bullish = ind_m5['ema9'] > ind_m5['ema21'] and current_price > ind_m5['ema50']
            m5_bearish = ind_m5['ema9'] < ind_m5['ema21'] and current_price < ind_m5['ema50']
            
            # M1 Entry Conditions
            m1_pullback_buy = (current_price > ind_m1['ema9'] and 
                              ind_m1['ema9'] > ind_m1['ema21'] and
                              ind_m1['rsi'] > 50)
            
            m1_pullback_sell = (current_price < ind_m1['ema9'] and 
                               ind_m1['ema9'] < ind_m1['ema21'] and
                               ind_m1['rsi'] < 50)
            
            # Generate signals
            if m5_bullish and m1_pullback_buy:
                return self.create_buy_signal(market_data, ind_m1)
            elif m5_bearish and m1_pullback_sell:
                return self.create_sell_signal(market_data, ind_m1)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Signal analysis error: {e}")
            return None
    
    def create_buy_signal(self, market_data: Dict, indicators: Dict) -> Dict:
        """Create BUY signal with SL/TP levels"""
        symbol = market_data['symbol']
        entry_price = market_data['ask']
        atr = indicators['atr']
        
        # Calculate SL/TP using ATR
        sl_distance = max(self.config['min_sl_points'], atr * 10000)  # Convert to points
        sl_price = entry_price - (sl_distance / 10000)
        tp_price = entry_price + (sl_distance * self.config['risk_multiple'] / 10000)
        
        # Calculate lot size
        lot_size = calculate_lot_size(
            self.config['risk_percent'],
            sl_distance,
            symbol
        )
        
        return {
            'type': 'BUY',
            'symbol': symbol,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'lot_size': lot_size,
            'sl_distance': sl_distance,
            'risk_reward': self.config['risk_multiple'],
            'timestamp': datetime.now()
        }
    
    def create_sell_signal(self, market_data: Dict, indicators: Dict) -> Dict:
        """Create SELL signal with SL/TP levels"""
        symbol = market_data['symbol']
        entry_price = market_data['bid']
        atr = indicators['atr']
        
        # Calculate SL/TP using ATR
        sl_distance = max(self.config['min_sl_points'], atr * 10000)  # Convert to points
        sl_price = entry_price + (sl_distance / 10000)
        tp_price = entry_price - (sl_distance * self.config['risk_multiple'] / 10000)
        
        # Calculate lot size
        lot_size = calculate_lot_size(
            self.config['risk_percent'],
            sl_distance,
            symbol
        )
        
        return {
            'type': 'SELL',
            'symbol': symbol,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'lot_size': lot_size,
            'sl_distance': sl_distance,
            'risk_reward': self.config['risk_multiple'],
            'timestamp': datetime.now()
        }
    
    def execute_trade(self, signal: Dict):
        """Execute trade based on signal"""
        try:
            symbol = signal['symbol']
            trade_type = mt5.ORDER_TYPE_BUY if signal['type'] == 'BUY' else mt5.ORDER_TYPE_SELL
            
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": signal['lot_size'],
                "type": trade_type,
                "price": signal['entry_price'],
                "sl": signal['sl_price'],
                "tp": signal['tp_price'],
                "deviation": self.config['deviation_points'],
                "magic": self.config['magic_number'],
                "comment": f"ScalpBot_{signal['type']}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.signal_log.emit(f"Order failed: {result.comment} (Code: {result.retcode})", "ERROR")
                return False
            
            # Update counters
            self.daily_trades += 1
            
            self.signal_log.emit(
                f"{signal['type']} order executed: {symbol} @ {signal['entry_price']:.5f}, "
                f"SL: {signal['sl_price']:.5f}, TP: {signal['tp_price']:.5f}", 
                "INFO"
            )
            
            return True
            
        except Exception as e:
            self.signal_log.emit(f"Trade execution error: {e}", "ERROR")
            return False
    
    def reset_daily_counters(self):
        """Reset daily counters at start of new day"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.consecutive_losses = 0
            self.in_cooldown = False
            self.last_reset_date = current_date
            self.signal_log.emit("Daily counters reset", "INFO")
    
    def check_daily_limits(self) -> bool:
        """Check if daily trading limits are exceeded"""
        # Check max trades per day
        if self.daily_trades >= self.config['max_trades_per_day']:
            return False
        
        # Check max daily loss
        account_info = mt5.account_info()
        if account_info:
            daily_loss_percent = abs(self.daily_pnl) / account_info.balance * 100
            if daily_loss_percent >= self.config['max_daily_loss']:
                return False
        
        return True
    
    def get_positions(self) -> List[Dict]:
        """Get current open positions"""
        try:
            positions = mt5.positions_get(symbol=self.config['symbol'])
            if positions is None:
                return []
            
            position_list = []
            for pos in positions:
                position_list.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'comment': pos.comment
                })
            
            return position_list
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
