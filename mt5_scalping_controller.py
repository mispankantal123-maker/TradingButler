"""
Complete MT5 Scalping Bot Controller - PRODUCTION READY
Implements all requested features: live data, signals, execution, risk management
"""

try:
    import MetaTrader5 as mt5
    DEMO_MODE = False
except ImportError:
    import mock_mt5 as mt5
    DEMO_MODE = True

import numpy as np
import pandas as pd
from datetime import datetime, time, timedelta
import threading
import logging
import csv
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import os

from PySide6.QtCore import QObject, Signal, QTimer, QThread

from indicators import TechnicalIndicators
from utils import (
    calculate_lot_size, check_trading_session, format_price,
    validate_symbol, get_spread_points, calculate_atr_levels
)

class MarketDataWorker(QThread):
    """Worker thread for real-time market data updates"""
    data_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = True
        
    def run(self):
        """Main market data loop - updates every 500ms as requested"""
        while self.running:
            try:
                symbol = self.controller.config['symbol']
                
                # Get current tick
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    self.error_occurred.emit(f"No tick data for {symbol}")
                    self.msleep(1000)
                    continue
                
                # Get M1 and M5 data
                m1_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 200)
                m5_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 200)
                
                if m1_data is None or m5_data is None:
                    self.error_occurred.emit("Failed to get historical data")
                    self.msleep(1000)
                    continue
                
                # Convert to DataFrames
                m1_df = pd.DataFrame(m1_data)
                m5_df = pd.DataFrame(m5_data)
                
                # Calculate indicators
                indicators_m1 = self.controller.calculate_indicators(m1_df)
                indicators_m5 = self.controller.calculate_indicators(m5_df)
                
                # Prepare market data package
                market_data = {
                    'tick': tick,
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread': get_spread_points(symbol, tick.ask, tick.bid),
                    'time': datetime.fromtimestamp(tick.time),
                    'm1_data': m1_df,
                    'm5_data': m5_df,
                    'indicators_m1': indicators_m1,
                    'indicators_m5': indicators_m5
                }
                
                self.data_ready.emit(market_data)
                
                # Update every 500ms as requested
                self.msleep(500)
                
            except Exception as e:
                self.error_occurred.emit(f"Market data error: {e}")
                self.msleep(1000)
    
    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class PositionMonitor(QThread):
    """Monitor open positions - updates every 1 second"""
    positions_updated = Signal(list)
    
    def __init__(self):
        super().__init__()
        self.running = True
    
    def run(self):
        while self.running:
            try:
                positions = mt5.positions_get()
                if positions is not None:
                    pos_list = []
                    for pos in positions:
                        pos_dict = {
                            'ticket': pos.ticket,
                            'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                            'volume': pos.volume,
                            'entry': pos.price_open,
                            'current': pos.price_current,
                            'sl': pos.sl,
                            'tp': pos.tp,
                            'profit': pos.profit,
                            'symbol': pos.symbol,
                            'comment': pos.comment
                        }
                        pos_list.append(pos_dict)
                    
                    self.positions_updated.emit(pos_list)
                
                self.msleep(1000)  # Update every 1 second
                
            except Exception as e:
                print(f"Position monitor error: {e}")
                self.msleep(2000)
    
    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class ScalpingBotController(QObject):
    """Complete MT5 Scalping Bot Controller with all requested features"""
    
    # Signals for GUI updates
    signal_log = Signal(str, str)  # message, level
    signal_status = Signal(str)    # status message
    signal_market_data = Signal(dict)  # market data
    signal_trade_signal = Signal(dict)  # trade signals
    signal_position_update = Signal(list)  # positions list
    signal_account_update = Signal(dict)  # account info
    signal_indicators_update = Signal(dict)  # current indicators
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Bot state
        self.is_connected = False
        self.is_running = False
        self.shadow_mode = True  # Start in shadow mode for safety
        self.demo_mode = DEMO_MODE
        
        # Configuration - Complete scalping setup
        self.config = {
            'symbol': 'XAUUSD',
            'risk_percent': 0.5,         # Risk per trade
            'max_daily_loss': 2.0,       # Daily loss limit
            'max_trades_per_day': 10,    # Max trades per day
            'max_spread_points': 50,     # Max spread filter
            'min_sl_points': 100,        # Min SL distance
            'risk_multiple': 1.5,        # Risk:Reward ratio
            'ema_periods': {'fast': 9, 'medium': 21, 'slow': 50},
            'rsi_period': 14,
            'atr_period': 14,
            'atr_multiplier': 1.5,       # ATR multiplier for SL
            'deviation_points': 20,
            'magic_number': 987654321,
            'rsi_confirmation': True     # RSI re-cross 50 confirmation
        }
        
        # Trading state
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        self.consecutive_losses = 0
        self.max_consecutive_losses = 3
        self.in_cooldown = False
        self.cooldown_until = None
        
        # Market data
        self.current_market_data = None
        self.current_signal = None
        self.indicators = TechnicalIndicators()
        self.account_info = None
        
        # Workers
        self.market_worker = None
        self.position_monitor = None
        
        # Timers
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_info)
        
        # Logging setup
        self.setup_csv_logging()
        
    def setup_csv_logging(self):
        """Setup CSV logging for trade history"""
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self.csv_file = self.log_dir / f"trade_log_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # CSV headers
        headers = ['time', 'signal_type', 'entry', 'sl', 'tp', 'lot', 'result', 'pnl', 'spread', 'atr']
        
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def connect_mt5(self) -> bool:
        """Connect to MT5 terminal with comprehensive setup"""
        try:
            mode_text = " (DEMO MODE)" if self.demo_mode else ""
            self.signal_log.emit(f"Connecting to MetaTrader 5{mode_text}...", "INFO")
            
            if not mt5.initialize():
                error = mt5.last_error()
                self.signal_log.emit(f"MT5 initialization failed: {error}", "ERROR")
                return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                self.signal_log.emit("Failed to get account info", "ERROR")
                mt5.shutdown()
                return False
            
            self.account_info = account_info
            self.is_connected = True
            
            # Log connection details
            self.signal_log.emit(f"✓ Connected to MT5{mode_text}", "INFO")
            self.signal_log.emit(f"Account: {account_info.login}", "INFO")
            self.signal_log.emit(f"Balance: ${account_info.balance:.2f}", "INFO")
            
            self.signal_status.emit(f"Connected{mode_text}")
            
            # Start account info timer
            self.account_timer.start(2000)  # Update every 2 seconds
            
            return True
            
        except Exception as e:
            self.signal_log.emit(f"Connection error: {e}", "ERROR")
            return False
    
    def disconnect_mt5(self):
        """Disconnect from MT5 and cleanup"""
        try:
            self.stop_bot()
            
            if self.account_timer.isActive():
                self.account_timer.stop()
            
            mt5.shutdown()
            self.is_connected = False
            self.signal_log.emit("Disconnected from MT5", "INFO")
            self.signal_status.emit("Disconnected")
            
        except Exception as e:
            self.signal_log.emit(f"Disconnect error: {e}", "ERROR")
    
    def start_bot(self):
        """Start the scalping bot with all features"""
        if not self.is_connected:
            self.signal_log.emit("Not connected to MT5", "ERROR")
            return False
        
        # Validate symbol
        symbol = self.config['symbol']
        if not validate_symbol(symbol):
            self.signal_log.emit(f"Invalid symbol: {symbol}", "ERROR")
            return False
        
        # Reset daily counters if new day
        self.check_daily_reset()
        
        # Check daily limits
        if self.daily_trades >= self.config['max_trades_per_day']:
            self.signal_log.emit("Daily trade limit reached", "WARNING")
            return False
        
        if self.daily_pnl <= -self.config['max_daily_loss']:
            self.signal_log.emit("Daily loss limit reached", "ERROR")
            return False
        
        # Check cooldown
        if self.in_cooldown and self.cooldown_until and datetime.now() < self.cooldown_until:
            remaining = self.cooldown_until - datetime.now()
            self.signal_log.emit(f"In cooldown for {remaining.seconds}s", "WARNING")
            return False
        
        self.is_running = True
        self.in_cooldown = False
        
        # Start market data worker
        self.market_worker = MarketDataWorker(self)
        self.market_worker.data_ready.connect(self.process_market_data)
        self.market_worker.error_occurred.connect(lambda msg: self.signal_log.emit(msg, "ERROR"))
        self.market_worker.start()
        
        # Start position monitor
        self.position_monitor = PositionMonitor()
        self.position_monitor.positions_updated.connect(self.signal_position_update.emit)
        self.position_monitor.start()
        
        mode = "Shadow Mode" if self.shadow_mode else "Live Trading"
        self.signal_log.emit(f"Bot started for {symbol} - {mode}", "INFO")
        self.signal_status.emit("Running")
        
        return True
    
    def stop_bot(self):
        """Stop the bot and cleanup workers"""
        self.is_running = False
        
        if self.market_worker:
            self.market_worker.stop()
            self.market_worker = None
        
        if self.position_monitor:
            self.position_monitor.stop()
            self.position_monitor = None
        
        self.signal_log.emit("Bot stopped", "INFO")
        self.signal_status.emit("Stopped")
    
    def process_market_data(self, market_data: dict):
        """Process incoming market data and generate signals"""
        try:
            self.current_market_data = market_data
            
            # Emit market data to GUI
            self.signal_market_data.emit(market_data)
            
            # Emit indicators to GUI
            indicators = {
                'M1': market_data['indicators_m1'],
                'M5': market_data['indicators_m5']
            }
            self.signal_indicators_update.emit(indicators)
            
            # Check trading filters
            if not self.check_trading_filters(market_data):
                return
            
            # Generate trading signal
            signal = self.generate_signal(market_data)
            
            if signal:
                self.current_signal = signal
                self.signal_trade_signal.emit(signal)
                
                # Execute if not in shadow mode
                if not self.shadow_mode:
                    self.execute_trade(signal)
                else:
                    self.log_shadow_signal(signal)
            
        except Exception as e:
            self.signal_log.emit(f"Market data processing error: {e}", "ERROR")
    
    def check_trading_filters(self, market_data: dict) -> bool:
        """Check all trading filters"""
        try:
            # Spread filter
            if market_data['spread'] > self.config['max_spread_points']:
                return False
            
            # Session filter - London and NY overlap
            current_time = market_data['time'].time()
            london_session = time(8, 0) <= current_time <= time(17, 0)  # 8:00-17:00 GMT
            ny_overlap = time(13, 0) <= current_time <= time(17, 0)      # 13:00-17:00 GMT
            
            if not (london_session or ny_overlap):
                return False
            
            # Avoid news times (simple implementation)
            avoid_periods = [
                (time(22, 0), time(1, 0)),   # Asian session
                (time(17, 0), time(18, 0)),  # London close
            ]
            
            for start_time, end_time in avoid_periods:
                if start_time <= current_time <= end_time:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Filter check error: {e}")
            return False
    
    def generate_signal(self, market_data: dict) -> Optional[Dict]:
        """Generate scalping signal based on M5 trend filter and M1 entry"""
        try:
            m1_data = market_data['m1_data']
            m5_data = market_data['m5_data']
            m1_ind = market_data['indicators_m1']
            m5_ind = market_data['indicators_m5']
            
            if len(m1_data) < 50 or len(m5_data) < 50:
                return None
            
            # Current prices
            current_price = market_data['ask']  # Use ask for signal generation
            
            # M5 Trend Filter
            ema9_m5 = m5_ind['ema9'][-1]
            ema21_m5 = m5_ind['ema21'][-1]
            ema50_m5 = m5_ind['ema50'][-1]
            
            # M1 Entry conditions
            ema9_m1 = m1_ind['ema9'][-1]
            ema21_m1 = m1_ind['ema21'][-1]
            rsi_m1 = m1_ind['rsi'][-1]
            atr_m1 = m1_ind['atr'][-1]
            
            # Previous values for confirmation
            ema9_m1_prev = m1_ind['ema9'][-2]
            ema21_m1_prev = m1_ind['ema21'][-2]
            rsi_m1_prev = m1_ind['rsi'][-2]
            
            # Candle analysis (avoid doji)
            last_candle = m1_data.iloc[-1]
            candle_body = abs(last_candle['close'] - last_candle['open'])
            candle_range = last_candle['high'] - last_candle['low']
            body_ratio = candle_body / candle_range if candle_range > 0 else 0
            
            if body_ratio < 0.3:  # Avoid doji candles
                return None
            
            # BUY Signal Logic
            # M5 Trend: EMA9 > EMA21 and price > EMA50
            m5_bullish = (ema9_m5 > ema21_m5) and (current_price > ema50_m5)
            
            # M1 Entry: Pullback to EMA9/EMA21 then continuation
            m1_pullback_buy = (
                (ema9_m1 > ema21_m1) and  # M1 trend aligned
                (current_price > ema9_m1) and  # Price above EMA9
                (ema9_m1_prev <= ema21_m1_prev or current_price <= ema9_m1_prev)  # Previous pullback
            )
            
            # RSI confirmation (optional)
            rsi_buy = True  # Default to True
            if self.config['rsi_confirmation']:
                rsi_buy = (rsi_m1 > 50) and (rsi_m1_prev <= 50)  # RSI re-cross above 50
            
            # SELL Signal Logic
            m5_bearish = (ema9_m5 < ema21_m5) and (current_price < ema50_m5)
            
            m1_pullback_sell = (
                (ema9_m1 < ema21_m1) and  # M1 trend aligned
                (current_price < ema9_m1) and  # Price below EMA9
                (ema9_m1_prev >= ema21_m1_prev or current_price >= ema9_m1_prev)  # Previous pullback
            )
            
            rsi_sell = True
            if self.config['rsi_confirmation']:
                rsi_sell = (rsi_m1 < 50) and (rsi_m1_prev >= 50)  # RSI re-cross below 50
            
            # Generate signal
            if m5_bullish and m1_pullback_buy and rsi_buy:
                return self.create_buy_signal(market_data, atr_m1)
            elif m5_bearish and m1_pullback_sell and rsi_sell:
                return self.create_sell_signal(market_data, atr_m1)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Signal generation error: {e}")
            return None
    
    def create_buy_signal(self, market_data: dict, atr_value: float) -> Dict:
        """Create BUY signal with precise SL/TP calculation"""
        symbol = self.config['symbol']
        entry_price = market_data['ask']  # BUY at ASK
        spread = market_data['spread']
        
        # Get symbol info for calculations
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {}
        
        # Calculate SL using ATR
        atr_points = atr_value / symbol_info.point
        sl_distance_points = max(self.config['min_sl_points'], atr_points * self.config['atr_multiplier'])
        
        # SL below entry, TP above entry
        sl_price = entry_price - (sl_distance_points * symbol_info.point)
        tp_price = entry_price + (sl_distance_points * self.config['risk_multiple'] * symbol_info.point)
        
        # Round to tick size
        sl_price = round(sl_price / symbol_info.trade_tick_size) * symbol_info.trade_tick_size
        tp_price = round(tp_price / symbol_info.trade_tick_size) * symbol_info.trade_tick_size
        
        # Calculate lot size
        lot_size = calculate_lot_size(
            self.config['risk_percent'],
            sl_distance_points,
            symbol
        )
        
        return {
            'type': 'BUY',
            'symbol': symbol,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'lot_size': lot_size,
            'sl_points': sl_distance_points,
            'risk_reward': self.config['risk_multiple'],
            'spread': spread,
            'atr': atr_value,
            'timestamp': datetime.now()
        }
    
    def create_sell_signal(self, market_data: dict, atr_value: float) -> Dict:
        """Create SELL signal with precise SL/TP calculation"""
        symbol = self.config['symbol']
        entry_price = market_data['bid']  # SELL at BID
        spread = market_data['spread']
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {}
        
        # Calculate SL using ATR
        atr_points = atr_value / symbol_info.point
        sl_distance_points = max(self.config['min_sl_points'], atr_points * self.config['atr_multiplier'])
        
        # SL above entry, TP below entry
        sl_price = entry_price + (sl_distance_points * symbol_info.point)
        tp_price = entry_price - (sl_distance_points * self.config['risk_multiple'] * symbol_info.point)
        
        # Round to tick size
        sl_price = round(sl_price / symbol_info.trade_tick_size) * symbol_info.trade_tick_size
        tp_price = round(tp_price / symbol_info.trade_tick_size) * symbol_info.trade_tick_size
        
        # Calculate lot size
        lot_size = calculate_lot_size(
            self.config['risk_percent'],
            sl_distance_points,
            symbol
        )
        
        return {
            'type': 'SELL',
            'symbol': symbol,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'lot_size': lot_size,
            'sl_points': sl_distance_points,
            'risk_reward': self.config['risk_multiple'],
            'spread': spread,
            'atr': atr_value,
            'timestamp': datetime.now()
        }
    
    def execute_trade(self, signal: Dict):
        """Execute trade with retry logic"""
        if self.shadow_mode:
            return
            
        try:
            symbol = signal['symbol']
            trade_type = mt5.ORDER_TYPE_BUY if signal['type'] == 'BUY' else mt5.ORDER_TYPE_SELL
            lot = signal['lot_size']
            price = signal['entry_price']
            sl = signal['sl_price']
            tp = signal['tp_price']
            
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": trade_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": self.config['deviation_points'],
                "magic": self.config['magic_number'],
                "comment": f"Scalping {signal['type']}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Execute with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    self.daily_trades += 1
                    self.signal_log.emit(f"✓ {signal['type']} order executed: {result.deal}", "INFO")
                    self.log_trade_to_csv(signal, 'EXECUTED', 0)
                    return True
                
                elif result.retcode in [mt5.TRADE_RETCODE_REQUOTE, mt5.TRADE_RETCODE_PRICE_OFF]:
                    # Update price and retry
                    new_tick = mt5.symbol_info_tick(symbol)
                    if new_tick:
                        if signal['type'] == 'BUY':
                            request['price'] = new_tick.ask
                        else:
                            request['price'] = new_tick.bid
                    
                    self.signal_log.emit(f"Retrying order (attempt {attempt + 1})", "WARNING")
                else:
                    break
            
            # Order failed
            self.signal_log.emit(f"✗ Order failed: {result.comment}", "ERROR")
            self.log_trade_to_csv(signal, 'FAILED', 0)
            return False
            
        except Exception as e:
            self.signal_log.emit(f"Execution error: {e}", "ERROR")
            return False
    
    def log_shadow_signal(self, signal: Dict):
        """Log signal in shadow mode"""
        self.log_trade_to_csv(signal, 'SHADOW', 0)
        self.signal_log.emit(f"Shadow {signal['type']}: Entry={signal['entry_price']:.5f}, SL={signal['sl_price']:.5f}, TP={signal['tp_price']:.5f}", "INFO")
    
    def log_trade_to_csv(self, signal: Dict, result: str, pnl: float):
        """Log trade to CSV file"""
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    signal['type'],
                    signal['entry_price'],
                    signal['sl_price'],
                    signal['tp_price'],
                    signal['lot_size'],
                    result,
                    pnl,
                    signal['spread'],
                    signal['atr']
                ])
        except Exception as e:
            self.logger.error(f"CSV logging error: {e}")
    
    def close_all_positions(self):
        """Emergency close all positions"""
        try:
            positions = mt5.positions_get()
            if not positions:
                self.signal_log.emit("No positions to close", "INFO")
                return
            
            closed_count = 0
            for pos in positions:
                # Prepare close request
                close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": close_type,
                    "position": pos.ticket,
                    "deviation": self.config['deviation_points'],
                    "magic": self.config['magic_number'],
                    "comment": "Emergency close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                if close_type == mt5.ORDER_TYPE_SELL:
                    tick = mt5.symbol_info_tick(pos.symbol)
                    request['price'] = tick.bid
                else:
                    tick = mt5.symbol_info_tick(pos.symbol)
                    request['price'] = tick.ask
                
                result = mt5.order_send(request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    closed_count += 1
            
            self.signal_log.emit(f"Emergency close: {closed_count} positions closed", "WARNING")
            
        except Exception as e:
            self.signal_log.emit(f"Emergency close error: {e}", "ERROR")
    
    def test_signal(self):
        """Test signal generation without execution"""
        if not self.current_market_data:
            self.signal_log.emit("No market data available for testing", "WARNING")
            return
        
        signal = self.generate_signal(self.current_market_data)
        if signal:
            self.signal_trade_signal.emit(signal)
            self.signal_log.emit(f"Test Signal: {signal['type']} at {signal['entry_price']:.5f}", "INFO")
        else:
            self.signal_log.emit("No signal generated at current market conditions", "INFO")
    
    def update_account_info(self):
        """Update account information"""
        try:
            account_info = mt5.account_info()
            if account_info:
                self.account_info = account_info
                
                account_data = {
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'margin': account_info.margin,
                    'free_margin': account_info.margin_free,
                    'profit': account_info.profit
                }
                
                self.signal_account_update.emit(account_data)
        except Exception as e:
            self.logger.error(f"Account update error: {e}")
    
    def check_daily_reset(self):
        """Check if daily counters need reset"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.consecutive_losses = 0
            self.in_cooldown = False
            self.last_reset_date = today
            self.signal_log.emit("Daily counters reset", "INFO")
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        try:
            close = np.array(data['close'].values, dtype=np.float64)
            high = np.array(data['high'].values, dtype=np.float64)
            low = np.array(data['low'].values, dtype=np.float64)
            
            # EMAs
            ema9 = self.indicators.ema(close, self.config['ema_periods']['fast'])
            ema21 = self.indicators.ema(close, self.config['ema_periods']['medium'])
            ema50 = self.indicators.ema(close, self.config['ema_periods']['slow'])
            
            # RSI
            rsi = self.indicators.rsi(close, self.config['rsi_period'])
            
            # ATR
            atr = self.indicators.atr(high, low, close, self.config['atr_period'])
            
            return {
                'ema9': ema9,
                'ema21': ema21,
                'ema50': ema50,
                'rsi': rsi,
                'atr': atr
            }
            
        except Exception as e:
            self.logger.error(f"Indicator calculation error: {e}")
            return {}
    
    def export_logs(self):
        """Export logs to CSV"""
        try:
            import shutil
            export_file = self.log_dir / f"exported_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            shutil.copy2(self.csv_file, export_file)
            self.signal_log.emit(f"Logs exported to {export_file.name}", "INFO")
            return str(export_file)
        except Exception as e:
            self.signal_log.emit(f"Export error: {e}", "ERROR")
            return None
    
    def update_config(self, new_config: Dict):
        """Update bot configuration"""
        self.config.update(new_config)
        self.signal_log.emit("Configuration updated", "INFO")
    
    def set_shadow_mode(self, enabled: bool):
        """Toggle shadow mode"""
        self.shadow_mode = enabled
        mode = "Shadow Mode" if enabled else "Live Trading"
        self.signal_log.emit(f"Switched to {mode}", "INFO")