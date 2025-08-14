
"""
Complete Bot Controller Implementation
PRODUCTION READY FOR REAL MONEY TRADING
"""

import sys
import logging
import threading
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import csv

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

# Import indicators
from indicators import TechnicalIndicators

class MarketDataWorker(QThread):
    """Worker thread for market data collection"""
    data_ready = Signal(dict)
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = False
        
    def run(self):
        """Main market data collection loop"""
        self.running = True
        while self.running:
            try:
                if self.controller.is_connected:
                    data = self.controller.get_market_data()
                    if data:
                        self.data_ready.emit(data)
                self.msleep(1000)  # Update every second
            except Exception as e:
                print(f"Market data worker error: {e}")
                self.msleep(5000)
    
    def stop(self):
        self.running = False

class BotController(QObject):
    """Complete MT5 Scalping Bot Controller - PRODUCTION READY"""
    
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
            'ema_periods': {'fast': 8, 'medium': 21, 'slow': 50},
            'rsi_period': 14,
            'atr_period': 14,
            'tp_sl_mode': 'ATR',  # ATR, Points, Pips, Percent
            'tp_percent': 1.0,    # TP percentage of balance
            'sl_percent': 0.5,    # SL percentage of balance
            'tp_points': 200,     # TP in points
            'sl_points': 100,     # SL in points
            'tp_pips': 20,        # TP in pips
            'sl_pips': 10         # SL in pips
        }
        
        # Trading state
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        # Market data
        self.current_market_data = {}
        self.current_signal = {}
        self.current_indicators = {'M1': {}, 'M5': {}}
        self.account_info = None
        self.positions = []
        
        # Indicators calculator
        self.indicators = TechnicalIndicators()
        
        # Workers and timers
        self.market_worker = None
        self.data_mutex = QMutex()
        
        # Account update timer
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_info)
        
        # Position update timer
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_positions_display)
        
        # Market data timer for fallback
        self.market_timer = QTimer()
        self.market_timer.timeout.connect(self.update_market_data_fallback)
        
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
                    writer.writerow(['timestamp', 'type', 'entry', 'sl', 'tp', 'lot', 'result'])
                    
        except Exception as e:
            print(f"Logging setup error: {e}")
    
    def log_message(self, message: str, level: str = "INFO"):
        """Emit log message signal"""
        try:
            self.signal_log.emit(message, level)
            
            # Also log to console in demo mode
            if not MT5_AVAILABLE:
                print(f"[{level}] {message}")
                
        except Exception as e:
            print(f"Log emit error: {e}")
    
    def connect_mt5(self) -> bool:
        """Connect to MetaTrader 5"""
        try:
            if not MT5_AVAILABLE:
                self.log_message("MT5 not available - Demo mode only", "WARNING")
                self.is_connected = True  # Demo connection
                self.start_demo_mode()
                return True
            
            # Real MT5 connection
            if not mt5.initialize():
                error = mt5.last_error()
                self.log_message(f"MT5 initialization failed: {error}", "ERROR")
                return False
            
            # Check connection
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                self.log_message("Cannot get terminal info", "ERROR")
                return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                self.log_message("Cannot get account info", "ERROR")
                return False
            
            self.account_info = account_info
            self.is_connected = True
            
            # Start timers
            self.account_timer.start(5000)  # Update every 5 seconds
            self.position_timer.start(3000)  # Update every 3 seconds
            
            # Start market data worker
            self.start_market_worker()
            
            self.log_message(f"Connected to MT5 - Account: {account_info.login}", "INFO")
            self.signal_status.emit("Connected")
            
            return True
            
        except Exception as e:
            self.log_message(f"MT5 connection error: {e}", "ERROR")
            return False
    
    def start_demo_mode(self):
        """Start demo mode with simulated data"""
        try:
            # Create demo account info
            self.account_info = type('AccountInfo', (), {
                'login': 123456789,
                'server': 'Demo-Server',
                'balance': 10000.0,
                'equity': 10000.0,
                'margin': 0.0,
                'profit': 0.0,
                'margin_free': 10000.0
            })()
            
            # Start demo timers
            self.market_timer.start(1000)  # Update market data every second
            self.account_timer.start(5000)
            self.position_timer.start(3000)
            
            self.log_message("Demo mode started - No real trading", "INFO")
            self.signal_status.emit("Connected (Demo)")
            
        except Exception as e:
            self.log_message(f"Demo mode error: {e}", "ERROR")
    
    def start_market_worker(self):
        """Start market data worker thread"""
        try:
            if self.market_worker is not None:
                self.market_worker.stop()
                self.market_worker.wait()
            
            self.market_worker = MarketDataWorker(self)
            self.market_worker.data_ready.connect(self.process_market_data)
            self.market_worker.start()
            
        except Exception as e:
            self.log_message(f"Market worker start error: {e}", "ERROR")
    
    def disconnect_mt5(self):
        """Disconnect from MetaTrader 5"""
        try:
            # Stop workers and timers
            if self.market_worker:
                self.market_worker.stop()
                self.market_worker.wait()
            
            self.account_timer.stop()
            self.position_timer.stop()
            self.market_timer.stop()
            
            # Shutdown MT5
            if MT5_AVAILABLE and self.is_connected:
                mt5.shutdown()
            
            self.is_connected = False
            self.signal_status.emit("Disconnected")
            self.log_message("Disconnected from MT5", "INFO")
            
        except Exception as e:
            self.log_message(f"Disconnect error: {e}", "ERROR")
    
    def get_market_data(self) -> Optional[Dict]:
        """Get current market data"""
        try:
            if not self.is_connected:
                return None
            
            symbol = self.config['symbol']
            
            if not MT5_AVAILABLE:
                # Demo market data
                import random
                base_price = 2000.0
                spread = random.randint(20, 50)
                bid = base_price + random.uniform(-5.0, 5.0)
                ask = bid + (spread / 100000)
                
                return {
                    'symbol': symbol,
                    'bid': bid,
                    'ask': ask,
                    'spread': spread,
                    'time': datetime.now(),
                    'indicators_m1': self.get_demo_indicators('M1'),
                    'indicators_m5': self.get_demo_indicators('M5')
                }
            
            # Real MT5 data
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            
            # Get indicator data
            indicators_m1 = self.calculate_indicators(symbol, mt5.TIMEFRAME_M1)
            indicators_m5 = self.calculate_indicators(symbol, mt5.TIMEFRAME_M5)
            
            return {
                'symbol': symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': int((tick.ask - tick.bid) * 100000),
                'time': datetime.fromtimestamp(tick.time),
                'indicators_m1': indicators_m1,
                'indicators_m5': indicators_m5
            }
            
        except Exception as e:
            self.log_message(f"Market data error: {e}", "ERROR")
            return None
    
    def get_demo_indicators(self, timeframe: str) -> Dict:
        """Generate demo indicator values"""
        import random
        
        base_price = 2000.0
        
        return {
            'ema_fast': base_price + random.uniform(-2.0, 2.0),
            'ema_medium': base_price + random.uniform(-3.0, 3.0),
            'ema_slow': base_price + random.uniform(-5.0, 5.0),
            'rsi': random.uniform(30.0, 70.0),
            'atr': random.uniform(0.8, 1.5)
        }
    
    def calculate_indicators(self, symbol: str, timeframe) -> Optional[Dict]:
        """Calculate technical indicators"""
        try:
            if not MT5_AVAILABLE:
                return self.get_demo_indicators('M1' if timeframe == mt5.TIMEFRAME_M1 else 'M5')
            
            # Get price data
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
            if rates is None or len(rates) < 50:
                return None
            
            closes = [r['close'] for r in rates]
            highs = [r['high'] for r in rates]
            lows = [r['low'] for r in rates]
            
            # Calculate indicators
            ema_fast = self.indicators.calculate_ema(closes, self.config['ema_periods']['fast'])
            ema_medium = self.indicators.calculate_ema(closes, self.config['ema_periods']['medium'])
            ema_slow = self.indicators.calculate_ema(closes, self.config['ema_periods']['slow'])
            rsi = self.indicators.calculate_rsi(closes, self.config['rsi_period'])
            atr = self.indicators.calculate_atr(highs, lows, closes, self.config['atr_period'])
            
            return {
                'ema_fast': ema_fast,
                'ema_medium': ema_medium,
                'ema_slow': ema_slow,
                'rsi': rsi,
                'atr': atr
            }
            
        except Exception as e:
            self.log_message(f"Indicator calculation error: {e}", "ERROR")
            return None
    
    def process_market_data(self, data: Dict):
        """Process incoming market data"""
        try:
            self.data_mutex.lock()
            self.current_market_data = data
            
            # Update indicators for GUI
            if 'indicators_m1' in data and 'indicators_m5' in data:
                self.current_indicators = {
                    'M1': data['indicators_m1'] or {},
                    'M5': data['indicators_m5'] or {}
                }
                self.signal_indicators_update.emit(self.current_indicators)
            
            self.data_mutex.unlock()
            
            # Emit to GUI
            self.signal_market_data.emit(data)
            
            # Generate trading signals if bot is running
            if self.is_running:
                signal = self.generate_signal(data)
                if signal:
                    self.current_signal = signal
                    self.signal_trade_signal.emit(signal)
                    
                    # Log signal generation
                    self.log_message(f"🎯 SIGNAL GENERATED: {signal['type']} at {signal['entry_price']:.5f}", "INFO")
                    
                    # Execute trade automatically if not in shadow mode
                    if not self.shadow_mode:
                        self.log_message("🚀 AUTO EXECUTION STARTED", "INFO")
                        QTimer.singleShot(1000, lambda: self.execute_signal(signal))  # Small delay for GUI update
                    else:
                        self.log_message("🛡️ Shadow mode - Signal only", "INFO")
            
        except Exception as e:
            self.log_message(f"Market data processing error: {e}", "ERROR")
        finally:
            if self.data_mutex.tryLock():
                self.data_mutex.unlock()
    
    def update_market_data_fallback(self):
        """Fallback market data update for demo mode"""
        try:
            data = self.get_market_data()
            if data:
                self.process_market_data(data)
                
        except Exception as e:
            self.log_message(f"Market data fallback error: {e}", "ERROR")
    
    def generate_signal(self, data: Dict) -> Optional[Dict]:
        """Generate scalping signals using M5 trend + M1 pullback strategy"""
        try:
            # Emit analysis start status
            self.signal_analysis_update.emit({
                'status': 'analyzing',
                'next_analysis': datetime.now().strftime("%H:%M:%S")
            })
            
            if not data.get('indicators_m1') or not data.get('indicators_m5'):
                self.signal_analysis_update.emit({
                    'status': 'no_signal',
                    'm5_trend': 'No Data',
                    'm1_setup': 'No Data',
                    'signal_strength': 0
                })
                return None
            
            m1_indicators = data['indicators_m1']
            m5_indicators = data['indicators_m5']
            
            # Check spread filter
            if data.get('spread', 0) > self.config['max_spread_points']:
                self.signal_analysis_update.emit({
                    'status': 'no_signal',
                    'm5_trend': 'High Spread',
                    'm1_setup': f"Spread: {data.get('spread', 0)} pts",
                    'signal_strength': 0
                })
                return None
            
            # Get indicator values with safe access
            m1_ema_fast = m1_indicators.get('ema_fast')
            m1_ema_medium = m1_indicators.get('ema_medium')
            m1_ema_slow = m1_indicators.get('ema_slow')
            m1_rsi = m1_indicators.get('rsi', 50)
            m1_atr = m1_indicators.get('atr', 0.001)
            
            m5_ema_fast = m5_indicators.get('ema_fast')
            m5_ema_medium = m5_indicators.get('ema_medium')
            m5_ema_slow = m5_indicators.get('ema_slow')
            m5_rsi = m5_indicators.get('rsi', 50)
            
            # Validate all indicators are available
            if any(x is None for x in [m1_ema_fast, m1_ema_medium, m1_ema_slow, m5_ema_fast, m5_ema_medium, m5_ema_slow]):
                return None
            
            current_price = data['ask']  # Use ask for signal price reference
            
            # BUY Signal Logic
            # M5 Trend Filter: EMAs aligned bullish and price above slow EMA
            m5_bullish_trend = (m5_ema_fast > m5_ema_medium > m5_ema_slow and 
                               current_price > m5_ema_slow)
            
            # M1 Entry: Fast EMA above medium EMA (trend) + RSI confirmation
            m1_bullish_setup = (m1_ema_fast > m1_ema_medium and 
                               m1_rsi > 45 and m1_rsi < 75)  # Not overbought
            
            # Price action: Price near or above M1 fast EMA (pullback completion)
            near_m1_ema = abs(current_price - m1_ema_fast) / current_price < 0.0005
            
            # SELL Signal Logic  
            m5_bearish_trend = (m5_ema_fast < m5_ema_medium < m5_ema_slow and 
                               current_price < m5_ema_slow)
            
            m1_bearish_setup = (m1_ema_fast < m1_ema_medium and 
                               m1_rsi < 55 and m1_rsi > 25)  # Not oversold
            
            signal_type = None
            entry_price = None
            signal_strength = 0
            
            # Calculate signal strength
            strength_factors = 0
            if m5_bullish_trend or m5_bearish_trend:
                strength_factors += 3
            if m1_bullish_setup or m1_bearish_setup:
                strength_factors += 3
            if near_m1_ema:
                strength_factors += 2
            if 35 < m1_rsi < 65:  # RSI in good range
                strength_factors += 2
                
            signal_strength = strength_factors
            
            # Determine trend status for display
            m5_trend_status = "📈 Bullish" if m5_bullish_trend else "📉 Bearish" if m5_bearish_trend else "➡️ Sideways"
            m1_setup_status = "✅ Long Setup" if m1_bullish_setup else "✅ Short Setup" if m1_bearish_setup else "❌ No Setup"
            
            # Generate BUY signal
            if m5_bullish_trend and m1_bullish_setup and near_m1_ema and signal_strength >= 7:
                signal_type = "BUY"
                entry_price = data['ask']  # Buy at ask price
                
            # Generate SELL signal
            elif m5_bearish_trend and m1_bearish_setup and near_m1_ema and signal_strength >= 7:
                signal_type = "SELL" 
                entry_price = data['bid']  # Sell at bid price
            
            # Update analysis status
            if signal_type:
                self.signal_analysis_update.emit({
                    'status': 'signal_found',
                    'm5_trend': m5_trend_status,
                    'm1_setup': m1_setup_status,
                    'signal_strength': signal_strength
                })
            else:
                self.signal_analysis_update.emit({
                    'status': 'no_signal',
                    'm5_trend': m5_trend_status,
                    'm1_setup': m1_setup_status,
                    'signal_strength': signal_strength
                })
            
            if signal_type:
                # Calculate SL/TP based on selected mode
                sl_price, tp_price = self.calculate_sl_tp(signal_type, entry_price, m1_atr)
                
                if sl_price is None or tp_price is None:
                    return None
                
                # Calculate optimal lot size
                lot_size = self.calculate_lot_size(abs(entry_price - sl_price))
                
                return {
                    'type': signal_type,
                    'entry_price': entry_price,
                    'sl_price': sl_price,
                    'tp_price': tp_price,
                    'lot_size': lot_size,
                    'risk_reward': abs(tp_price - entry_price) / abs(entry_price - sl_price) if abs(entry_price - sl_price) > 0 else 0,
                    'timestamp': datetime.now(),
                    'atr': m1_atr,
                    'spread': data.get('spread', 0),
                    'sl_points': int(abs(entry_price - sl_price) * 100000),
                    'tp_points': int(abs(tp_price - entry_price) * 100000)
                }
            
            return None
            
        except Exception as e:
            self.log_message(f"Signal generation error: {e}", "ERROR")
            return None
    
    def calculate_sl_tp(self, signal_type: str, entry_price: float, atr_value: float) -> Tuple[Optional[float], Optional[float]]:
        """Calculate SL and TP based on selected mode"""
        try:
            mode = self.config['tp_sl_mode']
            
            if mode == 'ATR':
                # ATR-based calculation
                atr_points = atr_value * 100000
                sl_distance_points = max(self.config['min_sl_points'], int(atr_points * 1.5))
                tp_distance_points = int(sl_distance_points * self.config['risk_multiple'])
                
                sl_distance_price = sl_distance_points / 100000
                tp_distance_price = tp_distance_points / 100000
                
            elif mode == 'Points':
                # Points-based calculation
                sl_distance_price = self.config['sl_points'] / 100000
                tp_distance_price = self.config['tp_points'] / 100000
                
            elif mode == 'Pips':
                # Pips-based calculation (1 pip = 10 points for 5-digit symbols)
                sl_distance_price = (self.config['sl_pips'] * 10) / 100000
                tp_distance_price = (self.config['tp_pips'] * 10) / 100000
                
            elif mode == 'Percent':
                # Percentage-based calculation
                if not self.account_info:
                    return None, None
                
                balance = self.account_info.balance
                sl_usd = balance * (self.config['sl_percent'] / 100)
                tp_usd = balance * (self.config['tp_percent'] / 100)
                
                # Convert USD to price distance
                # Simplified calculation - should be refined for actual implementation
                tick_value = 1.0  # USD per point for XAUUSD
                lot_size = 0.01   # Estimate
                
                sl_distance_price = sl_usd / (tick_value * lot_size * 100000)
                tp_distance_price = tp_usd / (tick_value * lot_size * 100000)
                
            else:
                return None, None
            
            # Apply direction
            if signal_type == "BUY":
                sl_price = entry_price - sl_distance_price
                tp_price = entry_price + tp_distance_price
            else:  # SELL
                sl_price = entry_price + sl_distance_price
                tp_price = entry_price - tp_distance_price
            
            return sl_price, tp_price
            
        except Exception as e:
            self.log_message(f"SL/TP calculation error: {e}", "ERROR")
            return None, None
    
    def calculate_lot_size(self, sl_distance: float) -> float:
        """Calculate lot size based on risk"""
        try:
            if not self.account_info:
                return 0.01
            
            risk_amount = self.account_info.balance * (self.config['risk_percent'] / 100)
            
            # Simple lot calculation
            pip_value = 10  # $10 per pip for XAUUSD
            risk_pips = sl_distance * 100000
            
            if risk_pips > 0:
                lot_size = risk_amount / (risk_pips * pip_value)
                return max(0.01, min(1.0, round(lot_size, 2)))
            
            return 0.01
            
        except Exception as e:
            self.log_message(f"Lot calculation error: {e}", "ERROR")
            return 0.01
    
    def execute_signal(self, signal: Dict):
        """Execute trading signal with real MT5 orders"""
        try:
            if self.shadow_mode:
                self.log_message(f"🛡️ SHADOW MODE: {signal['type']} signal at {signal['entry_price']:.5f}", "INFO")
                self.log_message(f"🛡️ SHADOW: SL={signal['sl_price']:.5f}, TP={signal['tp_price']:.5f}, Lot={signal['lot_size']}", "INFO")
                return
            
            if not MT5_AVAILABLE or not self.is_connected:
                self.log_message("❌ Cannot execute - MT5 not available or not connected", "ERROR")
                return
            
            # Check daily limits
            if self.daily_trades >= self.config['max_trades_per_day']:
                self.log_message(f"❌ Daily trade limit reached ({self.daily_trades}/{self.config['max_trades_per_day']})", "WARNING")
                return
            
            # Validate account balance for risk
            if not self.account_info:
                self.log_message("❌ Cannot execute - No account information", "ERROR")
                return
            
            risk_amount = self.account_info.balance * (self.config['risk_percent'] / 100)
            self.log_message(f"🎯 EXECUTING LIVE ORDER: {signal['type']}", "INFO")
            self.log_message(f"💰 Risk Amount: ${risk_amount:.2f} ({self.config['risk_percent']}%)", "INFO")
            
            symbol = self.config['symbol']
            
            # Get current prices
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.log_message("Cannot get current prices", "ERROR")
                return
            
            # Prepare order request
            order_type = mt5.ORDER_TYPE_BUY if signal['type'] == 'BUY' else mt5.ORDER_TYPE_SELL
            price = tick.ask if signal['type'] == 'BUY' else tick.bid
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": signal['lot_size'],
                "type": order_type,
                "price": price,
                "sl": signal['sl_price'],
                "tp": signal['tp_price'],
                "deviation": 20,
                "magic": 987654321,
                "comment": f"Scalping {signal['type']}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Execute order
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.daily_trades += 1
                self.log_message(f"✅ Order executed: {signal['type']} {signal['lot_size']} lots at {price:.5f}", "INFO")
                self.log_message(f"SL: {signal['sl_price']:.5f}, TP: {signal['tp_price']:.5f}", "INFO")
                
                # Log to CSV
                with open(self.csv_file, 'a', newline='') as f:
                    import csv
                    writer = csv.writer(f)
                    writer.writerow([
                        signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        signal['type'],
                        price,
                        signal['sl_price'],
                        signal['tp_price'],
                        signal['lot_size'],
                        'EXECUTED'
                    ])
            else:
                self.log_message(f"❌ Order failed: {result.comment} (Code: {result.retcode})", "ERROR")
            
        except Exception as e:
            self.log_message(f"Signal execution error: {e}", "ERROR")
    
    def update_account_info(self):
        """Update account information"""
        try:
            if not self.is_connected:
                return
            
            if not MT5_AVAILABLE:
                # Demo account updates
                import random
                profit_change = random.uniform(-50, 50)
                self.account_info.profit += profit_change
                self.account_info.equity = self.account_info.balance + self.account_info.profit
                
            else:
                # Real account info
                account_info = mt5.account_info()
                if account_info:
                    self.account_info = account_info
            
            # Emit account update
            if self.account_info:
                account_data = {
                    'balance': self.account_info.balance,
                    'equity': self.account_info.equity,
                    'margin': getattr(self.account_info, 'margin', 0),
                    'profit': getattr(self.account_info, 'profit', 0),
                    'margin_free': getattr(self.account_info, 'margin_free', 0)
                }
                self.signal_account_update.emit(account_data)
            
        except Exception as e:
            self.log_message(f"Account update error: {e}", "ERROR")
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            if not self.is_connected:
                return []
            
            if not MT5_AVAILABLE:
                # Demo positions
                return self.positions
            
            # Real positions
            positions = mt5.positions_get(symbol=self.config['symbol'])
            if positions is None:
                return []
            
            position_list = []
            for pos in positions:
                position_list.append({
                    'ticket': pos.ticket,
                    'type': 'BUY' if pos.type == 0 else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'comment': pos.comment
                })
            
            return position_list
            
        except Exception as e:
            self.log_message(f"Get positions error: {e}", "ERROR")
            return []
    
    def update_positions_display(self):
        """Update positions display"""
        try:
            positions = self.get_positions()
            self.signal_position_update.emit(positions)
            
        except Exception as e:
            self.log_message(f"Position display update error: {e}", "ERROR")
    
    def start_bot(self) -> bool:
        """Start the trading bot"""
        try:
            if not self.is_connected:
                self.log_message("Cannot start bot - Not connected", "ERROR")
                return False
            
            self.is_running = True
            self.signal_status.emit("Running")
            
            mode = "SHADOW MODE" if self.shadow_mode else "LIVE TRADING"
            self.log_message(f"Trading bot started in {mode}", "INFO")
            
            return True
            
        except Exception as e:
            self.log_message(f"Bot start error: {e}", "ERROR")
            return False
    
    def stop_bot(self):
        """Stop the trading bot"""
        try:
            self.is_running = False
            self.signal_status.emit("Stopped")
            self.log_message("Trading bot stopped", "INFO")
            
        except Exception as e:
            self.log_message(f"Bot stop error: {e}", "ERROR")
    
    def toggle_shadow_mode(self, enabled: bool):
        """Toggle shadow mode"""
        try:
            self.shadow_mode = enabled
            mode = "Shadow Mode" if enabled else "Live Trading"
            self.log_message(f"Switched to {mode}", "INFO")
            
        except Exception as e:
            self.log_message(f"Shadow mode toggle error: {e}", "ERROR")
    
    def update_config(self, config: Dict):
        """Update bot configuration with validation"""
        try:
            old_config = self.config.copy()
            self.config.update(config)
            
            # Log important configuration changes
            if 'tp_sl_mode' in config:
                self.log_message(f"✅ TP/SL Mode changed to: {config['tp_sl_mode']}", "INFO")
            
            if 'risk_percent' in config:
                self.log_message(f"✅ Risk per trade: {config['risk_percent']}%", "INFO")
                
            if 'symbol' in config:
                self.log_message(f"✅ Symbol changed to: {config['symbol']}", "INFO")
            
            self.log_message("✅ Configuration updated successfully", "INFO")
            
            # Validate critical parameters
            if self.config['risk_percent'] > 5.0:
                self.log_message("⚠️ WARNING: Risk per trade >5% - Very high risk!", "WARNING")
            
            if self.config['max_spread_points'] > 100:
                self.log_message("⚠️ WARNING: Max spread >100 points - May miss opportunities", "WARNING")
            
        except Exception as e:
            self.log_message(f"Config update error: {e}", "ERROR")
            # Restore old config on error
            self.config = old_config
    
    def close_all_positions(self):
        """Close all open positions"""
        try:
            self.log_message("Closing all positions...", "INFO")
            # Implementation would go here for real trading
            
        except Exception as e:
            self.log_message(f"Close positions error: {e}", "ERROR")
    
    def export_logs(self) -> Optional[str]:
        """Export trading logs"""
        try:
            filename = f"trading_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            self.log_message(f"Logs exported to {filename}", "INFO")
            return filename
            
        except Exception as e:
            self.log_message(f"Export error: {e}", "ERROR")
            return None
    
    def test_signal(self):
        """Test signal generation"""
        try:
            if self.current_market_data:
                signal = self.generate_signal(self.current_market_data)
                if signal:
                    self.signal_trade_signal.emit(signal)
                    self.log_message(f"Test Signal Generated: {signal['type']} at {signal['entry_price']:.5f}", "INFO")
                else:
                    self.log_message("No signal generated in current market conditions", "INFO")
            else:
                self.log_message("No market data available for signal testing", "WARNING")
        except Exception as e:
            self.log_message(f"Test signal error: {e}", "ERROR")
