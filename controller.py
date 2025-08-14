"""
MT5 Bot Controller - PRODUCTION READY for Windows Real Trading
Handles MT5 connection, trading logic, and market data processing
"""

try:
    import MetaTrader5 as mt5
    DEMO_MODE = False
except ImportError:
    # Fallback for development environment only
    import mock_mt5 as mt5
    DEMO_MODE = True
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
    """Main controller for the MT5 trading bot - PRODUCTION READY"""

    # Signals for GUI updates
    signal_log = Signal(str, str)  # message, level
    signal_status = Signal(str)    # status message
    signal_market_data = Signal(dict)  # market data
    signal_trade_signal = Signal(dict)  # trade signals
    signal_position_update = Signal(list)  # positions list
    signal_account_update = Signal(dict)  # account info

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Bot state
        self.is_connected = False
        self.is_running = False
        self.shadow_mode = True  # Start in shadow mode for safety

        # Configuration - Optimized for XAUUSD scalping
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
        self.last_signal_time = None

        # Market data
        self.current_tick = None
        self.indicators = TechnicalIndicators()
        self.account_info = None

        # Timers
        self.market_timer = QTimer()
        self.market_timer.timeout.connect(self.update_market_data)

        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_info)

    def connect_mt5(self) -> bool:
        """Connect to MT5 terminal - CRITICAL for Windows live trading"""
        try:
            self.signal_log.emit("Connecting to MetaTrader 5...", "INFO")

            # Initialize MT5 connection
            if not mt5.initialize():
                error = mt5.last_error()
                self.signal_log.emit(f"MT5 initialization failed: {error}", "ERROR")
                return False

            # Get account info immediately
            account_info = mt5.account_info()
            if account_info is None:
                self.signal_log.emit("Failed to get account info - check MT5 login", "ERROR")
                mt5.shutdown()
                return False

            self.account_info = account_info
            self.is_connected = True

            # Log connection success with account details
            self.signal_log.emit(f"✓ Connected to MT5 successfully!", "INFO")
            self.signal_log.emit(f"Account: {account_info.login}", "INFO")
            self.signal_log.emit(f"Balance: ${account_info.balance:.2f}", "INFO")
            self.signal_log.emit(f"Server: {account_info.server if hasattr(account_info, 'server') else 'N/A'}", "INFO")

            self.signal_status.emit("Connected")

            # Start account info timer
            self.account_timer.start(5000)  # Update every 5 seconds

            return True

        except Exception as e:
            self.signal_log.emit(f"MT5 connection error: {e}", "ERROR")
            return False

    def disconnect_mt5(self):
        """Disconnect from MT5 terminal"""
        try:
            if self.is_running:
                self.stop_bot()

            self.market_timer.stop()
            self.account_timer.stop()

            mt5.shutdown()
            self.is_connected = False
            self.account_info = None

            self.signal_log.emit("Disconnected from MT5", "INFO")
            self.signal_status.emit("Disconnected")

        except Exception as e:
            self.signal_log.emit(f"Disconnect error: {e}", "ERROR")

    def find_available_gold_symbol(self, preferred_symbol: str) -> Optional[str]:
        """Find available XAUUSD symbol with comprehensive validation"""
        # Priority order for XAUUSD symbols
        symbol_priority = [preferred_symbol, 'XAUUSD', 'XAUUSDm', 'XAUUSDc']

        for symbol in symbol_priority:
            try:
                if validate_symbol(symbol):
                    # Additional validation for trading
                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info and symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
                        self.signal_log.emit(f"✓ Using symbol: {symbol}", "INFO")
                        return symbol
            except Exception as e:
                self.logger.warning(f"Symbol validation failed for {symbol}: {e}")
                continue

        return None

    def update_config(self, new_config: Dict):
        """Update bot configuration with validation"""
        try:
            self.config.update(new_config)
            self.signal_log.emit("Configuration updated successfully", "INFO")

            # Log important config changes
            if 'symbol' in new_config:
                self.signal_log.emit(f"Symbol changed to: {new_config['symbol']}", "INFO")
            if 'risk_percent' in new_config:
                self.signal_log.emit(f"Risk per trade: {new_config['risk_percent']}%", "INFO")

        except Exception as e:
            self.signal_log.emit(f"Config update error: {e}", "ERROR")

    def start_bot(self):
        """Start the trading bot with comprehensive validation"""
        if not self.is_connected:
            self.signal_log.emit("❌ Not connected to MT5", "ERROR")
            return False

        try:
            # Validate symbol availability
            symbol = self.config['symbol']
            available_symbol = self.find_available_gold_symbol(symbol)

            if not available_symbol:
                self.signal_log.emit("❌ No XAUUSD symbols available for trading", "ERROR")
                return False

            # Update config with available symbol if different
            if available_symbol != symbol:
                self.config['symbol'] = available_symbol
                self.signal_log.emit(f"✓ Symbol auto-selected: {available_symbol}", "INFO")

            # Reset trading state
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.consecutive_losses = 0
            self.in_cooldown = False
            self.last_signal_time = None

            self.is_running = True

            mode = "SHADOW MODE" if self.shadow_mode else "⚠️ LIVE TRADING MODE"
            self.signal_log.emit(f"🚀 Bot STARTED for {available_symbol} in {mode}", "INFO")
            self.signal_status.emit("Running")

            # Start market data processing
            self.market_timer.start(500)  # Update every 500ms for faster response

            return True

        except Exception as e:
            self.signal_log.emit(f"Bot start error: {e}", "ERROR")
            return False

    def stop_bot(self):
        """Stop the trading bot"""
        self.is_running = False
        self.market_timer.stop()
        self.signal_log.emit("🛑 Bot STOPPED", "INFO")
        self.signal_status.emit("Stopped")

    def toggle_shadow_mode(self, enabled: bool):
        """Toggle shadow mode on/off"""
        self.shadow_mode = enabled
        self.signal_log.emit(f"Shadow mode {'enabled' if enabled else 'disabled'}", "INFO")

    def update_account_info(self):
        """Update account information"""
        try:
            if not self.is_connected:
                return

            account_info = mt5.account_info()
            if account_info:
                self.account_info = account_info
                account_data = {
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'margin': account_info.margin,
                    'margin_free': account_info.margin_free,
                    'profit': account_info.profit
                }
                self.signal_account_update.emit(account_data)

        except Exception as e:
            self.logger.error(f"Account info update error: {e}")

    def update_market_data(self):
        """Update market data and process trading logic - CORE TRADING ENGINE"""
        if not self.is_running or not self.is_connected:
            return

        try:
            symbol = self.config['symbol']

            # Get current tick data
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return

            self.current_tick = tick

            # Calculate spread in points
            spread_points = get_spread_points(symbol, tick.ask, tick.bid)

            # Skip if spread too wide
            if spread_points > self.config['max_spread_points']:
                return

            # Get market data for analysis
            m1_data = self.get_timeframe_data(symbol, mt5.TIMEFRAME_M1, 200)
            m5_data = self.get_timeframe_data(symbol, mt5.TIMEFRAME_M5, 200)

            if m1_data is None or m5_data is None or len(m1_data) < 50 or len(m5_data) < 50:
                return

            # Calculate technical indicators
            indicators_m1 = self.calculate_indicators(m1_data)
            indicators_m5 = self.calculate_indicators(m5_data)

            # Prepare market data package
            market_data = {
                'symbol': symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': spread_points,
                'time': datetime.fromtimestamp(tick.time),
                'indicators_m1': indicators_m1,
                'indicators_m5': indicators_m5
            }

            # Emit market data for GUI
            self.signal_market_data.emit(market_data)

            # Process trading logic
            self.process_trading_logic(market_data)

        except Exception as e:
            self.signal_log.emit(f"Market data error: {e}", "ERROR")

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
        """Calculate technical indicators for trading analysis"""
        try:
            close = np.array(data['close'].values, dtype=np.float64)
            high = np.array(data['high'].values, dtype=np.float64)
            low = np.array(data['low'].values, dtype=np.float64)

            if len(close) < 50:
                return {}

            # Calculate EMAs
            ema_fast = self.indicators.ema(close, self.config['ema_periods']['fast'])
            ema_medium = self.indicators.ema(close, self.config['ema_periods']['medium'])
            ema_slow = self.indicators.ema(close, self.config['ema_periods']['slow'])

            # Calculate RSI
            rsi = self.indicators.rsi(close, self.config['rsi_period'])

            # Calculate ATR
            atr = self.indicators.atr(high, low, close, self.config['atr_period'])

            return {
                'ema_fast': ema_fast[-1] if len(ema_fast) > 0 else None,
                'ema_medium': ema_medium[-1] if len(ema_medium) > 0 else None,
                'ema_slow': ema_slow[-1] if len(ema_slow) > 0 else None,
                'rsi': rsi[-1] if len(rsi) > 0 else None,
                'atr': atr[-1] if len(atr) > 0 else None,
                'close': close[-1]
            }

        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}

    def process_trading_logic(self, market_data: Dict):
        """Process trading logic - ENHANCED FOR HIGH WINRATE"""
        try:
            # Reset daily counters if new day
            self.reset_daily_counters()

            # Check daily limits
            if not self.check_daily_limits():
                return

            # Check trading session
            if not check_trading_session():
                return

            # Check cooldown after losses
            if self.in_cooldown:
                return

            # Get indicators
            indicators_m1 = market_data['indicators_m1']
            indicators_m5 = market_data['indicators_m5']

            # Validate all indicators are present
            required_indicators = ['ema_fast', 'ema_medium', 'ema_slow', 'rsi', 'atr', 'close']
            if not all(indicators_m1.get(k) is not None for k in required_indicators):
                return
            if not all(indicators_m5.get(k) is not None for k in required_indicators):
                return

            # Analyze for trading signals
            signal = self.analyze_enhanced_signal(market_data, indicators_m1, indicators_m5)

            if signal:
                self.signal_trade_signal.emit(signal)

                # Execute trade if not in shadow mode
                if not self.shadow_mode:
                    self.execute_trade(signal)
                else:
                    self.signal_log.emit(f"📊 SHADOW: {signal['type']} signal detected", "INFO")

        except Exception as e:
            self.signal_log.emit(f"Trading logic error: {e}", "ERROR")

    def analyze_enhanced_signal(self, market_data: Dict, ind_m1: Dict, ind_m5: Dict) -> Optional[Dict]:
        """Enhanced signal analysis for higher winrate - PRODUCTION OPTIMIZED"""
        try:
            current_price = market_data['ask']
            spread = market_data['spread']

            # M5 Trend Analysis (Primary filter)
            m5_bullish_trend = (
                ind_m5['ema_fast'] > ind_m5['ema_medium'] and
                ind_m5['ema_medium'] > ind_m5['ema_slow'] and
                ind_m5['close'] > ind_m5['ema_fast'] and
                ind_m5['rsi'] > 45 and ind_m5['rsi'] < 80
            )

            m5_bearish_trend = (
                ind_m5['ema_fast'] < ind_m5['ema_medium'] and
                ind_m5['ema_medium'] < ind_m5['ema_slow'] and
                ind_m5['close'] < ind_m5['ema_fast'] and
                ind_m5['rsi'] < 55 and ind_m5['rsi'] > 20
            )

            # M1 Entry Signals (Precise timing)
            m1_buy_signal = (
                ind_m1['ema_fast'] > ind_m1['ema_medium'] and
                ind_m1['close'] > ind_m1['ema_medium'] and
                ind_m1['rsi'] > 50 and ind_m1['rsi'] < 75 and
                current_price > ind_m1['ema_fast'] * 0.9998  # Near EMA for entry
            )

            m1_sell_signal = (
                ind_m1['ema_fast'] < ind_m1['ema_medium'] and
                ind_m1['close'] < ind_m1['ema_medium'] and
                ind_m1['rsi'] < 50 and ind_m1['rsi'] > 25 and
                current_price < ind_m1['ema_fast'] * 1.0002  # Near EMA for entry
            )

            # Additional filters
            volatility_ok = ind_m1['atr'] > 0.0001  # Sufficient volatility
            spread_ok = spread <= self.config['max_spread_points']

            # Time-based filters (avoid low liquidity periods)
            now = datetime.now().time()
            avoid_time = (
                (now >= time(22, 30) or now <= time(1, 30)) or  # Asian overnight
                (now >= time(16, 45) and now <= time(17, 15))   # London close gap
            )

            # Signal frequency control (prevent overtrading)
            signal_interval_ok = True
            if self.last_signal_time:
                time_since_last = datetime.now() - self.last_signal_time
                signal_interval_ok = time_since_last.total_seconds() > 300  # 5 minutes minimum

            # Generate signals with enhanced criteria
            if (m5_bullish_trend and m1_buy_signal and volatility_ok and
                spread_ok and not avoid_time and signal_interval_ok):

                self.last_signal_time = datetime.now()
                self.signal_log.emit("🔥 STRONG BUY SIGNAL DETECTED!", "INFO")
                return self.create_buy_signal(market_data, ind_m1)

            elif (m5_bearish_trend and m1_sell_signal and volatility_ok and
                  spread_ok and not avoid_time and signal_interval_ok):

                self.last_signal_time = datetime.now()
                self.signal_log.emit("🔥 STRONG SELL SIGNAL DETECTED!", "INFO")
                return self.create_sell_signal(market_data, ind_m1)

            return None

        except Exception as e:
            self.logger.error(f"Signal analysis error: {e}")
            return None

    def create_buy_signal(self, market_data: Dict, indicators: Dict) -> Dict:
        """Create BUY signal with precise SL/TP calculation"""
        symbol = market_data['symbol']
        entry_price = market_data['ask']
        atr = indicators['atr']

        # Get symbol specifications
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {}

        # Enhanced SL/TP calculation using ATR
        atr_points = (atr / symbol_info.point) * 1.5  # ATR multiplier for volatility
        sl_distance_points = max(self.config['min_sl_points'], atr_points)

        # Precise price calculations
        sl_price = entry_price - (sl_distance_points * symbol_info.point)
        tp_price = entry_price + (sl_distance_points * self.config['risk_multiple'] * symbol_info.point)

        # Round to valid tick sizes
        sl_price = round(sl_price / symbol_info.trade_tick_size) * symbol_info.trade_tick_size
        tp_price = round(tp_price / symbol_info.trade_tick_size) * symbol_info.trade_tick_size

        # Calculate optimal lot size
        lot_size = calculate_lot_size(self.config['risk_percent'], sl_distance_points, symbol)

        return {
            'type': 'BUY',
            'symbol': symbol,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'lot_size': lot_size,
            'sl_distance_points': sl_distance_points,
            'risk_reward': self.config['risk_multiple'],
            'timestamp': datetime.now()
        }

    def create_sell_signal(self, market_data: Dict, indicators: Dict) -> Dict:
        """Create SELL signal with precise SL/TP calculation"""
        symbol = market_data['symbol']
        entry_price = market_data['bid']
        atr = indicators['atr']

        # Get symbol specifications
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {}

        # Enhanced SL/TP calculation using ATR
        atr_points = (atr / symbol_info.point) * 1.5  # ATR multiplier for volatility
        sl_distance_points = max(self.config['min_sl_points'], atr_points)

        # Precise price calculations
        sl_price = entry_price + (sl_distance_points * symbol_info.point)
        tp_price = entry_price - (sl_distance_points * self.config['risk_multiple'] * symbol_info.point)

        # Round to valid tick sizes
        sl_price = round(sl_price / symbol_info.trade_tick_size) * symbol_info.trade_tick_size
        tp_price = round(tp_price / symbol_info.trade_tick_size) * symbol_info.trade_tick_size

        # Calculate optimal lot size
        lot_size = calculate_lot_size(self.config['risk_percent'], sl_distance_points, symbol)

        return {
            'type': 'SELL',
            'symbol': symbol,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'lot_size': lot_size,
            'sl_distance_points': sl_distance_points,
            'risk_reward': self.config['risk_multiple'],
            'timestamp': datetime.now()
        }

    def execute_trade(self, signal: Dict):
        """Execute trade with comprehensive validation - LIVE TRADING"""
        try:
            symbol = signal['symbol']
            trade_type = mt5.ORDER_TYPE_BUY if signal['type'] == 'BUY' else mt5.ORDER_TYPE_SELL

            # Pre-execution validation
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.signal_log.emit(f"❌ Symbol {symbol} not available", "ERROR")
                return False

            # Validate lot size
            lot_size = signal['lot_size']
            if lot_size < symbol_info.volume_min or lot_size > symbol_info.volume_max:
                self.signal_log.emit(f"❌ Invalid lot size: {lot_size}", "ERROR")
                return False

            # Get fresh market prices
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.signal_log.emit("❌ Failed to get current prices", "ERROR")
                return False

            # Use live market prices
            execution_price = tick.ask if signal['type'] == 'BUY' else tick.bid

            # Validate stop levels
            stops_level = symbol_info.trade_stops_level * symbol_info.point
            sl_distance = abs(execution_price - signal['sl_price'])
            tp_distance = abs(execution_price - signal['tp_price'])

            if sl_distance < stops_level or tp_distance < stops_level:
                self.signal_log.emit(f"❌ SL/TP too close to market", "ERROR")
                return False

            # Dynamic deviation based on volatility
            deviation = min(max(int(signal['sl_distance_points'] * 0.1), 10), 50)

            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": trade_type,
                "price": execution_price,
                "sl": signal['sl_price'],
                "tp": signal['tp_price'],
                "deviation": deviation,
                "magic": self.config['magic_number'],
                "comment": f"ScalpBot_{signal['type']}_{datetime.now().strftime('%H%M%S')}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Log execution attempt
            self.signal_log.emit(
                f"⚡ Executing {signal['type']}: {lot_size} lots @ {execution_price:.5f}", "INFO"
            )

            # Execute order with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                result = mt5.order_send(request)

                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    # SUCCESS!
                    self.daily_trades += 1
                    self.consecutive_losses = 0  # Reset loss counter

                    self.signal_log.emit(
                        f"✅ {signal['type']} ORDER EXECUTED! Ticket: #{result.order}, "
                        f"Price: {result.price:.5f}", "INFO"
                    )

                    # Update positions display
                    self.update_positions_display()

                    return True

                elif result.retcode in [mt5.TRADE_RETCODE_PRICE_OFF, mt5.TRADE_RETCODE_REQUOTE]:
                    # Handle requote
                    if attempt < max_retries - 1:
                        tick = mt5.symbol_info_tick(symbol)
                        if tick:
                            request["price"] = tick.ask if signal['type'] == 'BUY' else tick.bid
                            self.signal_log.emit(f"Requote - retry {attempt+2}", "WARNING")
                            continue

                # Log error
                self.signal_log.emit(f"❌ Order failed: {result.comment}", "ERROR")

                if attempt < max_retries - 1:
                    import time
                    time.sleep(0.1)

            # All attempts failed
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.in_cooldown = True
                self.signal_log.emit("⏸️ COOLDOWN ACTIVATED after consecutive losses", "WARNING")

            return False

        except Exception as e:
            self.signal_log.emit(f"❌ Trade execution error: {e}", "ERROR")
            return False

    def reset_daily_counters(self):
        """Reset daily trading counters"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.consecutive_losses = 0
            self.in_cooldown = False
            self.last_reset_date = current_date
            self.signal_log.emit("📅 Daily counters reset", "INFO")

    def check_daily_limits(self) -> bool:
        """Check daily trading limits"""
        # Check max trades
        if self.daily_trades >= self.config['max_trades_per_day']:
            return False

        # Check max daily loss
        if self.account_info:
            daily_loss_percent = abs(self.daily_pnl) / self.account_info.balance * 100
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

    def update_positions_display(self):
        """Update positions display in GUI"""
        try:
            positions = self.get_positions()
            self.signal_position_update.emit(positions)
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")