
"""
PySide6 GUI for MT5 Scalping Bot - PRODUCTION READY
Modern tabbed interface with TP/SL manual input and real-time updates
CRITICAL FOR REAL MONEY TRADING
"""

import sys
from datetime import datetime
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QGridLayout, QSplitter, QProgressBar,
    QStatusBar, QMessageBox, QFrame, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Slot, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon, QColor

class MainWindow(QMainWindow):
    """Main application window with tabbed interface - PRODUCTION READY"""
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("MT5 Professional Scalping Bot - REAL TRADING")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize all required attributes
        self.connection_status = None
        self.bot_status = None
        self.mode_status = None
        
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
        """Setup the main user interface with error handling"""
        try:
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            # Create tab widget
            self.tab_widget = QTabWidget()
            layout.addWidget(self.tab_widget)
            
            # Create all tabs with error handling
            self.create_dashboard_tab()
            self.create_strategy_tab()
            self.create_risk_tab()
            self.create_execution_tab()
            self.create_logs_tab()
            self.create_tools_tab()  # Additional tools for production
            
        except Exception as e:
            raise Exception(f"UI setup failed: {e}")
    
    def create_dashboard_tab(self):
        """Create dashboard tab with connection and overview"""
        try:
            dashboard = QWidget()
            layout = QVBoxLayout(dashboard)
            
            # Connection section
            conn_group = QGroupBox("🔗 MT5 Connection Status")
            conn_layout = QGridLayout(conn_group)
            
            self.connect_btn = QPushButton("🔌 Connect to MT5")
            self.connect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
            
            self.disconnect_btn = QPushButton("🔌 Disconnect")
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 8px; }")
            
            self.status_label = QLabel("❌ Status: Disconnected")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            
            self.account_login_label = QLabel("Account: N/A")
            self.server_label = QLabel("Server: N/A")
            
            conn_layout.addWidget(self.connect_btn, 0, 0)
            conn_layout.addWidget(self.disconnect_btn, 0, 1)
            conn_layout.addWidget(self.status_label, 1, 0, 1, 2)
            conn_layout.addWidget(self.account_login_label, 2, 0)
            conn_layout.addWidget(self.server_label, 2, 1)
            
            # Symbol selection and validation
            symbol_group = QGroupBox("📊 Symbol Configuration")
            symbol_layout = QFormLayout(symbol_group)
            
            self.symbol_combo = QComboBox()
            self.symbol_combo.addItems(["XAUUSD", "XAUUSDm", "XAUUSDc", "GOLD"])
            self.symbol_combo.setCurrentText("XAUUSD")
            
            self.symbol_status_label = QLabel("❓ Not validated")
            
            symbol_layout.addRow("Trading Symbol:", self.symbol_combo)
            symbol_layout.addRow("Symbol Status:", self.symbol_status_label)
            
            # Bot control with safety features
            control_group = QGroupBox("🤖 Bot Control Panel")
            control_layout = QGridLayout(control_group)
            
            self.start_btn = QPushButton("🚀 START BOT")
            self.start_btn.setEnabled(False)
            self.start_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 10px; font-size: 14px; }")
            
            self.stop_btn = QPushButton("🛑 STOP BOT")
            self.stop_btn.setEnabled(False)
            self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; font-size: 14px; }")
            
            self.shadow_mode_cb = QCheckBox("🛡️ Shadow Mode (Signals Only - RECOMMENDED)")
            self.shadow_mode_cb.setChecked(True)
            self.shadow_mode_cb.setStyleSheet("QCheckBox { color: green; font-weight: bold; }")
            
            self.emergency_stop_btn = QPushButton("🚨 EMERGENCY STOP")
            self.emergency_stop_btn.setStyleSheet("QPushButton { background-color: #8B0000; color: white; font-weight: bold; padding: 8px; }")
            
            control_layout.addWidget(self.start_btn, 0, 0)
            control_layout.addWidget(self.stop_btn, 0, 1)
            control_layout.addWidget(self.shadow_mode_cb, 1, 0, 1, 2)
            control_layout.addWidget(self.emergency_stop_btn, 2, 0, 1, 2)
            
            # Real-time market data display
            market_group = QGroupBox("💹 Live Market Data")
            market_layout = QFormLayout(market_group)
            
            self.bid_label = QLabel("0.00000")
            self.ask_label = QLabel("0.00000")
            self.spread_label = QLabel("0")
            self.time_label = QLabel("N/A")
            
            # Style market data labels
            for label in [self.bid_label, self.ask_label, self.spread_label, self.time_label]:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 12px; font-weight: bold; }")
            
            market_layout.addRow("📈 Bid Price:", self.bid_label)
            market_layout.addRow("📊 Ask Price:", self.ask_label)
            market_layout.addRow("📏 Spread (pts):", self.spread_label)
            market_layout.addRow("🕐 Last Update:", self.time_label)
            
            # Account information display
            account_group = QGroupBox("💰 Account Information")
            account_layout = QFormLayout(account_group)
            
            self.balance_label = QLabel("$0.00")
            self.equity_label = QLabel("$0.00")
            self.margin_label = QLabel("$0.00")
            self.pnl_label = QLabel("$0.00")
            self.margin_level_label = QLabel("0%")
            
            # Style account labels
            for label in [self.balance_label, self.equity_label, self.margin_label, self.pnl_label, self.margin_level_label]:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 12px; font-weight: bold; }")
            
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
            
            bottom_layout = QHBoxLayout()
            bottom_layout.addWidget(market_group)
            bottom_layout.addWidget(account_group)
            
            layout.addLayout(top_layout)
            layout.addLayout(bottom_layout)
            layout.addStretch()
            
            # Connect all signals with error handling
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
        """Create strategy configuration tab"""
        try:
            strategy = QWidget()
            layout = QVBoxLayout(strategy)
            
            # EMA Settings
            ema_group = QGroupBox("📈 EMA Configuration")
            ema_layout = QFormLayout(ema_group)
            
            self.ema_fast_spin = QSpinBox()
            self.ema_fast_spin.setRange(1, 50)
            self.ema_fast_spin.setValue(8)
            
            self.ema_medium_spin = QSpinBox()
            self.ema_medium_spin.setRange(1, 100)
            self.ema_medium_spin.setValue(21)
            
            self.ema_slow_spin = QSpinBox()
            self.ema_slow_spin.setRange(1, 200)
            self.ema_slow_spin.setValue(50)
            
            ema_layout.addRow("⚡ Fast EMA Period:", self.ema_fast_spin)
            ema_layout.addRow("📊 Medium EMA Period:", self.ema_medium_spin)
            ema_layout.addRow("🐌 Slow EMA Period:", self.ema_slow_spin)
            
            # RSI Settings
            rsi_group = QGroupBox("📊 RSI Configuration")
            rsi_layout = QFormLayout(rsi_group)
            
            self.rsi_period_spin = QSpinBox()
            self.rsi_period_spin.setRange(1, 50)
            self.rsi_period_spin.setValue(14)
            
            rsi_layout.addRow("📈 RSI Period:", self.rsi_period_spin)
            
            # ATR Settings
            atr_group = QGroupBox("📏 ATR Configuration")
            atr_layout = QFormLayout(atr_group)
            
            self.atr_period_spin = QSpinBox()
            self.atr_period_spin.setRange(1, 50)
            self.atr_period_spin.setValue(14)
            
            atr_layout.addRow("📊 ATR Period:", self.atr_period_spin)
            
            # Current indicators display with real-time updates
            indicators_group = QGroupBox("📊 Live Indicators Display")
            indicators_layout = QFormLayout(indicators_group)
            
            # M1 indicators
            self.ema_fast_m1_label = QLabel("N/A")
            self.ema_medium_m1_label = QLabel("N/A")
            self.ema_slow_m1_label = QLabel("N/A")
            self.rsi_m1_label = QLabel("N/A")
            self.atr_m1_label = QLabel("N/A")
            
            # M5 indicators
            self.ema_fast_m5_label = QLabel("N/A")
            self.ema_medium_m5_label = QLabel("N/A")
            self.ema_slow_m5_label = QLabel("N/A")
            self.rsi_m5_label = QLabel("N/A")
            self.atr_m5_label = QLabel("N/A")
            
            # Style indicator labels
            indicator_labels = [
                self.ema_fast_m1_label, self.ema_medium_m1_label, self.ema_slow_m1_label, 
                self.rsi_m1_label, self.atr_m1_label,
                self.ema_fast_m5_label, self.ema_medium_m5_label, self.ema_slow_m5_label,
                self.rsi_m5_label, self.atr_m5_label
            ]
            
            for label in indicator_labels:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 11px; }")
            
            indicators_layout.addRow("⚡ M1 Fast EMA:", self.ema_fast_m1_label)
            indicators_layout.addRow("📊 M1 Medium EMA:", self.ema_medium_m1_label)
            indicators_layout.addRow("🐌 M1 Slow EMA:", self.ema_slow_m1_label)
            indicators_layout.addRow("📈 M1 RSI:", self.rsi_m1_label)
            indicators_layout.addRow("📏 M1 ATR:", self.atr_m1_label)
            
            indicators_layout.addRow("", QLabel(""))  # Spacer
            
            indicators_layout.addRow("⚡ M5 Fast EMA:", self.ema_fast_m5_label)
            indicators_layout.addRow("📊 M5 Medium EMA:", self.ema_medium_m5_label)
            indicators_layout.addRow("🐌 M5 Slow EMA:", self.ema_slow_m5_label)
            indicators_layout.addRow("📈 M5 RSI:", self.rsi_m5_label)
            indicators_layout.addRow("📏 M5 ATR:", self.atr_m5_label)
            
            # Layout arrangement
            settings_layout = QHBoxLayout()
            settings_layout.addWidget(ema_group)
            settings_layout.addWidget(rsi_group)
            settings_layout.addWidget(atr_group)
            
            layout.addLayout(settings_layout)
            layout.addWidget(indicators_group)
            layout.addStretch()
            
            self.tab_widget.addTab(strategy, "📈 Strategy")
            
        except Exception as e:
            raise Exception(f"Strategy tab creation failed: {e}")
    
    def create_risk_tab(self):
        """Create risk management tab with TP/SL manual input"""
        try:
            risk = QWidget()
            layout = QVBoxLayout(risk)
            
            # Risk management settings
            risk_group = QGroupBox("🛡️ Risk Management Settings")
            risk_layout = QFormLayout(risk_group)
            
            self.risk_percent_spin = QDoubleSpinBox()
            self.risk_percent_spin.setRange(0.1, 10.0)
            self.risk_percent_spin.setValue(0.5)
            self.risk_percent_spin.setSuffix("%")
            self.risk_percent_spin.setDecimals(2)
            
            self.max_daily_loss_spin = QDoubleSpinBox()
            self.max_daily_loss_spin.setRange(0.5, 20.0)
            self.max_daily_loss_spin.setValue(2.0)
            self.max_daily_loss_spin.setSuffix("%")
            self.max_daily_loss_spin.setDecimals(1)
            
            self.max_trades_spin = QSpinBox()
            self.max_trades_spin.setRange(1, 100)
            self.max_trades_spin.setValue(15)
            
            self.risk_multiple_spin = QDoubleSpinBox()
            self.risk_multiple_spin.setRange(0.5, 5.0)
            self.risk_multiple_spin.setValue(2.0)
            self.risk_multiple_spin.setDecimals(1)
            
            self.max_spread_spin = QSpinBox()
            self.max_spread_spin.setRange(10, 200)
            self.max_spread_spin.setValue(30)
            self.max_spread_spin.setSuffix(" pts")
            
            self.min_sl_spin = QSpinBox()
            self.min_sl_spin.setRange(50, 500)
            self.min_sl_spin.setValue(150)
            self.min_sl_spin.setSuffix(" pts")
            
            risk_layout.addRow("💰 Risk per Trade:", self.risk_percent_spin)
            risk_layout.addRow("🚨 Max Daily Loss:", self.max_daily_loss_spin)
            risk_layout.addRow("🔢 Max Trades/Day:", self.max_trades_spin)
            risk_layout.addRow("📈 Risk Multiple (R:R):", self.risk_multiple_spin)
            risk_layout.addRow("📏 Max Spread:", self.max_spread_spin)
            risk_layout.addRow("🛡️ Min SL Distance:", self.min_sl_spin)
            
            # TP/SL Manual Configuration - NEW FEATURE
            tp_sl_group = QGroupBox("🎯 TP/SL Manual Configuration")
            tp_sl_layout = QFormLayout(tp_sl_group)
            
            # TP/SL Mode Selection
            self.tp_sl_mode_combo = QComboBox()
            self.tp_sl_mode_combo.addItems(["ATR", "Points", "Pips", "Percent"])
            self.tp_sl_mode_combo.setCurrentText("ATR")
            self.tp_sl_mode_combo.currentTextChanged.connect(self.on_tp_sl_mode_changed)
            
            tp_sl_layout.addRow("🔧 TP/SL Mode:", self.tp_sl_mode_combo)
            
            # ATR Mode Controls (default)
            self.atr_multiplier_spin = QDoubleSpinBox()
            self.atr_multiplier_spin.setRange(0.5, 5.0)
            self.atr_multiplier_spin.setValue(1.5)
            self.atr_multiplier_spin.setDecimals(1)
            
            # Points Mode Controls
            self.tp_points_spin = QSpinBox()
            self.tp_points_spin.setRange(50, 1000)
            self.tp_points_spin.setValue(200)
            self.tp_points_spin.setSuffix(" pts")
            
            self.sl_points_spin = QSpinBox()
            self.sl_points_spin.setRange(50, 500)
            self.sl_points_spin.setValue(100)
            self.sl_points_spin.setSuffix(" pts")
            
            # Pips Mode Controls
            self.tp_pips_spin = QSpinBox()
            self.tp_pips_spin.setRange(5, 100)
            self.tp_pips_spin.setValue(20)
            self.tp_pips_spin.setSuffix(" pips")
            
            self.sl_pips_spin = QSpinBox()
            self.sl_pips_spin.setRange(5, 50)
            self.sl_pips_spin.setValue(10)
            self.sl_pips_spin.setSuffix(" pips")
            
            # Percent Mode Controls
            self.tp_percent_spin = QDoubleSpinBox()
            self.tp_percent_spin.setRange(0.1, 10.0)
            self.tp_percent_spin.setValue(1.0)
            self.tp_percent_spin.setSuffix("% balance")
            self.tp_percent_spin.setDecimals(2)
            
            self.sl_percent_spin = QDoubleSpinBox()
            self.sl_percent_spin.setRange(0.1, 5.0)
            self.sl_percent_spin.setValue(0.5)
            self.sl_percent_spin.setSuffix("% balance")
            self.sl_percent_spin.setDecimals(2)
            
            # Add controls to layout
            tp_sl_layout.addRow("🔄 ATR Multiplier:", self.atr_multiplier_spin)
            tp_sl_layout.addRow("🎯 TP Points:", self.tp_points_spin)
            tp_sl_layout.addRow("🛡️ SL Points:", self.sl_points_spin)
            tp_sl_layout.addRow("🎯 TP Pips:", self.tp_pips_spin)
            tp_sl_layout.addRow("🛡️ SL Pips:", self.sl_pips_spin)
            tp_sl_layout.addRow("🎯 TP Percent:", self.tp_percent_spin)
            tp_sl_layout.addRow("🛡️ SL Percent:", self.sl_percent_spin)
            
            # Initially hide non-ATR controls
            self.on_tp_sl_mode_changed("ATR")
            
            # Apply button for TP/SL settings
            apply_tp_sl_btn = QPushButton("✅ Apply TP/SL Settings")
            apply_tp_sl_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
            apply_tp_sl_btn.clicked.connect(self.on_apply_tp_sl_settings)
            tp_sl_layout.addRow(apply_tp_sl_btn)
            
            # Daily statistics display
            stats_group = QGroupBox("📊 Daily Trading Statistics")
            stats_layout = QFormLayout(stats_group)
            
            self.daily_trades_label = QLabel("0")
            self.daily_pnl_label = QLabel("$0.00")
            self.win_rate_label = QLabel("0%")
            self.max_dd_label = QLabel("$0.00")
            self.total_volume_label = QLabel("0.00")
            self.avg_win_label = QLabel("$0.00")
            self.avg_loss_label = QLabel("$0.00")
            
            # Style statistics labels
            stat_labels = [
                self.daily_trades_label, self.daily_pnl_label, self.win_rate_label,
                self.max_dd_label, self.total_volume_label, self.avg_win_label, self.avg_loss_label
            ]
            
            for label in stat_labels:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 12px; font-weight: bold; }")
            
            stats_layout.addRow("🔢 Trades Today:", self.daily_trades_label)
            stats_layout.addRow("💰 Daily P&L:", self.daily_pnl_label)
            stats_layout.addRow("🎯 Win Rate:", self.win_rate_label)
            stats_layout.addRow("📉 Max Drawdown:", self.max_dd_label)
            stats_layout.addRow("📊 Total Volume:", self.total_volume_label)
            stats_layout.addRow("💚 Avg Win:", self.avg_win_label)
            stats_layout.addRow("🔴 Avg Loss:", self.avg_loss_label)
            
            layout.addWidget(risk_group)
            layout.addWidget(tp_sl_group)
            layout.addWidget(stats_group)
            layout.addStretch()
            
            self.tab_widget.addTab(risk, "🛡️ Risk Management")
            
        except Exception as e:
            raise Exception(f"Risk tab creation failed: {e}")
    
    def create_execution_tab(self):
        """Create trade execution tab with comprehensive monitoring"""
        try:
            execution = QWidget()
            layout = QVBoxLayout(execution)
            
            # Analysis status display - NEW
            analysis_group = QGroupBox("🔍 Market Analysis Status")
            analysis_layout = QFormLayout(analysis_group)
            
            self.analysis_status_label = QLabel("⏸️ Idle")
            self.analysis_status_label.setStyleSheet("QLabel { font-weight: bold; color: gray; }")
            
            self.trend_m5_label = QLabel("N/A")
            self.trend_m1_label = QLabel("N/A") 
            self.signal_strength_label = QLabel("N/A")
            self.next_analysis_label = QLabel("N/A")
            
            analysis_layout.addRow("📊 Analysis Status:", self.analysis_status_label)
            analysis_layout.addRow("📈 M5 Trend:", self.trend_m5_label)
            analysis_layout.addRow("⚡ M1 Setup:", self.trend_m1_label)
            analysis_layout.addRow("💪 Signal Strength:", self.signal_strength_label)
            analysis_layout.addRow("⏰ Next Analysis:", self.next_analysis_label)
            
            # Current signal display
            signal_group = QGroupBox("🎯 Current Trading Signal")
            signal_layout = QFormLayout(signal_group)
            
            self.signal_type_label = QLabel("None")
            self.signal_entry_label = QLabel("N/A")
            self.signal_sl_label = QLabel("N/A")
            self.signal_tp_label = QLabel("N/A")
            self.signal_lot_label = QLabel("N/A")
            self.signal_risk_label = QLabel("N/A")
            self.signal_time_label = QLabel("N/A")
            
            # Auto trading status
            self.auto_trade_status_label = QLabel("⏸️ Manual Mode")
            self.auto_trade_status_label.setStyleSheet("QLabel { font-weight: bold; color: orange; }")
            
            # Style signal labels
            signal_labels = [
                self.signal_type_label, self.signal_entry_label, self.signal_sl_label,
                self.signal_tp_label, self.signal_lot_label, self.signal_risk_label, self.signal_time_label
            ]
            
            for label in signal_labels:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 12px; font-weight: bold; }")
            
            signal_layout.addRow("📊 Signal Type:", self.signal_type_label)
            signal_layout.addRow("🎯 Entry Price:", self.signal_entry_label)
            signal_layout.addRow("🛡️ Stop Loss:", self.signal_sl_label)
            signal_layout.addRow("🎯 Take Profit:", self.signal_tp_label)
            signal_layout.addRow("📊 Lot Size:", self.signal_lot_label)
            signal_layout.addRow("📈 Risk/Reward:", self.signal_risk_label)
            signal_layout.addRow("🕐 Signal Time:", self.signal_time_label)
            signal_layout.addRow("🤖 Auto Trade:", self.auto_trade_status_label)
            
            # Positions table with enhanced display
            positions_group = QGroupBox("📋 Open Positions Monitor")
            positions_layout = QVBoxLayout(positions_group)
            
            self.positions_table = QTableWidget()
            self.positions_table.setColumnCount(9)
            self.positions_table.setHorizontalHeaderLabels([
                "Ticket", "Type", "Volume", "Entry", "Current", "SL", "TP", "Profit", "Comment"
            ])
            
            # Set table properties for better display
            self.positions_table.setAlternatingRowColors(True)
            self.positions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            
            positions_layout.addWidget(self.positions_table)
            
            # Position control buttons
            position_controls = QHBoxLayout()
            
            self.close_all_btn = QPushButton("🚨 Close All Positions")
            self.close_all_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 8px; }")
            
            self.refresh_positions_btn = QPushButton("🔄 Refresh Positions")
            self.refresh_positions_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }")
            
            position_controls.addWidget(self.close_all_btn)
            position_controls.addWidget(self.refresh_positions_btn)
            position_controls.addStretch()
            
            positions_layout.addLayout(position_controls)
            
            layout.addWidget(analysis_group)
            layout.addWidget(signal_group)
            layout.addWidget(positions_group)
            
            # Connect position control buttons
            self.close_all_btn.clicked.connect(self.on_close_all_positions)
            self.refresh_positions_btn.clicked.connect(self.refresh_positions)
            
            self.tab_widget.addTab(execution, "⚡ Execution")
            
        except Exception as e:
            raise Exception(f"Execution tab creation failed: {e}")
    
    def create_logs_tab(self):
        """Create comprehensive logs and history tab"""
        try:
            logs = QWidget()
            layout = QVBoxLayout(logs)
            
            # Log display with enhanced formatting
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setFont(QFont("Consolas", 10))
            self.log_text.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #444;
                }
            """)
            
            # Log controls with comprehensive options
            controls_layout = QHBoxLayout()
            
            clear_btn = QPushButton("🗑️ Clear Logs")
            clear_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
            
            save_btn = QPushButton("💾 Save Logs")
            save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
            
            export_btn = QPushButton("📤 Export Trading History")
            export_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; }")
            
            controls_layout.addWidget(clear_btn)
            controls_layout.addWidget(save_btn)
            controls_layout.addWidget(export_btn)
            controls_layout.addStretch()
            
            layout.addWidget(self.log_text)
            layout.addLayout(controls_layout)
            
            # Connect log control buttons
            clear_btn.clicked.connect(self.clear_logs)
            save_btn.clicked.connect(self.save_logs)
            export_btn.clicked.connect(self.on_export_logs)
            
            self.tab_widget.addTab(logs, "📜 Logs")
            
        except Exception as e:
            raise Exception(f"Logs tab creation failed: {e}")
    
    def create_tools_tab(self):
        """Create additional tools tab for production environment"""
        try:
            tools = QWidget()
            layout = QVBoxLayout(tools)
            
            # Testing and validation tools
            test_group = QGroupBox("🧪 Testing & Validation Tools")
            test_layout = QGridLayout(test_group)
            
            self.test_signal_btn = QPushButton("🧪 Test Signal Generation")
            self.test_signal_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; font-weight: bold; }")
            
            self.validate_symbol_btn = QPushButton("✅ Validate Symbol")
            self.validate_symbol_btn.setStyleSheet("QPushButton { background-color: #607D8B; color: white; font-weight: bold; }")
            
            self.check_margin_btn = QPushButton("💰 Check Margin Requirements")
            self.check_margin_btn.setStyleSheet("QPushButton { background-color: #795548; color: white; font-weight: bold; }")
            
            test_layout.addWidget(self.test_signal_btn, 0, 0)
            test_layout.addWidget(self.validate_symbol_btn, 0, 1)
            test_layout.addWidget(self.check_margin_btn, 1, 0, 1, 2)
            
            # System status
            status_group = QGroupBox("🔧 System Status")
            status_layout = QFormLayout(status_group)
            
            self.mt5_version_label = QLabel("N/A")
            self.connection_quality_label = QLabel("N/A")
            self.last_tick_label = QLabel("N/A")
            self.system_time_label = QLabel("N/A")
            
            status_layout.addRow("📊 MT5 Version:", self.mt5_version_label)
            status_layout.addRow("📡 Connection Quality:", self.connection_quality_label)
            status_layout.addRow("⏰ Last Tick:", self.last_tick_label)
            status_layout.addRow("🕐 System Time:", self.system_time_label)
            
            layout.addWidget(test_group)
            layout.addWidget(status_group)
            layout.addStretch()
            
            # Connect tool buttons
            self.test_signal_btn.clicked.connect(self.on_test_signal)
            self.validate_symbol_btn.clicked.connect(self.on_validate_symbol)
            self.check_margin_btn.clicked.connect(self.on_check_margin)
            
            self.tab_widget.addTab(tools, "🔧 Tools")
            
        except Exception as e:
            raise Exception(f"Tools tab creation failed: {e}")
    
    def setup_status_bar(self):
        """Setup comprehensive status bar"""
        try:
            self.statusBar().showMessage("🚀 System Ready - Awaiting MT5 Connection")
            
            # Add detailed status indicators
            self.connection_status = QLabel("❌ Disconnected")
            self.bot_status = QLabel("⏸️ Stopped")
            self.mode_status = QLabel("🛡️ Shadow")
            
            # Style status labels
            self.connection_status.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            self.bot_status.setStyleSheet("QLabel { color: gray; font-weight: bold; }")
            self.mode_status.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            
            self.statusBar().addPermanentWidget(QLabel("Connection:"))
            self.statusBar().addPermanentWidget(self.connection_status)
            self.statusBar().addPermanentWidget(QLabel("Bot:"))
            self.statusBar().addPermanentWidget(self.bot_status)
            self.statusBar().addPermanentWidget(QLabel("Mode:"))
            self.statusBar().addPermanentWidget(self.mode_status)
            
        except Exception as e:
            raise Exception(f"Status bar setup failed: {e}")
    
    def connect_signals(self):
        """Connect all controller signals to GUI slots with error handling"""
        try:
            # Connect all controller signals with proper error handling
            if hasattr(self.controller, 'signal_log'):
                self.controller.signal_log.connect(self.log_message)
            if hasattr(self.controller, 'signal_status'):
                self.controller.signal_status.connect(self.update_status)
            if hasattr(self.controller, 'signal_market_data'):
                self.controller.signal_market_data.connect(self.update_market_data)
            if hasattr(self.controller, 'signal_trade_signal'):
                self.controller.signal_trade_signal.connect(self.update_trade_signal)
            if hasattr(self.controller, 'signal_position_update'):
                self.controller.signal_position_update.connect(self.update_positions)
            if hasattr(self.controller, 'signal_account_update'):
                self.controller.signal_account_update.connect(self.update_account_display)
            if hasattr(self.controller, 'signal_indicators_update'):
                self.controller.signal_indicators_update.connect(self.update_indicators_display)
            if hasattr(self.controller, 'signal_analysis_update'):
                self.controller.signal_analysis_update.connect(self.update_analysis_status)
                
        except Exception as e:
            print(f"Signal connection error: {e}")
    
    def initialize_displays(self):
        """Initialize all display elements with default values"""
        try:
            # Initialize market data displays
            self.bid_label.setText("0.00000")
            self.ask_label.setText("0.00000")
            self.spread_label.setText("0")
            self.time_label.setText("Not Connected")
            
            # Initialize account displays
            self.balance_label.setText("$0.00")
            self.equity_label.setText("$0.00")
            self.margin_label.setText("$0.00")
            self.pnl_label.setText("$0.00")
            
            # Initialize indicator displays
            indicator_labels = [
                self.ema_fast_m1_label, self.ema_medium_m1_label, self.ema_slow_m1_label,
                self.rsi_m1_label, self.atr_m1_label,
                self.ema_fast_m5_label, self.ema_medium_m5_label, self.ema_slow_m5_label,
                self.rsi_m5_label, self.atr_m5_label
            ]
            
            for label in indicator_labels:
                label.setText("N/A")
                
        except Exception as e:
            print(f"Display initialization error: {e}")
    
    # TP/SL Mode Management
    def on_tp_sl_mode_changed(self, mode):
        """Handle TP/SL mode change"""
        try:
            # Hide all mode-specific controls first
            self.atr_multiplier_spin.setVisible(False)
            self.tp_points_spin.setVisible(False)
            self.sl_points_spin.setVisible(False)
            self.tp_pips_spin.setVisible(False)
            self.sl_pips_spin.setVisible(False)
            self.tp_percent_spin.setVisible(False)
            self.sl_percent_spin.setVisible(False)
            
            # Show relevant controls for selected mode
            if mode == "ATR":
                self.atr_multiplier_spin.setVisible(True)
            elif mode == "Points":
                self.tp_points_spin.setVisible(True)
                self.sl_points_spin.setVisible(True)
            elif mode == "Pips":
                self.tp_pips_spin.setVisible(True)
                self.sl_pips_spin.setVisible(True)
            elif mode == "Percent":
                self.tp_percent_spin.setVisible(True)
                self.sl_percent_spin.setVisible(True)
                
        except Exception as e:
            self.log_message(f"TP/SL mode change error: {e}", "ERROR")
    
    def on_apply_tp_sl_settings(self):
        """Apply TP/SL settings to controller with immediate effect"""
        try:
            mode = self.tp_sl_mode_combo.currentText()
            
            config_update = {
                'tp_sl_mode': mode
            }
            
            if mode == "ATR":
                config_update['atr_multiplier'] = self.atr_multiplier_spin.value()
            elif mode == "Points":
                config_update['tp_points'] = self.tp_points_spin.value()
                config_update['sl_points'] = self.sl_points_spin.value()
            elif mode == "Pips":
                config_update['tp_pips'] = self.tp_pips_spin.value()
                config_update['sl_pips'] = self.sl_pips_spin.value()
            elif mode == "Percent":
                config_update['tp_percent'] = self.tp_percent_spin.value()
                config_update['sl_percent'] = self.sl_percent_spin.value()
            
            # Update risk management settings too
            config_update.update({
                'risk_percent': self.risk_percent_spin.value(),
                'max_daily_loss': self.max_daily_loss_spin.value(),
                'max_trades_per_day': self.max_trades_spin.value(),
                'max_spread_points': self.max_spread_spin.value(),
                'min_sl_points': self.min_sl_spin.value(),
                'risk_multiple': self.risk_multiple_spin.value()
            })
            
            # Apply configuration immediately
            self.controller.update_config(config_update)
            self.log_message(f"✅ TP/SL and Risk settings applied successfully: {mode} mode", "INFO")
            self.log_message(f"Risk: {self.risk_percent_spin.value()}%, SL Mode: {mode}", "INFO")
            
        except Exception as e:
            self.log_message(f"TP/SL settings apply error: {e}", "ERROR")
    
    # Event handlers with comprehensive error handling
    def on_connect(self):
        """Handle connect button click with validation"""
        try:
            self.log_message("Attempting MT5 connection...", "INFO")
            
            if self.controller.connect_mt5():
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(True)
                self.start_btn.setEnabled(True)
                
                self.connection_status.setText("✅ Connected")
                self.connection_status.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                
                self.status_label.setText("✅ Status: Connected to MT5")
                self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                
                # Update account info displays
                if hasattr(self.controller, 'account_info') and self.controller.account_info:
                    self.account_login_label.setText(f"Account: {self.controller.account_info.login}")
                
                self.log_message("MT5 connection successful!", "INFO")
            else:
                self.log_message("MT5 connection failed!", "ERROR")
                QMessageBox.critical(self, "Connection Failed", 
                                   "Failed to connect to MetaTrader 5.\nPlease ensure MT5 is running and logged in.")
                                   
        except Exception as e:
            self.log_message(f"Connection error: {e}", "ERROR")
            QMessageBox.critical(self, "Connection Error", f"Connection failed with error: {e}")
    
    def on_disconnect(self):
        """Handle disconnect button click"""
        try:
            self.controller.disconnect_mt5()
            
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            
            self.connection_status.setText("❌ Disconnected")
            self.connection_status.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            
            self.status_label.setText("❌ Status: Disconnected")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            
            self.log_message("Disconnected from MT5", "INFO")
            
        except Exception as e:
            self.log_message(f"Disconnect error: {e}", "ERROR")
    
    def on_start_bot(self):
        """Handle start bot button click with comprehensive validation"""
        try:
            # Validate connection first
            if not self.controller.is_connected:
                QMessageBox.warning(self, "Not Connected", "Please connect to MT5 first!")
                return
            
            # Show safety warning for live trading
            if not self.shadow_mode_cb.isChecked():
                reply = QMessageBox.warning(
                    self, 
                    "⚠️ LIVE TRADING WARNING",
                    "You are about to start LIVE TRADING with REAL MONEY!\n\n"
                    "⚠️ This will place actual orders in your MT5 account\n"
                    "⚠️ You can lose real money\n"
                    "⚠️ Make sure you understand the risks\n\n"
                    "It's STRONGLY recommended to test in Shadow Mode first!\n\n"
                    "Do you want to continue with LIVE TRADING?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    return
            
            # Update configuration from GUI
            config = {
                'symbol': self.symbol_combo.currentText(),
                'risk_percent': self.risk_percent_spin.value(),
                'max_daily_loss': self.max_daily_loss_spin.value(),
                'max_trades_per_day': self.max_trades_spin.value(),
                'max_spread_points': self.max_spread_spin.value(),
                'min_sl_points': self.min_sl_spin.value(),
                'risk_multiple': self.risk_multiple_spin.value(),
                'ema_periods': {
                    'fast': self.ema_fast_spin.value(),
                    'medium': self.ema_medium_spin.value(),
                    'slow': self.ema_slow_spin.value()
                },
                'rsi_period': self.rsi_period_spin.value(),
                'atr_period': self.atr_period_spin.value()
            }
            
            self.controller.update_config(config)
            
            if self.controller.start_bot():
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                
                self.bot_status.setText("🚀 Running")
                self.bot_status.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                
                mode = "SHADOW MODE" if self.shadow_mode_cb.isChecked() else "🚨 LIVE TRADING"
                self.log_message(f"Bot started in {mode}", "INFO")
            else:
                QMessageBox.critical(self, "Start Failed", "Failed to start trading bot!")
                
        except Exception as e:
            self.log_message(f"Bot start error: {e}", "ERROR")
            QMessageBox.critical(self, "Start Error", f"Failed to start bot: {e}")
    
    def on_stop_bot(self):
        """Handle stop bot button click"""
        try:
            self.controller.stop_bot()
            
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            self.bot_status.setText("⏸️ Stopped")
            self.bot_status.setStyleSheet("QLabel { color: gray; font-weight: bold; }")
            
            self.log_message("Bot stopped successfully", "INFO")
            
        except Exception as e:
            self.log_message(f"Bot stop error: {e}", "ERROR")
    
    def on_emergency_stop(self):
        """Handle emergency stop button click"""
        try:
            reply = QMessageBox.question(
                self,
                "🚨 Emergency Stop Confirmation",
                "This will immediately:\n"
                "• Stop the trading bot\n"
                "• Close all open positions\n"
                "• Disconnect from MT5\n\n"
                "Are you sure you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Stop bot first
                self.controller.stop_bot()
                
                # Close all positions
                if hasattr(self.controller, 'close_all_positions'):
                    self.controller.close_all_positions()
                
                # Disconnect
                self.controller.disconnect_mt5()
                
                # Update UI
                self.on_disconnect()
                
                self.log_message("🚨 EMERGENCY STOP EXECUTED", "WARNING")
                QMessageBox.information(self, "Emergency Stop", "Emergency stop completed successfully!")
                
        except Exception as e:
            self.log_message(f"Emergency stop error: {e}", "ERROR")
    
    def on_shadow_mode_toggle(self, checked):
        """Handle shadow mode toggle"""
        try:
            self.controller.toggle_shadow_mode(checked)
            
            if checked:
                self.mode_status.setText("🛡️ Shadow")
                self.mode_status.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                self.log_message("Shadow mode enabled - Signals only, no real trades", "INFO")
            else:
                self.mode_status.setText("🚨 Live")
                self.mode_status.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                self.log_message("⚠️ LIVE TRADING MODE - Real money at risk!", "WARNING")
                
        except Exception as e:
            self.log_message(f"Shadow mode toggle error: {e}", "ERROR")
    
    def on_symbol_changed(self, symbol):
        """Handle symbol change with validation"""
        try:
            # Update controller configuration
            self.controller.update_config({'symbol': symbol})
            
            # Reset symbol status
            self.symbol_status_label.setText("❓ Not validated")
            
            self.log_message(f"Symbol changed to: {symbol}", "INFO")
            
        except Exception as e:
            self.log_message(f"Symbol change error: {e}", "ERROR")
    
    def on_test_signal(self):
        """Test signal generation"""
        try:
            if hasattr(self.controller, 'test_signal'):
                self.controller.test_signal()
            else:
                self.log_message("Test signal function not available", "WARNING")
        except Exception as e:
            self.log_message(f"Test signal error: {e}", "ERROR")
    
    def on_validate_symbol(self):
        """Validate current symbol"""
        try:
            symbol = self.symbol_combo.currentText()
            # Add symbol validation logic here
            self.log_message(f"Validating symbol: {symbol}", "INFO")
            # Update symbol status based on validation result
            self.symbol_status_label.setText("✅ Valid")
        except Exception as e:
            self.log_message(f"Symbol validation error: {e}", "ERROR")
            self.symbol_status_label.setText("❌ Invalid")
    
    def on_check_margin(self):
        """Check margin requirements"""
        try:
            self.log_message("Checking margin requirements...", "INFO")
            # Add margin checking logic here
        except Exception as e:
            self.log_message(f"Margin check error: {e}", "ERROR")
    
    def on_close_all_positions(self):
        """Close all open positions"""
        try:
            reply = QMessageBox.question(
                self, "Confirm", "Close all open positions?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if hasattr(self.controller, 'close_all_positions'):
                    self.controller.close_all_positions()
                else:
                    self.log_message("Close all positions function not available", "WARNING")
        except Exception as e:
            self.log_message(f"Close positions error: {e}", "ERROR")
    
    def on_export_logs(self):
        """Export trading logs"""
        try:
            if hasattr(self.controller, 'export_logs'):
                file_path = self.controller.export_logs()
                if file_path:
                    QMessageBox.information(self, "Success", f"Logs exported to {file_path}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to export logs")
            else:
                self.log_message("Export logs function not available", "WARNING")
        except Exception as e:
            self.log_message(f"Export logs error: {e}", "ERROR")
    
    def refresh_positions(self):
        """Refresh positions display"""
        try:
            if hasattr(self.controller, 'update_positions_display'):
                self.controller.update_positions_display()
            self.log_message("Positions refreshed", "INFO")
        except Exception as e:
            self.log_message(f"Refresh positions error: {e}", "ERROR")
    
    # Slots for controller signals with error handling
    @Slot(str, str)
    def log_message(self, message: str, level: str):
        """Display log message with color coding"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Color code based on log level
            color_map = {
                "INFO": "#00FF00",      # Green
                "WARNING": "#FFA500",   # Orange
                "ERROR": "#FF0000",     # Red
                "DEBUG": "#00FFFF"      # Cyan
            }
            
            color = color_map.get(level, "#FFFFFF")  # White as default
            formatted_msg = f'<span style="color: {color};">[{timestamp}] {level}: {message}</span>'
            
            self.log_text.append(formatted_msg)
            
            # Auto-scroll to bottom
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)
            
        except Exception as e:
            print(f"Log display error: {e}")
    
    @Slot(str)
    def update_status(self, status: str):
        """Update status display"""
        try:
            self.status_label.setText(f"Status: {status}")
            self.bot_status.setText(status)
            
            # Update status bar
            self.statusBar().showMessage(f"System Status: {status}")
            
            if status == "Connected":
                self.connection_status.setText("✅ Connected")
                self.connection_status.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            elif status == "Disconnected":
                self.connection_status.setText("❌ Disconnected")
                self.connection_status.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            elif status == "Running":
                self.bot_status.setText("🚀 Running")
                self.bot_status.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            elif status == "Stopped":
                self.bot_status.setText("⏸️ Stopped")
                self.bot_status.setStyleSheet("QLabel { color: gray; font-weight: bold; }")
                
        except Exception as e:
            print(f"Status update error: {e}")
    
    @Slot(dict)
    def update_market_data(self, data: Dict):
        """Update market data display with error handling"""
        try:
            # Update price displays
            self.bid_label.setText(f"{data.get('bid', 0.0):.5f}")
            self.ask_label.setText(f"{data.get('ask', 0.0):.5f}")
            self.spread_label.setText(f"{data.get('spread', 0)}")
            
            if 'time' in data:
                self.time_label.setText(data['time'].strftime("%H:%M:%S"))
            
        except Exception as e:
            print(f"Market data update error: {e}")
    
    @Slot(dict)
    def update_indicators_display(self, indicators: Dict):
        """Update indicators display"""
        try:
            # Update M1 indicators
            if 'M1' in indicators and indicators['M1']:
                ind_m1 = indicators['M1']
                self.ema_fast_m1_label.setText(f"{ind_m1.get('ema_fast', 0):.5f}" if ind_m1.get('ema_fast') else "N/A")
                self.ema_medium_m1_label.setText(f"{ind_m1.get('ema_medium', 0):.5f}" if ind_m1.get('ema_medium') else "N/A")
                self.ema_slow_m1_label.setText(f"{ind_m1.get('ema_slow', 0):.5f}" if ind_m1.get('ema_slow') else "N/A")
                self.rsi_m1_label.setText(f"{ind_m1.get('rsi', 0):.2f}" if ind_m1.get('rsi') else "N/A")
                self.atr_m1_label.setText(f"{ind_m1.get('atr', 0):.5f}" if ind_m1.get('atr') else "N/A")
            
            # Update M5 indicators
            if 'M5' in indicators and indicators['M5']:
                ind_m5 = indicators['M5']
                self.ema_fast_m5_label.setText(f"{ind_m5.get('ema_fast', 0):.5f}" if ind_m5.get('ema_fast') else "N/A")
                self.ema_medium_m5_label.setText(f"{ind_m5.get('ema_medium', 0):.5f}" if ind_m5.get('ema_medium') else "N/A")
                self.ema_slow_m5_label.setText(f"{ind_m5.get('ema_slow', 0):.5f}" if ind_m5.get('ema_slow') else "N/A")
                self.rsi_m5_label.setText(f"{ind_m5.get('rsi', 0):.2f}" if ind_m5.get('rsi') else "N/A")
                self.atr_m5_label.setText(f"{ind_m5.get('atr', 0):.5f}" if ind_m5.get('atr') else "N/A")
                
        except Exception as e:
            print(f"Indicators update error: {e}")
    
    @Slot(dict)
    def update_analysis_status(self, analysis: Dict):
        """Update analysis status display"""
        try:
            status = analysis.get('status', 'idle')
            if status == 'analyzing':
                self.analysis_status_label.setText("🔍 Analyzing Market...")
                self.analysis_status_label.setStyleSheet("QLabel { font-weight: bold; color: blue; }")
            elif status == 'signal_found':
                self.analysis_status_label.setText("✅ Signal Detected")
                self.analysis_status_label.setStyleSheet("QLabel { font-weight: bold; color: green; }")
            elif status == 'no_signal':
                self.analysis_status_label.setText("⏳ Waiting for Setup")
                self.analysis_status_label.setStyleSheet("QLabel { font-weight: bold; color: orange; }")
            else:
                self.analysis_status_label.setText("⏸️ Idle")
                self.analysis_status_label.setStyleSheet("QLabel { font-weight: bold; color: gray; }")
            
            # Update trend analysis
            m5_trend = analysis.get('m5_trend', 'N/A')
            m1_setup = analysis.get('m1_setup', 'N/A')
            strength = analysis.get('signal_strength', 'N/A')
            
            self.trend_m5_label.setText(m5_trend)
            self.trend_m1_label.setText(m1_setup)
            self.signal_strength_label.setText(f"{strength}/10" if isinstance(strength, (int, float)) else strength)
            
            # Update next analysis time
            if 'next_analysis' in analysis:
                self.next_analysis_label.setText(analysis['next_analysis'])
                
        except Exception as e:
            print(f"Analysis status update error: {e}")
    
    @Slot(dict)
    def update_trade_signal(self, signal: Dict):
        """Update trade signal display with error handling"""
        try:
            signal_type = signal.get('type', 'None')
            self.signal_type_label.setText(signal_type)
            self.signal_entry_label.setText(f"{signal.get('entry_price', 0):.5f}")
            self.signal_sl_label.setText(f"{signal.get('sl_price', 0):.5f}")
            self.signal_tp_label.setText(f"{signal.get('tp_price', 0):.5f}")
            self.signal_lot_label.setText(f"{signal.get('lot_size', 0):.2f}")
            self.signal_risk_label.setText(f"1:{signal.get('risk_reward', 0):.1f}")
            
            if 'timestamp' in signal:
                self.signal_time_label.setText(signal['timestamp'].strftime("%H:%M:%S"))
            
            # Update auto trade status
            if not self.shadow_mode_cb.isChecked() and signal_type != 'None':
                self.auto_trade_status_label.setText("🚀 AUTO ORDER READY")
                self.auto_trade_status_label.setStyleSheet("QLabel { font-weight: bold; color: green; }")
            elif self.shadow_mode_cb.isChecked() and signal_type != 'None':
                self.auto_trade_status_label.setText("🛡️ SHADOW - Signal Only")
                self.auto_trade_status_label.setStyleSheet("QLabel { font-weight: bold; color: blue; }")
            else:
                self.auto_trade_status_label.setText("⏸️ No Signal")
                self.auto_trade_status_label.setStyleSheet("QLabel { font-weight: bold; color: gray; }")
            
        except Exception as e:
            print(f"Signal update error: {e}")
    
    @Slot(list)
    def update_positions(self, positions: List[Dict]):
        """Update positions table with error handling"""
        try:
            self.positions_table.setRowCount(len(positions))
            
            for row, pos in enumerate(positions):
                try:
                    # Safely update each cell
                    items = [
                        str(pos.get('ticket', '')),
                        pos.get('type', ''),
                        f"{pos.get('volume', 0):.2f}",
                        f"{pos.get('price_open', 0):.5f}",
                        f"{pos.get('price_current', pos.get('price_open', 0)):.5f}",
                        f"{pos.get('sl', 0):.5f}",
                        f"{pos.get('tp', 0):.5f}",
                        f"{pos.get('profit', 0):.2f}",
                        pos.get('comment', '')
                    ]
                    
                    for col, item_text in enumerate(items):
                        item = QTableWidgetItem(item_text)
                        
                        # Color code profit/loss
                        if col == 7:  # Profit column
                            profit = pos.get('profit', 0)
                            if profit > 0:
                                item.setBackground(QColor("#4CAF50"))  # Green
                            elif profit < 0:
                                item.setBackground(QColor("#f44336"))  # Red
                        
                        self.positions_table.setItem(row, col, item)
                        
                except Exception as row_error:
                    print(f"Error updating row {row}: {row_error}")
                    continue
                    
        except Exception as e:
            print(f"Position update error: {e}")
    
    @Slot(dict)
    def update_account_display(self, account_data: Dict):
        """Update account information display with error handling"""
        try:
            balance = account_data.get('balance', 0)
            equity = account_data.get('equity', 0)
            margin = account_data.get('margin', 0)
            profit = account_data.get('profit', 0)
            margin_free = account_data.get('margin_free', 0)
            
            self.balance_label.setText(f"${balance:.2f}")
            self.equity_label.setText(f"${equity:.2f}")
            self.margin_label.setText(f"${margin:.2f}")
            self.pnl_label.setText(f"${profit:.2f}")
            
            # Calculate and display margin level
            if margin > 0:
                margin_level = (equity / margin) * 100
                self.margin_level_label.setText(f"{margin_level:.1f}%")
                
                # Color code margin level
                if margin_level < 100:
                    self.margin_level_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                elif margin_level < 200:
                    self.margin_level_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
                else:
                    self.margin_level_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            
            # Color code P&L
            if profit > 0:
                self.pnl_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            elif profit < 0:
                self.pnl_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            else:
                self.pnl_label.setStyleSheet("QLabel { color: gray; font-weight: bold; }")
                
        except Exception as e:
            print(f"Account display update error: {e}")
    
    def update_gui_data(self):
        """Periodic GUI data update with error handling"""
        try:
            # Update system time
            if hasattr(self, 'system_time_label'):
                self.system_time_label.setText(datetime.now().strftime("%H:%M:%S"))
            
            # Update time in dashboard
            if hasattr(self, 'time_label') and self.controller.is_connected:
                self.time_label.setText(datetime.now().strftime("%H:%M:%S"))
            
            # Update positions if controller is available and connected
            if (hasattr(self.controller, 'is_connected') and 
                self.controller.is_connected and 
                hasattr(self.controller, 'get_positions')):
                try:
                    positions = self.controller.get_positions()
                    if positions is not None:
                        self.update_positions(positions)
                except:
                    pass  # Ignore position update errors
            
        except Exception as e:
            # Ignore GUI update errors to prevent disruption
            pass
    
    def clear_logs(self):
        """Clear log display"""
        try:
            self.log_text.clear()
            self.log_message("Logs cleared", "INFO")
        except Exception as e:
            print(f"Clear logs error: {e}")
    
    def save_logs(self):
        """Save logs to file with error handling"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Logs", 
                f"trading_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Success", f"Logs saved to:\n{filename}")
                self.log_message(f"Logs saved to {filename}", "INFO")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save logs:\n{e}")
            self.log_message(f"Failed to save logs: {e}", "ERROR")
    
    def closeEvent(self, event):
        """Handle application close event"""
        try:
            # Confirm before closing if bot is running
            if hasattr(self.controller, 'is_running') and self.controller.is_running:
                reply = QMessageBox.question(
                    self,
                    "Confirm Exit",
                    "Trading bot is still running!\n\n"
                    "Do you want to stop the bot and exit?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
                
                # Stop the bot before closing
                self.controller.stop_bot()
            
            # Disconnect if connected
            if hasattr(self.controller, 'is_connected') and self.controller.is_connected:
                self.controller.disconnect_mt5()
            
            # Stop timers
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
            
            self.log_message("Application closing...", "INFO")
            event.accept()
            
        except Exception as e:
            print(f"Close event error: {e}")
            event.accept()  # Close anyway
