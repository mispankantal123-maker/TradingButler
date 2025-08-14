"""
Fixed PySide6 GUI for MT5 Scalping Bot - PRODUCTION READY
Perbaikan untuk masalah krusial:
1. Input TP/SL dinamis sesuai mode (ATR, Points, Pips, Balance%)
2. Status indicators real-time
3. Emergency controls
"""

import sys
from datetime import datetime
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QTextEdit, QPlainTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QGridLayout, QSplitter, QProgressBar,
    QStatusBar, QMessageBox, QFrame, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Slot, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon, QColor

class MainWindow(QMainWindow):
    """Fixed Main Window dengan TP/SL input dinamis"""
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("MT5 Professional Scalping Bot - FIXED VERSION")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Initialize all required attributes
        self.connection_status = None
        self.bot_status = None
        self.mode_status = None
        
        # TP/SL Input widgets (akan dibuat dinamis)
        self.tp_sl_inputs = {}
        
        # Setup UI components
        try:
            self.setup_ui()
            self.setup_status_bar()
            self.connect_signals()
            
            # Update timer for GUI refresh
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_gui_data)
            self.update_timer.start(1000)  # Update every second
            
            # Initialize display values
            self.initialize_displays()
            
        except Exception as e:
            QMessageBox.critical(self, "GUI Initialization Error", f"Failed to setup GUI: {e}")
            raise
    
    def setup_ui(self):
        """Setup the main user interface"""
        try:
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            # Create tab widget
            self.tab_widget = QTabWidget()
            layout.addWidget(self.tab_widget)
            
            # Create all tabs dengan error handling individual
            try:
                self.create_dashboard_tab()
            except Exception as e:
                print(f"Dashboard tab creation failed: {e}")
                
            try:
                self.create_strategy_tab()
            except Exception as e:
                print(f"Strategy tab creation failed: {e}")
                
            try:
                self.create_risk_tab()
            except Exception as e:
                print(f"Risk tab creation failed: {e}")
                
            try:
                self.create_execution_tab()
            except Exception as e:
                print(f"Execution tab creation failed: {e}")
                
            try:
                self.create_positions_tab()
            except Exception as e:
                print(f"Positions tab creation failed: {e}")
                
            try:
                self.create_logs_tab()
            except Exception as e:
                print(f"Logs tab creation failed: {e}")
                # Fallback: create simple logs tab
                self.create_simple_logs_tab()
                
            try:
                self.create_tools_tab()
            except Exception as e:
                print(f"Tools tab creation failed: {e}")
            
        except Exception as e:
            raise Exception(f"UI setup failed: {e}")
    
    def create_dashboard_tab(self):
        """Create enhanced dashboard with status indicators"""
        try:
            dashboard = QWidget()
            layout = QVBoxLayout(dashboard)
            
            # Connection group
            conn_group = QGroupBox("🔌 MT5 Connection")
            conn_layout = QFormLayout(conn_group)
            
            self.connect_btn = QPushButton("Connect")
            self.connect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
            
            self.disconnect_btn = QPushButton("Disconnect")
            self.disconnect_btn.setEnabled(False)
            
            self.connection_status = QLabel("⚪ Disconnected")
            
            conn_layout.addRow("Action:", self.connect_btn)
            conn_layout.addRow("", self.disconnect_btn)
            conn_layout.addRow("Status:", self.connection_status)
            
            # Symbol group
            symbol_group = QGroupBox("📊 Symbol Configuration")
            symbol_layout = QFormLayout(symbol_group)
            
            self.symbol_combo = QComboBox()
            self.symbol_combo.addItems(["XAUUSD", "XAUUSDC", "XAUUSDm", "EURUSD", "GBPUSD"])
            self.symbol_combo.setCurrentText("XAUUSD")
            
            # Warning label untuk non-XAU symbols
            self.symbol_warning = QLabel("")
            self.symbol_warning.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
            self.symbol_warning.setWordWrap(True)
            
            symbol_layout.addRow("Symbol:", self.symbol_combo)
            symbol_layout.addRow("", self.symbol_warning)
            
            # Bot control group
            control_group = QGroupBox("🤖 Bot Control")
            control_layout = QFormLayout(control_group)
            
            self.start_btn = QPushButton("Start Bot")
            self.start_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
            self.start_btn.setEnabled(False)
            
            self.stop_btn = QPushButton("Stop Bot")
            self.stop_btn.setEnabled(False)
            
            self.emergency_stop_btn = QPushButton("🛑 EMERGENCY STOP")
            self.emergency_stop_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; font-weight: bold; }")
            self.emergency_stop_btn.setEnabled(False)
            
            self.shadow_mode_cb = QCheckBox("Shadow Mode (Safe Testing)")
            self.shadow_mode_cb.setChecked(True)  # Start in shadow mode
            
            self.bot_status = QLabel("⚪ Stopped")
            
            control_layout.addRow("", self.start_btn)
            control_layout.addRow("", self.stop_btn)
            control_layout.addRow("", self.emergency_stop_btn)
            control_layout.addRow("", self.shadow_mode_cb)
            control_layout.addRow("Status:", self.bot_status)
            
            # Real-time status indicators
            status_group = QGroupBox("🚦 Real-time Status")
            status_layout = QFormLayout(status_group)
            
            self.spread_status = QLabel("⚪ Unknown")
            self.session_status = QLabel("⚪ Unknown")
            self.risk_status = QLabel("⚪ Unknown")
            
            status_layout.addRow("Spread OK:", self.spread_status)
            status_layout.addRow("Session OK:", self.session_status)
            status_layout.addRow("Risk OK:", self.risk_status)
            
            # Market data group
            market_group = QGroupBox("📈 Live Market Data")
            market_layout = QFormLayout(market_group)
            
            self.bid_label = QLabel("N/A")
            self.ask_label = QLabel("N/A")
            self.spread_label = QLabel("N/A")
            self.last_update_label = QLabel("N/A")
            
            # Style market labels
            market_labels = [self.bid_label, self.ask_label, self.spread_label, self.last_update_label]
            for label in market_labels:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 14px; font-weight: bold; }")
            
            market_layout.addRow("💰 Bid:", self.bid_label)
            market_layout.addRow("💸 Ask:", self.ask_label)
            market_layout.addRow("📏 Spread:", self.spread_label)
            market_layout.addRow("🕐 Updated:", self.last_update_label)
            
            # Account group
            account_group = QGroupBox("👤 Account Information")
            account_layout = QFormLayout(account_group)
            
            self.balance_label = QLabel("N/A")
            self.equity_label = QLabel("N/A")
            self.margin_label = QLabel("N/A")
            self.pnl_label = QLabel("N/A")
            self.margin_level_label = QLabel("N/A")
            
            # Style account labels
            account_labels = [self.balance_label, self.equity_label, self.margin_label, self.pnl_label, self.margin_level_label]
            for label in account_labels:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 12px; }")
            
            account_layout.addRow("💵 Balance:", self.balance_label)
            account_layout.addRow("💎 Equity:", self.equity_label)
            account_layout.addRow("📊 Margin Used:", self.margin_label)
            account_layout.addRow("📈 P&L:", self.pnl_label)
            account_layout.addRow("🎯 Margin Level:", self.margin_level_label)
            
            # Layout arrangement
            top_layout = QHBoxLayout()
            top_layout.addWidget(conn_group)
            top_layout.addWidget(symbol_group)
            top_layout.addWidget(control_group)
            
            middle_layout = QHBoxLayout()
            middle_layout.addWidget(status_group)
            middle_layout.addWidget(market_group)
            
            bottom_layout = QHBoxLayout()
            bottom_layout.addWidget(account_group)
            
            layout.addLayout(top_layout)
            layout.addLayout(middle_layout)
            layout.addLayout(bottom_layout)
            layout.addStretch()
            
            # Connect signals
            self.connect_btn.clicked.connect(self.on_connect)
            self.disconnect_btn.clicked.connect(self.on_disconnect)
            self.start_btn.clicked.connect(self.on_start_bot)
            self.stop_btn.clicked.connect(self.on_stop_bot)
            self.emergency_stop_btn.clicked.connect(self.on_emergency_stop)
            self.shadow_mode_cb.toggled.connect(self.on_shadow_mode_toggle)
            self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
            
            self.tab_widget.addTab(dashboard, "🏠 Dashboard")
            
        except Exception as e:
            raise Exception(f"Dashboard creation failed: {e}")
    
    def create_strategy_tab(self):
        """Create strategy tab with live indicators"""
        try:
            strategy = QWidget()
            layout = QVBoxLayout(strategy)
            
            # Strategy settings
            settings_group = QGroupBox("⚙️ Strategy Configuration")
            settings_layout = QFormLayout(settings_group)
            
            # EMA periods
            self.ema_fast_spin = QSpinBox()
            self.ema_fast_spin.setRange(1, 50)
            self.ema_fast_spin.setValue(9)
            
            self.ema_medium_spin = QSpinBox()
            self.ema_medium_spin.setRange(1, 100)
            self.ema_medium_spin.setValue(21)
            
            self.ema_slow_spin = QSpinBox()
            self.ema_slow_spin.setRange(1, 200)
            self.ema_slow_spin.setValue(50)
            
            # RSI period
            self.rsi_period_spin = QSpinBox()
            self.rsi_period_spin.setRange(1, 50)
            self.rsi_period_spin.setValue(14)
            
            # ATR period
            self.atr_period_spin = QSpinBox()
            self.atr_period_spin.setRange(1, 50)
            self.atr_period_spin.setValue(14)
            
            # RSI filter checkbox
            self.rsi_filter_cb = QCheckBox("Use RSI re-cross 50 filter")
            
            settings_layout.addRow("⚡ Fast EMA:", self.ema_fast_spin)
            settings_layout.addRow("📊 Medium EMA:", self.ema_medium_spin)
            settings_layout.addRow("🐌 Slow EMA:", self.ema_slow_spin)
            settings_layout.addRow("📈 RSI Period:", self.rsi_period_spin)
            settings_layout.addRow("📏 ATR Period:", self.atr_period_spin)
            settings_layout.addRow("", self.rsi_filter_cb)
            
            # Live indicators display
            indicators_group = QGroupBox("📊 Live Indicators")
            indicators_layout = QVBoxLayout(indicators_group)
            
            # M1 indicators
            m1_group = QGroupBox("M1 Indicators")
            m1_layout = QFormLayout(m1_group)
            
            self.ema_fast_m1_label = QLabel("N/A")
            self.ema_medium_m1_label = QLabel("N/A")
            self.ema_slow_m1_label = QLabel("N/A")
            self.rsi_m1_label = QLabel("N/A")
            self.atr_m1_label = QLabel("N/A")
            
            m1_layout.addRow("⚡ Fast EMA:", self.ema_fast_m1_label)
            m1_layout.addRow("📊 Medium EMA:", self.ema_medium_m1_label)
            m1_layout.addRow("🐌 Slow EMA:", self.ema_slow_m1_label)
            m1_layout.addRow("📈 RSI:", self.rsi_m1_label)
            m1_layout.addRow("📏 ATR:", self.atr_m1_label)
            
            # M5 indicators
            m5_group = QGroupBox("M5 Indicators")
            m5_layout = QFormLayout(m5_group)
            
            self.ema_fast_m5_label = QLabel("N/A")
            self.ema_medium_m5_label = QLabel("N/A")
            self.ema_slow_m5_label = QLabel("N/A")
            self.rsi_m5_label = QLabel("N/A")
            self.atr_m5_label = QLabel("N/A")
            
            m5_layout.addRow("⚡ Fast EMA:", self.ema_fast_m5_label)
            m5_layout.addRow("📊 Medium EMA:", self.ema_medium_m5_label)
            m5_layout.addRow("🐌 Slow EMA:", self.ema_slow_m5_label)
            m5_layout.addRow("📈 RSI:", self.rsi_m5_label)
            m5_layout.addRow("📏 ATR:", self.atr_m5_label)
            
            # Style indicator labels
            indicator_labels = [
                self.ema_fast_m1_label, self.ema_medium_m1_label, self.ema_slow_m1_label,
                self.rsi_m1_label, self.atr_m1_label,
                self.ema_fast_m5_label, self.ema_medium_m5_label, self.ema_slow_m5_label,
                self.rsi_m5_label, self.atr_m5_label
            ]
            
            for label in indicator_labels:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 11px; color: #2196F3; }")
            
            indicators_hlayout = QHBoxLayout()
            indicators_hlayout.addWidget(m1_group)
            indicators_hlayout.addWidget(m5_group)
            indicators_layout.addLayout(indicators_hlayout)
            
            # Layout
            layout.addWidget(settings_group)
            layout.addWidget(indicators_group)
            layout.addStretch()
            
            self.tab_widget.addTab(strategy, "📈 Strategy")
            
        except Exception as e:
            raise Exception(f"Strategy tab creation failed: {e}")
    
    def create_risk_tab(self):
        """Create risk management tab dengan TP/SL input dinamis - KRUSIAL"""
        try:
            risk = QWidget()
            layout = QVBoxLayout(risk)
            
            # Risk management settings
            risk_group = QGroupBox("🛡️ Risk Management")
            risk_layout = QFormLayout(risk_group)
            
            self.risk_percent_spin = QDoubleSpinBox()
            self.risk_percent_spin.setRange(0.1, 10.0)
            self.risk_percent_spin.setValue(0.5)
            self.risk_percent_spin.setSuffix("%")
            
            self.max_daily_loss_spin = QDoubleSpinBox()
            self.max_daily_loss_spin.setRange(0.5, 20.0)
            self.max_daily_loss_spin.setValue(2.0)
            self.max_daily_loss_spin.setSuffix("%")
            
            self.max_trades_spin = QSpinBox()
            self.max_trades_spin.setRange(1, 100)
            self.max_trades_spin.setValue(15)
            
            self.max_spread_spin = QSpinBox()
            self.max_spread_spin.setRange(1, 100)
            self.max_spread_spin.setValue(30)
            self.max_spread_spin.setSuffix(" points")
            
            risk_layout.addRow("💰 Risk per Trade:", self.risk_percent_spin)
            risk_layout.addRow("🚫 Max Daily Loss:", self.max_daily_loss_spin)
            risk_layout.addRow("📊 Max Trades/Day:", self.max_trades_spin)
            risk_layout.addRow("📏 Max Spread:", self.max_spread_spin)
            
            # TP/SL Configuration - KRUSIAL PERBAIKAN
            tpsl_group = QGroupBox("🎯 Take Profit / Stop Loss Configuration")
            tpsl_layout = QVBoxLayout(tpsl_group)
            
            # Mode selection
            mode_layout = QFormLayout()
            self.tpsl_mode_combo = QComboBox()
            self.tpsl_mode_combo.addItems(["ATR", "Points", "Pips", "Balance%"])
            self.tpsl_mode_combo.currentTextChanged.connect(self.on_tpsl_mode_changed)
            mode_layout.addRow("📋 TP/SL Mode:", self.tpsl_mode_combo)
            tpsl_layout.addLayout(mode_layout)
            
            # Dynamic inputs container
            self.tpsl_inputs_frame = QFrame()
            self.tpsl_inputs_layout = QFormLayout(self.tpsl_inputs_frame)
            tpsl_layout.addWidget(self.tpsl_inputs_frame)
            
            # Initialize with ATR mode
            self.setup_tpsl_inputs("ATR")
            
            # Daily stats display
            stats_group = QGroupBox("📊 Daily Statistics")
            stats_layout = QFormLayout(stats_group)
            
            self.daily_trades_label = QLabel("0")
            self.daily_pnl_label = QLabel("$0.00")
            self.consecutive_losses_label = QLabel("0")
            
            stats_layout.addRow("🔢 Trades Today:", self.daily_trades_label)
            stats_layout.addRow("💰 P&L Today:", self.daily_pnl_label)
            stats_layout.addRow("📉 Consecutive Losses:", self.consecutive_losses_label)
            
            # Layout arrangement
            layout.addWidget(risk_group)
            layout.addWidget(tpsl_group)
            layout.addWidget(stats_group)
            layout.addStretch()
            
            self.tab_widget.addTab(risk, "🛡️ Risk Management")
            
        except Exception as e:
            raise Exception(f"Risk tab creation failed: {e}")
    
    def setup_tpsl_inputs(self, mode):
        """Setup TP/SL inputs sesuai mode - KRUSIAL"""
        try:
            # Clear existing inputs
            for i in reversed(range(self.tpsl_inputs_layout.count())):
                child = self.tpsl_inputs_layout.itemAt(i).widget()
                if child:
                    child.deleteLater()
            
            self.tp_sl_inputs = {}
            
            if mode == "ATR":
                # ATR multiplier for SL, Risk multiple for TP
                self.tp_sl_inputs['atr_multiplier'] = QDoubleSpinBox()
                self.tp_sl_inputs['atr_multiplier'].setRange(0.5, 5.0)
                self.tp_sl_inputs['atr_multiplier'].setValue(2.0)
                self.tp_sl_inputs['atr_multiplier'].setSingleStep(0.1)
                
                self.tp_sl_inputs['risk_multiple'] = QDoubleSpinBox()
                self.tp_sl_inputs['risk_multiple'].setRange(1.0, 5.0)
                self.tp_sl_inputs['risk_multiple'].setValue(2.0)
                self.tp_sl_inputs['risk_multiple'].setSingleStep(0.1)
                
                self.tpsl_inputs_layout.addRow("📏 ATR Multiplier (SL):", self.tp_sl_inputs['atr_multiplier'])
                self.tpsl_inputs_layout.addRow("🎯 Risk Multiple (TP):", self.tp_sl_inputs['risk_multiple'])
                
                # Info label
                info_label = QLabel("SL = max(minSL, ATR × multiplier)\nTP = SL × risk_multiple")
                info_label.setStyleSheet("QLabel { color: gray; font-size: 10px; }")
                self.tpsl_inputs_layout.addRow("ℹ️ Info:", info_label)
            
            elif mode == "Points":
                # Direct points input
                self.tp_sl_inputs['tp_points'] = QSpinBox()
                self.tp_sl_inputs['tp_points'].setRange(10, 1000)
                self.tp_sl_inputs['tp_points'].setValue(200)
                self.tp_sl_inputs['tp_points'].setSuffix(" points")
                
                self.tp_sl_inputs['sl_points'] = QSpinBox()
                self.tp_sl_inputs['sl_points'].setRange(10, 500)
                self.tp_sl_inputs['sl_points'].setValue(100)
                self.tp_sl_inputs['sl_points'].setSuffix(" points")
                
                self.tpsl_inputs_layout.addRow("🎯 Take Profit:", self.tp_sl_inputs['tp_points'])
                self.tpsl_inputs_layout.addRow("🛑 Stop Loss:", self.tp_sl_inputs['sl_points'])
                
                # Info label
                info_label = QLabel("Direct points distance from entry")
                info_label.setStyleSheet("QLabel { color: gray; font-size: 10px; }")
                self.tpsl_inputs_layout.addRow("ℹ️ Info:", info_label)
            
            elif mode == "Pips":
                # Pips input (akan dikonversi ke points)
                self.tp_sl_inputs['tp_pips'] = QDoubleSpinBox()
                self.tp_sl_inputs['tp_pips'].setRange(1.0, 100.0)
                self.tp_sl_inputs['tp_pips'].setValue(20.0)
                self.tp_sl_inputs['tp_pips'].setSuffix(" pips")
                
                self.tp_sl_inputs['sl_pips'] = QDoubleSpinBox()
                self.tp_sl_inputs['sl_pips'].setRange(1.0, 50.0)
                self.tp_sl_inputs['sl_pips'].setValue(10.0)
                self.tp_sl_inputs['sl_pips'].setSuffix(" pips")
                
                self.tpsl_inputs_layout.addRow("🎯 Take Profit:", self.tp_sl_inputs['tp_pips'])
                self.tpsl_inputs_layout.addRow("🛑 Stop Loss:", self.tp_sl_inputs['sl_pips'])
                
                # Info label
                info_label = QLabel("Pips converted to points based on digits\n(digits 3,5: 1 pip = 10 points)")
                info_label.setStyleSheet("QLabel { color: gray; font-size: 10px; }")
                self.tpsl_inputs_layout.addRow("ℹ️ Info:", info_label)
            
            elif mode == "Balance%":
                # Percentage of balance
                self.tp_sl_inputs['tp_percent'] = QDoubleSpinBox()
                self.tp_sl_inputs['tp_percent'].setRange(0.1, 10.0)
                self.tp_sl_inputs['tp_percent'].setValue(1.0)
                self.tp_sl_inputs['tp_percent'].setSuffix("%")
                
                self.tp_sl_inputs['sl_percent'] = QDoubleSpinBox()
                self.tp_sl_inputs['sl_percent'].setRange(0.1, 5.0)
                self.tp_sl_inputs['sl_percent'].setValue(0.5)
                self.tp_sl_inputs['sl_percent'].setSuffix("%")
                
                self.tpsl_inputs_layout.addRow("🎯 TP (% Balance):", self.tp_sl_inputs['tp_percent'])
                self.tpsl_inputs_layout.addRow("🛑 SL (% Balance):", self.tp_sl_inputs['sl_percent'])
                
                # Info label
                info_label = QLabel("USD amount = balance × %\nConverted to points via tick_value")
                info_label.setStyleSheet("QLabel { color: gray; font-size: 10px; }")
                self.tpsl_inputs_layout.addRow("ℹ️ Info:", info_label)
            
        except Exception as e:
            print(f"Setup TP/SL inputs error: {e}")
    
    def create_execution_tab(self):
        """Create execution monitoring tab"""
        try:
            execution = QWidget()
            layout = QVBoxLayout(execution)
            
            # Current signal display
            signal_group = QGroupBox("🎯 Current Trading Signal")
            signal_layout = QFormLayout(signal_group)
            
            self.signal_side_label = QLabel("None")
            self.signal_price_label = QLabel("N/A")
            self.signal_reason_label = QLabel("N/A")
            self.signal_timestamp_label = QLabel("N/A")
            
            # Style signal labels
            signal_labels = [self.signal_side_label, self.signal_price_label, self.signal_reason_label, self.signal_timestamp_label]
            for label in signal_labels:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 12px; }")
            
            signal_layout.addRow("📊 Signal:", self.signal_side_label)
            signal_layout.addRow("💰 Entry Price:", self.signal_price_label)
            signal_layout.addRow("📝 Reason:", self.signal_reason_label)
            signal_layout.addRow("🕐 Time:", self.signal_timestamp_label)
            
            # Manual trading controls
            manual_group = QGroupBox("🖱️ Manual Trading Controls")
            manual_layout = QFormLayout(manual_group)
            
            self.manual_side_combo = QComboBox()
            self.manual_side_combo.addItems(["BUY", "SELL"])
            
            self.manual_lot_spin = QDoubleSpinBox()
            self.manual_lot_spin.setRange(0.01, 10.0)
            self.manual_lot_spin.setValue(0.01)
            self.manual_lot_spin.setSingleStep(0.01)
            
            self.manual_buy_btn = QPushButton("📈 Manual BUY")
            self.manual_buy_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
            self.manual_buy_btn.setEnabled(False)
            
            self.manual_sell_btn = QPushButton("📉 Manual SELL")
            self.manual_sell_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; }")
            self.manual_sell_btn.setEnabled(False)
            
            manual_layout.addRow("📊 Side:", self.manual_side_combo)
            manual_layout.addRow("📦 Lot Size:", self.manual_lot_spin)
            manual_layout.addRow("", self.manual_buy_btn)
            manual_layout.addRow("", self.manual_sell_btn)
            
            # Execution statistics
            exec_stats_group = QGroupBox("📊 Execution Statistics")
            exec_stats_layout = QFormLayout(exec_stats_group)
            
            self.signals_generated_label = QLabel("0")
            self.signals_executed_label = QLabel("0")
            self.execution_rate_label = QLabel("0%")
            self.last_execution_label = QLabel("Never")
            
            exec_stats_layout.addRow("🎯 Signals Generated:", self.signals_generated_label)
            exec_stats_layout.addRow("⚡ Signals Executed:", self.signals_executed_label)
            exec_stats_layout.addRow("📊 Execution Rate:", self.execution_rate_label)
            exec_stats_layout.addRow("🕐 Last Execution:", self.last_execution_label)
            
            # Layout
            layout.addWidget(signal_group)
            layout.addWidget(manual_group)
            layout.addWidget(exec_stats_group)
            layout.addStretch()
            
            self.tab_widget.addTab(execution, "⚡ Execution")
            
        except Exception as e:
            raise Exception(f"Execution tab creation failed: {e}")
    
    def create_positions_tab(self):
        """Create positions monitoring tab"""
        try:
            positions = QWidget()
            layout = QVBoxLayout(positions)
            
            # Positions table
            positions_group = QGroupBox("📊 Open Positions")
            positions_layout = QVBoxLayout(positions_group)
            
            self.positions_table = QTableWidget()
            self.positions_table.setColumnCount(8)
            self.positions_table.setHorizontalHeaderLabels([
                "Ticket", "Type", "Volume", "Price", "SL", "TP", "Profit", "Action"
            ])
            
            # Table styling
            self.positions_table.setAlternatingRowColors(True)
            self.positions_table.setSelectionBehavior(QTableWidget.SelectRows)
            
            positions_layout.addWidget(self.positions_table)
            
            # Position controls
            controls_layout = QHBoxLayout()
            
            self.close_selected_btn = QPushButton("❌ Close Selected")
            self.close_selected_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
            
            self.close_all_btn = QPushButton("🚫 Close All Positions")
            self.close_all_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; font-weight: bold; }")
            
            self.refresh_positions_btn = QPushButton("🔄 Refresh")
            
            controls_layout.addWidget(self.close_selected_btn)
            controls_layout.addWidget(self.close_all_btn)
            controls_layout.addWidget(self.refresh_positions_btn)
            controls_layout.addStretch()
            
            positions_layout.addLayout(controls_layout)
            
            # Position summary
            summary_group = QGroupBox("📊 Position Summary")
            summary_layout = QFormLayout(summary_group)
            
            self.total_positions_label = QLabel("0")
            self.total_volume_label = QLabel("0.00")
            self.total_profit_label = QLabel("$0.00")
            self.floating_pnl_label = QLabel("$0.00")
            
            summary_layout.addRow("📊 Total Positions:", self.total_positions_label)
            summary_layout.addRow("📦 Total Volume:", self.total_volume_label)
            summary_layout.addRow("💰 Total Profit:", self.total_profit_label)
            summary_layout.addRow("🏃 Floating P&L:", self.floating_pnl_label)
            
            # Layout
            layout.addWidget(positions_group)
            layout.addWidget(summary_group)
            
            # Connect signals
            self.close_selected_btn.clicked.connect(self.on_close_selected_position)
            self.close_all_btn.clicked.connect(self.on_close_all_positions)
            self.refresh_positions_btn.clicked.connect(self.on_refresh_positions)
            
            self.tab_widget.addTab(positions, "📊 Positions")
            
        except Exception as e:
            raise Exception(f"Positions tab creation failed: {e}")
    
    def create_logs_tab(self):
        """Create logs and diagnostics tab"""
        try:
            logs = QWidget()
            layout = QVBoxLayout(logs)
            
            # Log controls
            controls_layout = QHBoxLayout()
            
            self.clear_logs_btn = QPushButton("🗑️ Clear Logs")
            self.export_logs_btn = QPushButton("📥 Export Logs")
            self.diagnostic_btn = QPushButton("🩺 Run Diagnostic")
            self.diagnostic_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; }")
            
            controls_layout.addWidget(self.clear_logs_btn)
            controls_layout.addWidget(self.export_logs_btn)
            controls_layout.addWidget(self.diagnostic_btn)
            controls_layout.addStretch()
            
            layout.addLayout(controls_layout)
            
            # Log display - gunakan QPlainTextEdit untuk setMaximumBlockCount
            self.log_display = QPlainTextEdit()
            self.log_display.setReadOnly(True)
            self.log_display.setFont(QFont("Courier New", 10))
            self.log_display.setMaximumBlockCount(1000)  # Limit log lines
            
            layout.addWidget(self.log_display)
            
            # Connect signals
            self.clear_logs_btn.clicked.connect(self.on_clear_logs)
            self.export_logs_btn.clicked.connect(self.on_export_logs)
            self.diagnostic_btn.clicked.connect(self.on_run_diagnostic)
            
            self.tab_widget.addTab(logs, "📝 Logs")
            
        except Exception as e:
            raise Exception(f"Logs tab creation failed: {e}")
    
    def create_simple_logs_tab(self):
        """Create simple fallback logs tab jika terjadi error"""
        try:
            logs = QWidget()
            layout = QVBoxLayout(logs)
            
            # Simple log display tanpa fitur advanced
            self.log_display = QTextEdit()
            self.log_display.setReadOnly(True)
            self.log_display.setFont(QFont("Courier New", 10))
            
            # Basic controls
            controls_layout = QHBoxLayout()
            self.clear_logs_btn = QPushButton("Clear Logs")
            self.clear_logs_btn.clicked.connect(lambda: self.log_display.clear())
            controls_layout.addWidget(self.clear_logs_btn)
            controls_layout.addStretch()
            
            layout.addLayout(controls_layout)
            layout.addWidget(self.log_display)
            
            self.tab_widget.addTab(logs, "Logs (Simple)")
            
        except Exception as e:
            print(f"Simple logs tab creation failed: {e}")
    
    def create_tools_tab(self):
        """Create tools and utilities tab"""
        try:
            tools = QWidget()
            layout = QVBoxLayout(tools)
            
            # Session settings
            session_group = QGroupBox("🌍 Trading Session Settings")
            session_layout = QFormLayout(session_group)
            
            self.session_enabled_cb = QCheckBox("Enable session filter")
            self.session_enabled_cb.setChecked(True)
            
            self.london_start_time = QLineEdit("15:00")
            self.london_end_time = QLineEdit("18:00")
            self.ny_start_time = QLineEdit("20:00")
            self.ny_end_time = QLineEdit("23:59")
            
            session_layout.addRow("", self.session_enabled_cb)
            session_layout.addRow("🇬🇧 London Start (Jakarta):", self.london_start_time)
            session_layout.addRow("🇬🇧 London End (Jakarta):", self.london_end_time)
            session_layout.addRow("🇺🇸 NY Start (Jakarta):", self.ny_start_time)
            session_layout.addRow("🇺🇸 NY End (Jakarta):", self.ny_end_time)
            
            # Magic number setting
            magic_group = QGroupBox("🎭 Magic Number")
            magic_layout = QFormLayout(magic_group)
            
            self.magic_number_spin = QSpinBox()
            self.magic_number_spin.setRange(100000, 999999)
            self.magic_number_spin.setValue(234567)
            
            magic_layout.addRow("🔢 Magic Number:", self.magic_number_spin)
            
            # Deviation setting
            deviation_group = QGroupBox("📏 Order Deviation")
            deviation_layout = QFormLayout(deviation_group)
            
            self.deviation_spin = QSpinBox()
            self.deviation_spin.setRange(1, 100)
            self.deviation_spin.setValue(10)
            self.deviation_spin.setSuffix(" points")
            
            deviation_layout.addRow("📊 Price Deviation:", self.deviation_spin)
            
            # Advanced controls
            advanced_group = QGroupBox("🔧 Advanced Controls")
            advanced_layout = QVBoxLayout(advanced_group)
            
            self.force_update_btn = QPushButton("🔄 Force Data Update")
            self.reset_counters_btn = QPushButton("🔃 Reset Daily Counters")
            self.test_signal_btn = QPushButton("🧪 Generate Test Signal")
            
            advanced_layout.addWidget(self.force_update_btn)
            advanced_layout.addWidget(self.reset_counters_btn)
            advanced_layout.addWidget(self.test_signal_btn)
            
            # Layout
            layout.addWidget(session_group)
            layout.addWidget(magic_group)
            layout.addWidget(deviation_group)
            layout.addWidget(advanced_group)
            layout.addStretch()
            
            self.tab_widget.addTab(tools, "🔧 Tools")
            
        except Exception as e:
            raise Exception(f"Tools tab creation failed: {e}")
    
    def setup_status_bar(self):
        """Setup status bar"""
        try:
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            
            # Status indicators
            self.conn_indicator = QLabel("⚪ Disconnected")
            self.bot_indicator = QLabel("⚪ Stopped")
            self.mode_indicator = QLabel("🔒 Shadow")
            
            self.status_bar.addWidget(QLabel("Connection:"))
            self.status_bar.addWidget(self.conn_indicator)
            self.status_bar.addPermanentWidget(QLabel("Bot:"))
            self.status_bar.addPermanentWidget(self.bot_indicator)
            self.status_bar.addPermanentWidget(QLabel("Mode:"))
            self.status_bar.addPermanentWidget(self.mode_indicator)
            
        except Exception as e:
            print(f"Status bar setup error: {e}")
    
    def connect_signals(self):
        """Connect controller signals to GUI slots"""
        try:
            if self.controller:
                self.controller.signal_log.connect(self.on_log_message)
                self.controller.signal_status.connect(self.on_status_update)
                self.controller.signal_market_data.connect(self.on_market_data_update)
                self.controller.signal_trade_signal.connect(self.on_trade_signal_update)
                self.controller.signal_position_update.connect(self.on_position_update)
                self.controller.signal_account_update.connect(self.on_account_update)
                self.controller.signal_indicators_update.connect(self.on_indicators_update)
                
        except Exception as e:
            print(f"Signal connection error: {e}")
    
    def initialize_displays(self):
        """Initialize display values"""
        try:
            # Set initial values
            self.update_connection_status(False)
            self.update_bot_status(False)
            
            # Symbol warning check
            self.check_symbol_warning()
            
        except Exception as e:
            print(f"Display initialization error: {e}")
    
    # EVENT HANDLERS
    def on_connect(self):
        """Handle connect button"""
        try:
            if self.controller.connect_mt5():
                self.update_connection_status(True)
                self.start_btn.setEnabled(True)
                QMessageBox.information(self, "Connection", "Successfully connected to MT5")
            else:
                QMessageBox.warning(self, "Connection Error", "Failed to connect to MT5")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Connection failed: {e}")
    
    def on_disconnect(self):
        """Handle disconnect button"""
        try:
            self.controller.disconnect_mt5()
            self.update_connection_status(False)
            self.update_bot_status(False)
            self.start_btn.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Disconnect Error", f"Disconnect failed: {e}")
    
    def on_start_bot(self):
        """Handle start bot button"""
        try:
            # Update configuration from GUI
            self.update_controller_config()
            
            if self.controller.start_bot():
                self.update_bot_status(True)
                QMessageBox.information(self, "Bot Started", "Trading bot started successfully")
            else:
                QMessageBox.warning(self, "Start Error", "Failed to start bot")
        except Exception as e:
            QMessageBox.critical(self, "Start Error", f"Bot start failed: {e}")
    
    def on_stop_bot(self):
        """Handle stop bot button"""
        try:
            self.controller.stop_bot()
            self.update_bot_status(False)
        except Exception as e:
            QMessageBox.critical(self, "Stop Error", f"Bot stop failed: {e}")
    
    def on_emergency_stop(self):
        """Handle emergency stop button"""
        try:
            reply = QMessageBox.question(self, "Emergency Stop", 
                                       "This will close ALL positions and stop the bot. Continue?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.controller.close_all_positions()
        except Exception as e:
            QMessageBox.critical(self, "Emergency Stop Error", f"Emergency stop failed: {e}")
    
    def on_shadow_mode_toggle(self, checked):
        """Handle shadow mode toggle"""
        try:
            self.controller.shadow_mode = checked
            self.mode_indicator.setText("🔒 Shadow" if checked else "⚡ Live")
            self.mode_indicator.setStyleSheet(f"QLabel {{ color: {'orange' if checked else 'red'}; }}")
        except Exception as e:
            print(f"Shadow mode toggle error: {e}")
    
    def on_symbol_changed(self, symbol):
        """Handle symbol change"""
        try:
            self.controller.set_config('symbol', symbol)
            self.check_symbol_warning()
        except Exception as e:
            print(f"Symbol change error: {e}")
    
    def on_tpsl_mode_changed(self, mode):
        """Handle TP/SL mode change - KRUSIAL"""
        try:
            self.setup_tpsl_inputs(mode)
            self.controller.set_config('tp_sl_mode', mode)
        except Exception as e:
            print(f"TP/SL mode change error: {e}")
    
    def on_close_selected_position(self):
        """Handle close selected position"""
        try:
            current_row = self.positions_table.currentRow()
            if current_row >= 0:
                ticket_item = self.positions_table.item(current_row, 0)
                if ticket_item:
                    ticket = int(ticket_item.text())
                    self.controller.close_position(ticket)
        except Exception as e:
            QMessageBox.critical(self, "Close Position Error", f"Failed to close position: {e}")
    
    def on_close_all_positions(self):
        """Handle close all positions"""
        try:
            reply = QMessageBox.question(self, "Close All Positions", 
                                       "Close ALL open positions?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.controller.close_all_positions()
        except Exception as e:
            QMessageBox.critical(self, "Close All Error", f"Failed to close positions: {e}")
    
    def on_refresh_positions(self):
        """Handle refresh positions"""
        try:
            self.controller.update_positions()
        except Exception as e:
            print(f"Refresh positions error: {e}")
    
    def on_clear_logs(self):
        """Handle clear logs"""
        try:
            self.log_display.clear()
        except Exception as e:
            print(f"Clear logs error: {e}")
    
    def on_export_logs(self):
        """Handle export logs"""
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Export Logs", "logs_export.csv", "CSV files (*.csv)")
            if filename:
                if self.controller.export_logs(filename):
                    QMessageBox.information(self, "Export", "Logs exported successfully")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export logs: {e}")
    
    def on_run_diagnostic(self):
        """Handle run diagnostic"""
        try:
            self.controller.diagnostic_check()
        except Exception as e:
            print(f"Diagnostic error: {e}")
    
    # SIGNAL HANDLERS (dari controller)
    @Slot(str, str)
    def on_log_message(self, message, level):
        """Handle log message dari controller"""
        try:
            # Color berdasarkan level
            color_map = {
                'INFO': 'black',
                'WARNING': 'orange', 
                'ERROR': 'red',
                'DEBUG': 'blue'
            }
            
            color = color_map.get(level, 'black')
            formatted = f'<span style="color: {color};">[{level}] {message}</span>'
            
            self.log_display.append(formatted)
            
            # Auto-scroll to bottom
            cursor = self.log_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_display.setTextCursor(cursor)
            
        except Exception as e:
            print(f"Log message error: {e}")
    
    @Slot(str)
    def on_status_update(self, status):
        """Handle status update dari controller"""
        try:
            self.status_bar.showMessage(status, 5000)
        except Exception as e:
            print(f"Status update error: {e}")
    
    @Slot(dict)
    def on_market_data_update(self, data):
        """Handle market data update"""
        try:
            if 'bid' in data and 'ask' in data:
                self.bid_label.setText(f"{data['bid']:.5f}")
                self.ask_label.setText(f"{data['ask']:.5f}")
                
            if 'spread_points' in data:
                self.spread_label.setText(f"{data['spread_points']} pts")
                
                # Update spread status
                max_spread = self.controller.config['max_spread_points']
                spread_ok = data['spread_points'] <= max_spread
                self.spread_status.setText("✅ OK" if spread_ok else "❌ Wide")
                self.spread_status.setStyleSheet(f"QLabel {{ color: {'green' if spread_ok else 'red'}; }}")
            
            if 'time' in data:
                self.last_update_label.setText(data['time'].strftime('%H:%M:%S'))
                
        except Exception as e:
            print(f"Market data update error: {e}")
    
    @Slot(dict)
    def on_trade_signal_update(self, signal):
        """Handle trade signal update"""
        try:
            if signal.get('side'):
                self.signal_side_label.setText(signal['side'])
                self.signal_side_label.setStyleSheet(f"QLabel {{ color: {'green' if signal['side'] == 'BUY' else 'red'}; font-weight: bold; }}")
                
            if 'entry_price' in signal:
                self.signal_price_label.setText(f"{signal['entry_price']:.5f}")
                
            if 'reason' in signal:
                self.signal_reason_label.setText(signal['reason'])
                
            if 'timestamp' in signal:
                self.signal_timestamp_label.setText(signal['timestamp'].strftime('%H:%M:%S'))
                
        except Exception as e:
            print(f"Signal update error: {e}")
    
    @Slot(list)
    def on_position_update(self, positions):
        """Handle position update"""
        try:
            # Clear table
            self.positions_table.setRowCount(0)
            
            total_volume = 0.0
            total_profit = 0.0
            
            # Populate table
            for i, pos in enumerate(positions):
                self.positions_table.insertRow(i)
                
                # Populate cells
                self.positions_table.setItem(i, 0, QTableWidgetItem(str(pos['ticket'])))
                self.positions_table.setItem(i, 1, QTableWidgetItem("BUY" if pos['type'] == 0 else "SELL"))
                self.positions_table.setItem(i, 2, QTableWidgetItem(f"{pos['volume']:.2f}"))
                self.positions_table.setItem(i, 3, QTableWidgetItem(f"{pos['price_open']:.5f}"))
                self.positions_table.setItem(i, 4, QTableWidgetItem(f"{pos.get('sl', 0):.5f}"))
                self.positions_table.setItem(i, 5, QTableWidgetItem(f"{pos.get('tp', 0):.5f}"))
                
                profit = pos.get('profit', 0)
                profit_item = QTableWidgetItem(f"${profit:.2f}")
                profit_item.setForeground(QColor('green' if profit >= 0 else 'red'))
                self.positions_table.setItem(i, 6, profit_item)
                
                # Close button
                close_btn = QPushButton("❌")
                close_btn.clicked.connect(lambda checked, ticket=pos['ticket']: self.controller.close_position(ticket))
                self.positions_table.setCellWidget(i, 7, close_btn)
                
                total_volume += pos['volume']
                total_profit += profit
            
            # Update summary
            self.total_positions_label.setText(str(len(positions)))
            self.total_volume_label.setText(f"{total_volume:.2f}")
            self.total_profit_label.setText(f"${total_profit:.2f}")
            self.floating_pnl_label.setText(f"${total_profit:.2f}")
            
            # Auto-resize columns
            self.positions_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Position update error: {e}")
    
    @Slot(dict)
    def on_account_update(self, account):
        """Handle account update"""
        try:
            if 'balance' in account:
                self.balance_label.setText(f"${account['balance']:.2f}")
                
            if 'equity' in account:
                self.equity_label.setText(f"${account['equity']:.2f}")
                
            if 'margin' in account:
                self.margin_label.setText(f"${account.get('margin', 0):.2f}")
                
            if 'profit' in account:
                profit = account['profit']
                self.pnl_label.setText(f"${profit:.2f}")
                self.pnl_label.setStyleSheet(f"QLabel {{ color: {'green' if profit >= 0 else 'red'}; }}")
                
            # Calculate margin level
            margin = account.get('margin', 1)
            if margin > 0:
                margin_level = (account.get('equity', 0) / margin) * 100
                self.margin_level_label.setText(f"{margin_level:.1f}%")
            
        except Exception as e:
            print(f"Account update error: {e}")
    
    @Slot(dict)
    def on_indicators_update(self, indicators):
        """Handle indicators update"""
        try:
            # Update M1 indicators
            if 'M1' in indicators:
                m1 = indicators['M1']
                self.ema_fast_m1_label.setText(f"{m1.get('ema_fast', 0):.5f}")
                self.ema_medium_m1_label.setText(f"{m1.get('ema_medium', 0):.5f}")
                self.ema_slow_m1_label.setText(f"{m1.get('ema_slow', 0):.5f}")
                self.rsi_m1_label.setText(f"{m1.get('rsi', 50):.2f}")
                self.atr_m1_label.setText(f"{m1.get('atr', 0):.5f}")
            
            # Update M5 indicators
            if 'M5' in indicators:
                m5 = indicators['M5']
                self.ema_fast_m5_label.setText(f"{m5.get('ema_fast', 0):.5f}")
                self.ema_medium_m5_label.setText(f"{m5.get('ema_medium', 0):.5f}")
                self.ema_slow_m5_label.setText(f"{m5.get('ema_slow', 0):.5f}")
                self.rsi_m5_label.setText(f"{m5.get('rsi', 50):.2f}")
                self.atr_m5_label.setText(f"{m5.get('atr', 0):.5f}")
                
        except Exception as e:
            print(f"Indicators update error: {e}")
    
    # UTILITY METHODS
    def update_controller_config(self):
        """Update controller configuration dari GUI inputs"""
        try:
            # Basic config
            self.controller.set_config('symbol', self.symbol_combo.currentText())
            self.controller.set_config('risk_percent', self.risk_percent_spin.value())
            self.controller.set_config('max_daily_loss', self.max_daily_loss_spin.value())
            self.controller.set_config('max_trades_per_day', self.max_trades_spin.value())
            self.controller.set_config('max_spread_points', self.max_spread_spin.value())
            
            # Strategy config
            self.controller.config['ema_periods'] = {
                'fast': self.ema_fast_spin.value(),
                'medium': self.ema_medium_spin.value(),
                'slow': self.ema_slow_spin.value()
            }
            self.controller.set_config('rsi_period', self.rsi_period_spin.value())
            self.controller.set_config('atr_period', self.atr_period_spin.value())
            self.controller.set_config('use_rsi_filter', self.rsi_filter_cb.isChecked())
            
            # TP/SL config - KRUSIAL
            mode = self.tpsl_mode_combo.currentText()
            self.controller.set_config('tp_sl_mode', mode)
            
            # Update TP/SL values berdasarkan mode
            for key, widget in self.tp_sl_inputs.items():
                if hasattr(widget, 'value'):
                    self.controller.set_config(key, widget.value())
            
            # Shadow mode
            self.controller.shadow_mode = self.shadow_mode_cb.isChecked()
            
        except Exception as e:
            print(f"Config update error: {e}")
    
    def update_connection_status(self, connected):
        """Update connection status indicators"""
        try:
            if connected:
                self.connection_status.setText("🟢 Connected")
                self.conn_indicator.setText("🟢 Connected")
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(True)
                self.emergency_stop_btn.setEnabled(True)
            else:
                self.connection_status.setText("⚪ Disconnected")
                self.conn_indicator.setText("⚪ Disconnected")
                self.connect_btn.setEnabled(True)
                self.disconnect_btn.setEnabled(False)
                self.start_btn.setEnabled(False)
                self.emergency_stop_btn.setEnabled(False)
                
        except Exception as e:
            print(f"Connection status update error: {e}")
    
    def update_bot_status(self, running):
        """Update bot status indicators"""
        try:
            if running:
                self.bot_status.setText("🟢 Running")
                self.bot_indicator.setText("🟢 Running")
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.manual_buy_btn.setEnabled(not self.shadow_mode_cb.isChecked())
                self.manual_sell_btn.setEnabled(not self.shadow_mode_cb.isChecked())
            else:
                self.bot_status.setText("⚪ Stopped")
                self.bot_indicator.setText("⚪ Stopped")
                self.start_btn.setEnabled(self.controller.is_connected)
                self.stop_btn.setEnabled(False)
                self.manual_buy_btn.setEnabled(False)
                self.manual_sell_btn.setEnabled(False)
                
        except Exception as e:
            print(f"Bot status update error: {e}")
    
    def check_symbol_warning(self):
        """Check dan tampilkan warning untuk non-XAU symbols"""
        try:
            symbol = self.symbol_combo.currentText()
            if not symbol.startswith('XAU'):
                warning_text = "⚠️ Strategy optimized for XAU symbols. Parameters may need adjustment for other pairs."
                self.symbol_warning.setText(warning_text)
            else:
                self.symbol_warning.setText("")
        except Exception as e:
            print(f"Symbol warning check error: {e}")
    
    def update_gui_data(self):
        """Update GUI data periodically"""
        try:
            # Update daily stats
            if hasattr(self.controller, 'daily_trades'):
                self.daily_trades_label.setText(str(self.controller.daily_trades))
                self.daily_pnl_label.setText(f"${self.controller.daily_pnl:.2f}")
                self.consecutive_losses_label.setText(str(self.controller.consecutive_losses))
            
            # Update session status
            if hasattr(self.controller.analysis_worker, 'is_trading_session'):
                session_ok = self.controller.analysis_worker.is_trading_session()
                self.session_status.setText("✅ Active" if session_ok else "❌ Closed")
                self.session_status.setStyleSheet(f"QLabel {{ color: {'green' if session_ok else 'red'}; }}")
            
            # Update risk status
            risk_ok = self.controller.check_risk_limits() if hasattr(self.controller, 'check_risk_limits') else True
            self.risk_status.setText("✅ OK" if risk_ok else "❌ Limit Hit")
            self.risk_status.setStyleSheet(f"QLabel {{ color: {'green' if risk_ok else 'red'}; }}")
            
        except Exception as e:
            pass  # Silent fail untuk GUI updates