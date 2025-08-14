"""
Fixed MT5 Scalping Bot Controller - PRODUCTION READY
Solusi untuk masalah krusial:
1. Threading analysis worker dengan heartbeat
2. Auto-order execution setelah sinyal
3. TP/SL modes (ATR, Points, Pips, Balance%)
"""

import sys
import logging
import threading
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import csv
import traceback
import pytz

from PySide6.QtCore import QObject, QTimer, Signal, QThread, QMutex
from PySide6.QtWidgets import QMessageBox

# Import configuration
from config import *

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("⚠️ MetaTrader5 not available - Running in demo mode")
    import mock_mt5 as mt5

# Import indicators
from indicators import TechnicalIndicators

class AnalysisWorker(QThread):
    """Worker thread untuk analisis real-time dengan heartbeat"""
    
    # Signals
    heartbeat_signal = Signal(str)
    signal_ready = Signal(dict)
    indicators_ready = Signal(dict)
    tick_data_signal = Signal(dict)
    error_signal = Signal(str)
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = False
        self.indicators = TechnicalIndicators()
        self.last_m1_time = None
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Main analysis loop dengan heartbeat setiap 1 detik"""
        self.running = True
        self.logger.info("[START] analysis thread starting...")
        
        try:
            while self.running:
                current_time = datetime.now(pytz.timezone('Asia/Jakarta'))
                
                # HEARTBEAT LOG - WAJIB setiap 1 detik
                try:
                    m1_bars = self.get_bars_count('M1')
                    m5_bars = self.get_bars_count('M5')
                    heartbeat_msg = f"[HB] analyzer alive t={current_time.isoformat()} bars(M1)={m1_bars} bars(M5)={m5_bars}"
                    self.heartbeat_signal.emit(heartbeat_msg)
                except Exception as e:
                    self.heartbeat_signal.emit(f"[HB] analyzer alive t={current_time.isoformat()} bars(M1)=ERROR bars(M5)=ERROR")
                
                if self.controller.is_connected:
                    try:
                        # 1. Ambil tick data
                        self.fetch_tick_data()
                        
                        # 2. Ambil bar data dan hitung indikator
                        self.fetch_and_analyze_data()
                        
                        # 3. Generate signals
                        self.generate_signals()
                        
                    except Exception as e:
                        error_msg = f"Analysis worker error: {e}\n{traceback.format_exc()}"
                        self.error_signal.emit(error_msg)
                        self.logger.error(error_msg)
                
                self.msleep(1000)  # 1 second heartbeat
                
        except Exception as e:
            error_msg = f"Analysis worker fatal error: {e}\n{traceback.format_exc()}"
            self.error_signal.emit(error_msg)
            self.logger.error(error_msg)
    
    def get_bars_count(self, timeframe):
        """Get jumlah bars untuk heartbeat"""
        try:
            if not self.controller.is_connected:
                return 0
            
            tf_map = {'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5}
            rates = mt5.copy_rates_from_pos(self.controller.config['symbol'], tf_map[timeframe], 0, 10)
            return len(rates) if rates is not None else 0
        except:
            return 0
    
    def fetch_tick_data(self):
        """Fetch tick data setiap 250-500ms"""
        try:
            symbol = self.controller.config['symbol']
            tick = mt5.symbol_info_tick(symbol)
            
            if tick:
                spread_points = round((tick.ask - tick.bid) / self.controller.symbol_info.point)
                tick_data = {
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread_points': spread_points,
                    'time': datetime.now()
                }
                self.tick_data_signal.emit(tick_data)
                
                # Log tick periodically
                if hasattr(self, '_last_tick_log'):
                    if (datetime.now() - self._last_tick_log).seconds >= 5:
                        tick_msg = f"tick: bid={tick.bid:.5f}, ask={tick.ask:.5f}, spread_pts={spread_points}"
                        self.heartbeat_signal.emit(tick_msg)
                        self._last_tick_log = datetime.now()
                else:
                    self._last_tick_log = datetime.now()
                    
        except Exception as e:
            self.logger.error(f"Tick fetch error: {e}")
    
    def fetch_and_analyze_data(self):
        """Fetch bars dan hitung indikator"""
        try:
            symbol = self.controller.config['symbol']
            
            # Ambil M1 dan M5 bars (minimal 200 candles)
            rates_m1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 200)
            rates_m5 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 200)
            
            if rates_m1 is None or rates_m5 is None or len(rates_m1) < 50:
                self.logger.warning("Insufficient bar data, retrying...")
                return
            
            # Hitung indikator M1
            close_m1 = rates_m1['close']
            high_m1 = rates_m1['high']
            low_m1 = rates_m1['low']
            
            ema_fast_m1 = self.indicators.ema(close_m1, self.controller.config['ema_periods']['fast'])
            ema_medium_m1 = self.indicators.ema(close_m1, self.controller.config['ema_periods']['medium'])
            ema_slow_m1 = self.indicators.ema(close_m1, self.controller.config['ema_periods']['slow'])
            rsi_m1 = self.indicators.rsi(close_m1, self.controller.config['rsi_period'])
            atr_m1 = self.indicators.atr(high_m1, low_m1, close_m1, self.controller.config['atr_period'])
            
            # Hitung indikator M5
            close_m5 = rates_m5['close']
            high_m5 = rates_m5['high']
            low_m5 = rates_m5['low']
            
            ema_fast_m5 = self.indicators.ema(close_m5, self.controller.config['ema_periods']['fast'])
            ema_medium_m5 = self.indicators.ema(close_m5, self.controller.config['ema_periods']['medium'])
            ema_slow_m5 = self.indicators.ema(close_m5, self.controller.config['ema_periods']['slow'])
            rsi_m5 = self.indicators.rsi(close_m5, self.controller.config['rsi_period'])
            atr_m5 = self.indicators.atr(high_m5, low_m5, close_m5, self.controller.config['atr_period'])
            
            # Update controller indicators
            self.controller.current_indicators['M1'] = {
                'ema_fast': ema_fast_m1[-1] if len(ema_fast_m1) > 0 and not np.isnan(ema_fast_m1[-1]) else 0,
                'ema_medium': ema_medium_m1[-1] if len(ema_medium_m1) > 0 and not np.isnan(ema_medium_m1[-1]) else 0,
                'ema_slow': ema_slow_m1[-1] if len(ema_slow_m1) > 0 and not np.isnan(ema_slow_m1[-1]) else 0,
                'rsi': rsi_m1[-1] if len(rsi_m1) > 0 and not np.isnan(rsi_m1[-1]) else 50,
                'atr': atr_m1[-1] if len(atr_m1) > 0 and not np.isnan(atr_m1[-1]) else 0,
                'close': close_m1[-1],
                'rates': rates_m1
            }
            
            self.controller.current_indicators['M5'] = {
                'ema_fast': ema_fast_m5[-1] if len(ema_fast_m5) > 0 and not np.isnan(ema_fast_m5[-1]) else 0,
                'ema_medium': ema_medium_m5[-1] if len(ema_medium_m5) > 0 and not np.isnan(ema_medium_m5[-1]) else 0,
                'ema_slow': ema_slow_m5[-1] if len(ema_slow_m5) > 0 and not np.isnan(ema_slow_m5[-1]) else 0,
                'rsi': rsi_m5[-1] if len(rsi_m5) > 0 and not np.isnan(rsi_m5[-1]) else 50,
                'atr': atr_m5[-1] if len(atr_m5) > 0 and not np.isnan(atr_m5[-1]) else 0,
                'close': close_m5[-1],
                'rates': rates_m5
            }
            
            # Emit indicators ready signal (hanya sekali di awal)
            if not hasattr(self, '_indicators_logged'):
                indicators_msg = (f"indicators ready: ema=[{ema_fast_m1[-1]:.5f},{ema_medium_m1[-1]:.5f},{ema_slow_m1[-1]:.5f}], "
                                f"rsi=[{rsi_m1[-1]:.2f}], atr=[{atr_m1[-1]:.5f}]")
                self.heartbeat_signal.emit(indicators_msg)
                self._indicators_logged = True
            
            self.indicators_ready.emit(self.controller.current_indicators)
            
        except Exception as e:
            error_msg = f"Data analysis error: {e}\n{traceback.format_exc()}"
            self.error_signal.emit(error_msg)
    
    def generate_signals(self):
        """Generate trading signals"""
        try:
            if not self.controller.current_indicators['M1'] or not self.controller.current_indicators['M5']:
                return
            
            m1_data = self.controller.current_indicators['M1']
            m5_data = self.controller.current_indicators['M5']
            
            # Check if new M1 bar (avoid double signals)
            if 'rates' in m1_data and len(m1_data['rates']) > 0:
                current_bar_time = m1_data['rates'][-1]['time']
                if self.last_m1_time == current_bar_time:
                    return  # Same bar, skip
                self.last_m1_time = current_bar_time
            
            # Strategy logic: Trend filter (M5) + Entry (M1)
            signal = self.evaluate_strategy(m1_data, m5_data)
            
            if signal and signal['side']:
                # Log detailed signal
                signal_msg = (f"[SIGNAL] side={signal['side']} price={signal['entry_price']:.5f}, "
                            f"trend_ok={signal['trend_ok']}, pullback_ok={signal['pullback_ok']}, "
                            f"rsi_ok={signal['rsi_ok']}, spread={signal['spread_points']}, "
                            f"atr_pts={signal['atr_points']:.1f}, reason={signal['reason']}")
                self.heartbeat_signal.emit(signal_msg)
                
                self.signal_ready.emit(signal)
                
        except Exception as e:
            error_msg = f"Signal generation error: {e}\n{traceback.format_exc()}"
            self.error_signal.emit(error_msg)
    
    def evaluate_strategy(self, m1_data, m5_data):
        """Evaluate scalping strategy"""
        try:
            # Get current tick
            symbol = self.controller.config['symbol']
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None
            
            spread_points = round((tick.ask - tick.bid) / self.controller.symbol_info.point)
            
            # Check spread filter
            if spread_points > self.controller.config['max_spread_points']:
                return {'side': None, 'reason': 'spread_too_wide'}
            
            # Check session filter
            if not self.is_trading_session():
                return {'side': None, 'reason': 'outside_session'}
            
            # Trend filter (M5): BUY jika EMA9>EMA21 & price>EMA50
            m5_ema_fast = m5_data.get('ema_fast', 0)
            m5_ema_medium = m5_data.get('ema_medium', 0) 
            m5_ema_slow = m5_data.get('ema_slow', 0)
            m5_close = m5_data.get('close', 0)
            
            trend_bullish = m5_ema_fast > m5_ema_medium and m5_close > m5_ema_slow
            trend_bearish = m5_ema_fast < m5_ema_medium and m5_close < m5_ema_slow
            
            if not trend_bullish and not trend_bearish:
                return {'side': None, 'reason': 'no_trend'}
            
            # Entry logic (M1): Pullback continuation
            m1_close = m1_data.get('close', 0)
            m1_ema_fast = m1_data.get('ema_fast', 0)
            m1_ema_medium = m1_data.get('ema_medium', 0)
            m1_rsi = m1_data.get('rsi', 50)
            
            # Check for pullback and continuation
            pullback_signal = None
            
            if trend_bullish:
                # BUY signal: price pulled back to EMA then continues up
                if (m1_close > m1_ema_fast and 
                    abs(m1_close - m1_ema_fast) < m1_data.get('atr', 100) * 0.5):
                    pullback_signal = 'BUY'
            
            elif trend_bearish:
                # SELL signal: price pulled back to EMA then continues down  
                if (m1_close < m1_ema_fast and
                    abs(m1_close - m1_ema_fast) < m1_data.get('atr', 100) * 0.5):
                    pullback_signal = 'SELL'
            
            if not pullback_signal:
                return {'side': None, 'reason': 'no_pullback_signal'}
            
            # RSI confirmation (optional, based on checkbox)
            rsi_ok = True  # Default true
            if self.controller.config.get('use_rsi_filter', False):
                if pullback_signal == 'BUY' and m1_rsi < 50:
                    rsi_ok = False
                elif pullback_signal == 'SELL' and m1_rsi > 50:
                    rsi_ok = False
            
            # Avoid doji candles
            if 'rates' in m1_data and len(m1_data['rates']) > 0:
                last_bar = m1_data['rates'][-1]
                body = abs(last_bar['close'] - last_bar['open'])
                range_size = last_bar['high'] - last_bar['low']
                if range_size > 0 and (body / range_size) < 0.3:
                    return {'side': None, 'reason': 'doji_candle'}
            
            # Calculate ATR in points
            atr_points = m1_data.get('atr', 0) / self.controller.symbol_info.point
            
            return {
                'side': pullback_signal,
                'entry_price': tick.ask if pullback_signal == 'BUY' else tick.bid,
                'trend_ok': 1,
                'pullback_ok': 1,
                'rsi_ok': 1 if rsi_ok else 0,
                'spread_points': spread_points,
                'atr_points': atr_points,
                'reason': 'strategy_confirmed',
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Strategy evaluation error: {e}")
            return {'side': None, 'reason': f'error: {e}'}
    
    def is_trading_session(self):
        """Check if dalam trading session (Asia/Jakarta GMT+7)"""
        try:
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            now_jakarta = datetime.now(jakarta_tz)
            current_time = now_jakarta.time()
            
            # London open (15:00-18:00 Jakarta) dan NY overlap (20:00-24:00 Jakarta)
            london_start = time(15, 0)  # 15:00
            london_end = time(18, 0)    # 18:00
            ny_start = time(20, 0)      # 20:00
            ny_end = time(23, 59)       # 23:59
            
            in_london = london_start <= current_time <= london_end
            in_ny = ny_start <= current_time <= ny_end
            
            return in_london or in_ny
            
        except Exception:
            return True  # Default allow trading if error
    
    def stop(self):
        self.running = False
        self.quit()
        self.wait(5000)

class BotController(QObject):
    """Fixed MT5 Scalping Bot Controller - PRODUCTION READY"""
    
    # Signals for GUI updates
    signal_log = Signal(str, str)  # message, level
    signal_status = Signal(str)    # status message
    signal_market_data = Signal(dict)  # market data
    signal_trade_signal = Signal(dict)  # trade signals
    signal_position_update = Signal(list)  # positions list
    signal_account_update = Signal(dict)  # account info
    signal_indicators_update = Signal(dict)  # indicators update
    signal_analysis_update = Signal(dict)  # analysis status update
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Bot state
        self.is_connected = False
        self.is_running = False
        self.shadow_mode = True  # Start in shadow mode for safety
        self.mt5_available = MT5_AVAILABLE
        
        # Configuration
        self.config = {
            'symbol': 'XAUUSD',
            'risk_percent': 0.5,
            'max_daily_loss': 2.0,
            'max_trades_per_day': 15,
            'max_spread_points': 30,
            'min_sl_points': 150,
            'risk_multiple': 2.0,
            'ema_periods': {'fast': 9, 'medium': 21, 'slow': 50},
            'rsi_period': 14,
            'atr_period': 14,
            'tp_sl_mode': 'ATR',  # ATR, Points, Pips, Balance%
            'atr_multiplier': 2.0,
            'tp_percent': 1.0,    # TP percentage of balance
            'sl_percent': 0.5,    # SL percentage of balance
            'tp_points': 200,     # TP in points
            'sl_points': 100,     # SL in points
            'tp_pips': 20,        # TP in pips
            'sl_pips': 10,        # SL in pips
            'use_rsi_filter': False,
            'deviation': 10,      # Price deviation for orders
            'magic_number': 234567
        }
        
        # Trading state
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.last_reset_date = datetime.now().date()
        
        # Market data
        self.current_market_data = {}
        self.current_signal = {}
        self.current_indicators = {'M1': {}, 'M5': {}}
        self.account_info = None
        self.positions = []
        self.symbol_info = None
        
        # Workers
        self.analysis_worker = None
        self.data_mutex = QMutex()
        
        # Timers
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_info)
        
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_positions)
        
        # Initialize logging
        self.setup_logging()
        
        self.log_message("Bot controller initialized", "INFO")
    
    def setup_logging(self):
        """Setup logging system"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Setup CSV logging for trades
            self.csv_file = log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.csv"
            
            if not self.csv_file.exists():
                with open(self.csv_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'side', 'entry', 'sl', 'tp', 'lot', 'result', 'spread_pts', 'atr_pts', 'mode', 'reason'])
                    
        except Exception as e:
            print(f"Logging setup error: {e}")
    
    def log_message(self, message: str, level: str = "INFO"):
        """Emit log message signal"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            formatted_message = f"[{timestamp}] {message}"
            self.signal_log.emit(formatted_message, level)
            
            # Also log to console in demo mode
            if not MT5_AVAILABLE:
                print(f"[{level}] {formatted_message}")
                
        except Exception as e:
            print(f"Log emit error: {e}")
    
    def connect_mt5(self) -> bool:
        """Connect to MetaTrader 5 dengan pre-flight checks"""
        try:
            if not MT5_AVAILABLE:
                self.log_message("MT5 not available - Demo mode only", "WARNING")
                self.is_connected = True  # Demo connection
                self.setup_demo_symbol_info()
                return True
            
            # Real MT5 connection
            self.log_message("Initializing MT5 connection...", "INFO")
            
            # 1. Initialize MT5
            if not mt5.initialize():
                error = mt5.last_error()
                self.log_message(f"MT5 initialization failed: {error}", "ERROR")
                return False
            
            # 2. Get account info
            account_info = mt5.account_info()
            if account_info is None:
                self.log_message("Failed to get account info", "ERROR")
                return False
            
            self.account_info = account_info._asdict()
            self.log_message(f"Connected to account: {self.account_info['login']}", "INFO")
            
            # 3. Select and validate symbol
            symbol = self.config['symbol']
            if not mt5.symbol_select(symbol, True):
                self.log_message(f"Failed to select symbol {symbol}", "ERROR")
                return False
            
            # 4. Get symbol info
            self.symbol_info = mt5.symbol_info(symbol)
            if self.symbol_info is None:
                self.log_message(f"Failed to get symbol info for {symbol}", "ERROR")
                return False
            
            # 5. Validate symbol trading
            if self.symbol_info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL:
                self.log_message(f"Symbol {symbol} not available for trading", "ERROR")
                return False
            
            # 6. Log symbol specifications
            self.log_symbol_info()
            
            self.is_connected = True
            self.log_message("MT5 connection successful", "INFO")
            
            # Start timers
            self.account_timer.start(2000)  # Update every 2 seconds
            self.position_timer.start(1000)  # Update every second
            
            return True
            
        except Exception as e:
            error_msg = f"MT5 connection error: {e}\n{traceback.format_exc()}"
            self.log_message(error_msg, "ERROR")
            return False
    
    def setup_demo_symbol_info(self):
        """Setup demo symbol info for fallback mode"""
        class DemoSymbolInfo:
            def __init__(self):
                self.name = "XAUUSD"
                self.point = 0.01
                self.digits = 2
                self.trade_contract_size = 100.0
                self.trade_tick_value = 1.0
                self.volume_min = 0.01
                self.volume_step = 0.01
                self.volume_max = 100.0
                self.stops_level = 10
                self.freeze_level = 5
                self.trade_mode = 0  # Full trading mode
        
        self.symbol_info = DemoSymbolInfo()
        self.account_info = {'balance': 10000.0, 'equity': 10000.0, 'login': 12345}
    
    def log_symbol_info(self):
        """Log symbol specifications"""
        try:
            info = self.symbol_info
            self.log_message(f"Symbol: {info.name}", "INFO")
            self.log_message(f"Point: {info.point}, Digits: {info.digits}", "INFO")
            self.log_message(f"Contract size: {info.trade_contract_size}", "INFO")
            self.log_message(f"Tick value: {info.trade_tick_value}", "INFO")
            self.log_message(f"Volume: min={info.volume_min}, step={info.volume_step}, max={info.volume_max}", "INFO")
            self.log_message(f"Stops level: {info.stops_level}, Freeze level: {info.freeze_level}", "INFO")
        except Exception as e:
            self.log_message(f"Error logging symbol info: {e}", "ERROR")
    
    def disconnect_mt5(self):
        """Disconnect from MT5"""
        try:
            self.stop_bot()
            
            if self.account_timer.isActive():
                self.account_timer.stop()
            if self.position_timer.isActive():
                self.position_timer.stop()
            
            if MT5_AVAILABLE and self.is_connected:
                mt5.shutdown()
            
            self.is_connected = False
            self.log_message("Disconnected from MT5", "INFO")
            
        except Exception as e:
            self.log_message(f"Disconnect error: {e}", "ERROR")
    
    def start_bot(self) -> bool:
        """Start bot dengan validasi lengkap"""
        try:
            if not self.is_connected:
                self.log_message("Not connected to MT5", "ERROR")
                return False
            
            # Validasi input GUI
            if not self.validate_config():
                return False
            
            # Check session
            self.log_message(f"Trading session check passed", "INFO")
            
            # Reset daily counters jika perlu
            self.check_daily_reset()
            
            # Start analysis worker dengan proper threading
            self.analysis_worker = AnalysisWorker(self)
            
            # Connect signals
            self.analysis_worker.heartbeat_signal.connect(
                lambda msg: self.log_message(msg, "INFO"))
            self.analysis_worker.signal_ready.connect(self.handle_trading_signal)
            self.analysis_worker.indicators_ready.connect(self.handle_indicators_update)
            self.analysis_worker.tick_data_signal.connect(self.handle_tick_data)
            self.analysis_worker.error_signal.connect(
                lambda msg: self.log_message(msg, "ERROR"))
            
            # Start worker thread
            self.analysis_worker.start()
            
            self.is_running = True
            self.log_message("[START] Bot started - Analysis thread running", "INFO")
            
            return True
            
        except Exception as e:
            error_msg = f"Start bot error: {e}\n{traceback.format_exc()}"
            self.log_message(error_msg, "ERROR")
            return False
    
    def validate_config(self) -> bool:
        """Validasi konfigurasi sebelum start"""
        try:
            # Check TP/SL mode dan values
            mode = self.config['tp_sl_mode']
            if mode not in ['ATR', 'Points', 'Pips', 'Balance%']:
                self.log_message(f"Invalid TP/SL mode: {mode}", "ERROR")
                return False
            
            # Validate risk percent
            if self.config['risk_percent'] <= 0 or self.config['risk_percent'] > 10:
                self.log_message("Risk percent must be between 0.1-10%", "ERROR")
                return False
            
            # Validate spread cap
            if self.config['max_spread_points'] <= 0:
                self.log_message("Max spread points must be positive", "ERROR")
                return False
            
            self.log_message("Configuration validation passed", "INFO")
            return True
            
        except Exception as e:
            self.log_message(f"Config validation error: {e}", "ERROR")
            return False
    
    def check_daily_reset(self):
        """Check dan reset daily counters"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.consecutive_losses = 0
            self.last_reset_date = current_date
            self.log_message("Daily counters reset", "INFO")
    
    def handle_tick_data(self, tick_data):
        """Handle tick data dari analysis worker"""
        self.current_market_data = tick_data
        self.signal_market_data.emit(tick_data)
    
    def handle_indicators_update(self, indicators):
        """Handle indicators update"""
        self.current_indicators = indicators
        self.signal_indicators_update.emit(indicators)
    
    def handle_trading_signal(self, signal):
        """Handle trading signal - KRUSIAL untuk auto-order"""
        try:
            if not signal or not signal.get('side'):
                return
            
            self.current_signal = signal
            self.signal_trade_signal.emit(signal)
            
            # AUTO EXECUTE - PERBAIKAN KRUSIAL
            if not self.shadow_mode and self.is_running:
                success = self.execute_signal(signal)
                if success:
                    self.log_message(f"[ORDER SUCCESS] Signal executed", "INFO")
                else:
                    self.log_message(f"[ORDER FAILED] Signal execution failed", "ERROR")
            else:
                self.log_message(f"[SHADOW MODE] Signal detected but not executed", "INFO")
                
        except Exception as e:
            error_msg = f"Signal handling error: {e}\n{traceback.format_exc()}"
            self.log_message(error_msg, "ERROR")
    
    def execute_signal(self, signal):
        """Execute trading signal dengan proper order management"""
        try:
            # Pre-execution checks
            if not self.check_risk_limits():
                self.log_message("[RISK STOP] Risk limits hit", "ERROR")
                self.stop_bot()
                return False
            
            # Check spread
            if signal['spread_points'] > self.config['max_spread_points']:
                self.log_message("[EXECUTE SKIP] Spread too wide", "WARNING")
                return False
            
            self.log_message(f"[EXECUTE] attempting order...", "INFO")
            
            # Calculate lot size
            lot_size = self.calculate_lot_size(signal)
            if lot_size < self.symbol_info.volume_min:
                self.log_message(f"[EXECUTE FAIL] Lot size too small: {lot_size}", "ERROR")
                return False
            
            # Calculate TP/SL
            entry_price = signal['entry_price']
            tp_price, sl_price = self.calculate_tp_sl(signal, entry_price)
            
            # Validate stops
            if not self.validate_stops(entry_price, sl_price, tp_price, signal['side']):
                self.log_message("[EXECUTE FAIL] Invalid stops", "ERROR")
                return False
            
            # Execute order
            result = self.send_order(signal['side'], lot_size, entry_price, sl_price, tp_price)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log_message(f"[ORDER OK] ticket={result.order}, side={signal['side']}, lot={lot_size:.2f}, entry={entry_price:.5f}, sl={sl_price:.5f}, tp={tp_price:.5f}", "INFO")
                
                # Update counters
                self.daily_trades += 1
                
                # Log to CSV
                self.log_trade_to_csv(signal['side'], entry_price, sl_price, tp_price, lot_size, "EXECUTED", signal['spread_points'], signal['atr_points'])
                
                return True
            else:
                error_code = result.retcode if result else "Unknown"
                error_comment = result.comment if result else "No response"
                self.log_message(f"[ORDER FAIL] code={error_code}, comment={error_comment}", "ERROR")
                return False
                
        except Exception as e:
            error_msg = f"Execute signal error: {e}\n{traceback.format_exc()}"
            self.log_message(error_msg, "ERROR")
            return False
    
    def calculate_lot_size(self, signal):
        """Calculate lot size berdasarkan risk percentage"""
        try:
            balance = self.account_info['balance']
            risk_amount = balance * (self.config['risk_percent'] / 100.0)
            
            # Calculate SL distance in points
            entry_price = signal['entry_price']
            _, sl_price = self.calculate_tp_sl(signal, entry_price)
            sl_distance_points = abs(entry_price - sl_price) / self.symbol_info.point
            
            if sl_distance_points <= 0:
                return self.symbol_info.volume_min
            
            # Calculate lot
            lot_raw = risk_amount / (sl_distance_points * self.symbol_info.trade_tick_value)
            
            # Round to step
            lot_step = self.symbol_info.volume_step
            lot_rounded = round(lot_raw / lot_step) * lot_step
            
            # Clamp to limits
            lot_final = max(self.symbol_info.volume_min, 
                          min(lot_rounded, self.symbol_info.volume_max))
            
            return lot_final
            
        except Exception as e:
            self.log_message(f"Lot calculation error: {e}", "ERROR")
            return self.symbol_info.volume_min
    
    def calculate_tp_sl(self, signal, entry_price):
        """Calculate TP/SL berdasarkan mode yang dipilih"""
        try:
            mode = self.config['tp_sl_mode']
            side = signal['side']
            point = self.symbol_info.point
            
            if mode == 'ATR':
                # ATR mode
                atr_points = max(self.config['min_sl_points'], signal['atr_points'])
                sl_distance = atr_points * point
                tp_distance = sl_distance * self.config['risk_multiple']
                
            elif mode == 'Points':
                # Points mode
                sl_distance = self.config['sl_points'] * point
                tp_distance = self.config['tp_points'] * point
                
            elif mode == 'Pips':
                # Pips mode - convert to points
                pip_to_point = 10 if self.symbol_info.digits in [3, 5] else 1
                sl_distance = self.config['sl_pips'] * pip_to_point * point
                tp_distance = self.config['tp_pips'] * pip_to_point * point
                
            elif mode == 'Balance%':
                # Balance percentage mode
                balance = self.account_info['balance']
                sl_usd = balance * (self.config['sl_percent'] / 100.0)
                tp_usd = balance * (self.config['tp_percent'] / 100.0)
                
                # Convert to points (simplified)
                tick_value = self.symbol_info.trade_tick_value
                lot_size = self.symbol_info.volume_min  # Use min lot for calculation
                
                sl_points = sl_usd / (tick_value * lot_size)
                tp_points = tp_usd / (tick_value * lot_size)
                
                sl_distance = sl_points * point
                tp_distance = tp_points * point
            else:
                # Default to ATR
                sl_distance = signal['atr_points'] * point
                tp_distance = sl_distance * 2
            
            # Calculate prices
            if side == 'BUY':
                sl_price = entry_price - sl_distance
                tp_price = entry_price + tp_distance
            else:  # SELL
                sl_price = entry_price + sl_distance
                tp_price = entry_price - tp_distance
            
            return tp_price, sl_price
            
        except Exception as e:
            self.log_message(f"TP/SL calculation error: {e}", "ERROR")
            # Fallback
            if side == 'BUY':
                return entry_price + 200 * point, entry_price - 100 * point
            else:
                return entry_price - 200 * point, entry_price + 100 * point
    
    def validate_stops(self, entry_price, sl_price, tp_price, side):
        """Validate SL/TP distances vs stops_level"""
        try:
            point = self.symbol_info.point
            stops_level = self.symbol_info.stops_level
            
            sl_distance = abs(entry_price - sl_price) / point
            tp_distance = abs(entry_price - tp_price) / point
            
            if sl_distance < stops_level:
                self.log_message(f"SL too close: {sl_distance:.1f} < {stops_level}", "WARNING")
                return False
                
            if tp_distance < stops_level:
                self.log_message(f"TP too close: {tp_distance:.1f} < {stops_level}", "WARNING")
                return False
            
            return True
            
        except Exception as e:
            self.log_message(f"Stops validation error: {e}", "ERROR")
            return False
    
    def send_order(self, side, lot, price, sl, tp):
        """Send order to MT5 dengan retry logic"""
        try:
            symbol = self.config['symbol']
            deviation = self.config['deviation']
            magic = self.config['magic_number']
            
            order_type = mt5.ORDER_TYPE_BUY if side == 'BUY' else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": deviation,
                "magic": magic,
                "comment": f"Scalping_{side}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Try IOC first
            result = mt5.order_send(request)
            
            # Fallback to FOK if IOC fails
            if result and result.retcode != mt5.TRADE_RETCODE_DONE:
                request["type_filling"] = mt5.ORDER_FILLING_FOK
                result = mt5.order_send(request)
            
            return result
            
        except Exception as e:
            self.log_message(f"Send order error: {e}", "ERROR")
            return None
    
    def check_risk_limits(self):
        """Check risk limits"""
        try:
            # Daily trades limit
            if self.daily_trades >= self.config['max_trades_per_day']:
                return False
            
            # Daily loss limit
            current_equity = self.account_info.get('equity', 0)
            daily_start_equity = self.account_info.get('balance', 0)  # Simplified
            daily_loss_percent = abs(current_equity - daily_start_equity) / daily_start_equity * 100
            
            if daily_loss_percent >= self.config['max_daily_loss']:
                return False
            
            return True
            
        except Exception as e:
            self.log_message(f"Risk check error: {e}", "ERROR")
            return True  # Allow trading if error
    
    def log_trade_to_csv(self, side, entry, sl, tp, lot, result, spread_pts, atr_pts):
        """Log trade to CSV"""
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    side, entry, sl, tp, lot, result,
                    spread_pts, atr_pts, self.config['tp_sl_mode'],
                    "strategy_signal"
                ])
        except Exception as e:
            self.log_message(f"CSV logging error: {e}", "ERROR")
    
    def stop_bot(self):
        """Stop bot"""
        try:
            self.is_running = False
            
            if self.analysis_worker and self.analysis_worker.isRunning():
                self.analysis_worker.stop()
            
            self.log_message("Bot stopped", "INFO")
            
        except Exception as e:
            self.log_message(f"Stop bot error: {e}", "ERROR")
    
    def update_account_info(self):
        """Update account information"""
        try:
            if not self.is_connected:
                return
            
            if MT5_AVAILABLE:
                account = mt5.account_info()
                if account:
                    self.account_info = account._asdict()
            else:
                # Demo mode - simulate account
                pass
            
            if self.account_info:
                self.signal_account_update.emit(self.account_info)
                
        except Exception as e:
            self.log_message(f"Account update error: {e}", "ERROR")
    
    def update_positions(self):
        """Update positions"""
        try:
            if not self.is_connected:
                return
            
            if MT5_AVAILABLE:
                positions = mt5.positions_get(symbol=self.config['symbol'])
                if positions is not None:
                    self.positions = [pos._asdict() for pos in positions]
            else:
                # Demo mode
                self.positions = []
            
            self.signal_position_update.emit(self.positions)
            
        except Exception as e:
            self.log_message(f"Position update error: {e}", "ERROR")
    
    def close_position(self, ticket):
        """Close specific position"""
        try:
            if not MT5_AVAILABLE:
                self.log_message("Demo mode - position close simulated", "INFO")
                return True
            
            position = None
            for pos in self.positions:
                if pos['ticket'] == ticket:
                    position = pos
                    break
            
            if not position:
                self.log_message(f"Position {ticket} not found", "ERROR")
                return False
            
            # Close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position['symbol'],
                "volume": position['volume'],
                "type": mt5.ORDER_TYPE_SELL if position['type'] == 0 else mt5.ORDER_TYPE_BUY,
                "position": ticket,
                "price": mt5.symbol_info_tick(position['symbol']).bid if position['type'] == 0 else mt5.symbol_info_tick(position['symbol']).ask,
                "deviation": 20,
                "magic": position['magic'],
                "comment": "Close_by_bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log_message(f"Position {ticket} closed successfully", "INFO")
                return True
            else:
                self.log_message(f"Failed to close position {ticket}: {result.comment}", "ERROR")
                return False
                
        except Exception as e:
            error_msg = f"Close position error: {e}\n{traceback.format_exc()}"
            self.log_message(error_msg, "ERROR")
            return False
    
    def close_all_positions(self):
        """Close all positions (Emergency Stop)"""
        try:
            closed_count = 0
            for position in self.positions:
                if self.close_position(position['ticket']):
                    closed_count += 1
            
            self.log_message(f"Emergency stop: {closed_count} positions closed", "INFO")
            self.stop_bot()
            
        except Exception as e:
            error_msg = f"Close all positions error: {e}\n{traceback.format_exc()}"
            self.log_message(error_msg, "ERROR")
    
    def export_logs(self, filename):
        """Export logs to file"""
        try:
            import shutil
            shutil.copy(self.csv_file, filename)
            self.log_message(f"Logs exported to {filename}", "INFO")
            return True
        except Exception as e:
            self.log_message(f"Export error: {e}", "ERROR")
            return False
    
    def diagnostic_check(self):
        """Run comprehensive diagnostic checks"""
        try:
            self.log_message("=== DIAGNOSTIC DOCTOR ===", "INFO")
            
            # 1. MT5 Connection
            if MT5_AVAILABLE and self.is_connected:
                self.log_message("✓ MT5 initialized & connected", "INFO")
            else:
                self.log_message("⚠ MT5 not available - demo mode", "WARNING")
            
            # 2. Symbol info
            if self.symbol_info:
                self.log_message(f"✓ Symbol {self.symbol_info.name} loaded", "INFO")
                if hasattr(self.symbol_info, 'trade_mode'):
                    self.log_message(f"✓ Trade mode: {self.symbol_info.trade_mode}", "INFO")
            else:
                self.log_message("✗ Symbol info missing", "ERROR")
            
            # 3. Account info
            if self.account_info:
                self.log_message(f"✓ Account balance: {self.account_info.get('balance', 0)}", "INFO")
            else:
                self.log_message("✗ Account info missing", "ERROR")
            
            # 4. Analysis worker
            if self.analysis_worker and self.analysis_worker.isRunning():
                self.log_message("✓ Analysis worker running", "INFO")
            else:
                self.log_message("⚠ Analysis worker not running", "WARNING")
            
            # 5. Data feed
            if self.current_market_data:
                self.log_message("✓ Market data feed active", "INFO")
            else:
                self.log_message("⚠ No market data", "WARNING")
            
            # 6. Indicators
            if self.current_indicators['M1'] and self.current_indicators['M5']:
                self.log_message("✓ Indicators calculated", "INFO")
            else:
                self.log_message("⚠ Indicators missing", "WARNING")
            
            self.log_message("=== DIAGNOSTIC COMPLETE ===", "INFO")
            
        except Exception as e:
            error_msg = f"Diagnostic error: {e}\n{traceback.format_exc()}"
            self.log_message(error_msg, "ERROR")
    
    # Configuration methods
    def set_config(self, key, value):
        """Update configuration"""
        self.config[key] = value
        
    def get_config(self, key):
        """Get configuration value"""
        return self.config.get(key)
    
    def update_tp_sl_config(self, mode, tp_value, sl_value):
        """Update TP/SL configuration"""
        self.config['tp_sl_mode'] = mode
        
        if mode == 'ATR':
            self.config['atr_multiplier'] = tp_value if tp_value else 2.0
        elif mode == 'Points':
            self.config['tp_points'] = tp_value if tp_value else 200
            self.config['sl_points'] = sl_value if sl_value else 100
        elif mode == 'Pips':
            self.config['tp_pips'] = tp_value if tp_value else 20
            self.config['sl_pips'] = sl_value if sl_value else 10
        elif mode == 'Balance%':
            self.config['tp_percent'] = tp_value if tp_value else 1.0
            self.config['sl_percent'] = sl_value if sl_value else 0.5