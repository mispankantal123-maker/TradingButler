"""
PySide6 GUI for MT5 Scalping Bot
Modern tabbed interface with real-time updates
"""

import sys
from datetime import datetime
from typing import Dict, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QGridLayout, QSplitter, QProgressBar,
    QStatusBar, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QFont, QPixmap, QIcon

class MainWindow(QMainWindow):
    """Main application window with tabbed interface"""
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("MT5 Professional Scalping Bot")
        self.setGeometry(100, 100, 1200, 800)
        
        # Setup UI
        self.setup_ui()
        self.setup_status_bar()
        self.connect_signals()
        
        # Update timer for GUI refresh
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_gui_data)
        self.update_timer.start(1000)  # Update every second
    
    def setup_ui(self):
        """Setup the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_strategy_tab()
        self.create_risk_tab()
        self.create_execution_tab()
        self.create_logs_tab()
    
    def create_dashboard_tab(self):
        """Create dashboard tab with connection and overview"""
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        
        # Connection section
        conn_group = QGroupBox("MT5 Connection")
        conn_layout = QGridLayout(conn_group)
        
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)
        self.status_label = QLabel("Status: Disconnected")
        
        conn_layout.addWidget(self.connect_btn, 0, 0)
        conn_layout.addWidget(self.disconnect_btn, 0, 1)
        conn_layout.addWidget(self.status_label, 1, 0, 1, 2)
        
        # Symbol selection
        symbol_group = QGroupBox("Symbol Configuration")
        symbol_layout = QFormLayout(symbol_group)
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["XAUUSD", "XAUUSDm", "XAUUSDc"])
        self.symbol_combo.setCurrentText("XAUUSD")
        
        symbol_layout.addRow("Symbol:", self.symbol_combo)
        
        # Bot control
        control_group = QGroupBox("Bot Control")
        control_layout = QGridLayout(control_group)
        
        self.start_btn = QPushButton("Start Bot")
        self.stop_btn = QPushButton("Stop Bot")
        self.stop_btn.setEnabled(False)
        self.shadow_mode_cb = QCheckBox("Shadow Mode (Signals Only)")
        self.shadow_mode_cb.setChecked(True)
        
        control_layout.addWidget(self.start_btn, 0, 0)
        control_layout.addWidget(self.stop_btn, 0, 1)
        control_layout.addWidget(self.shadow_mode_cb, 1, 0, 1, 2)
        
        # Market data display
        market_group = QGroupBox("Market Data")
        market_layout = QFormLayout(market_group)
        
        self.bid_label = QLabel("0.00000")
        self.ask_label = QLabel("0.00000")
        self.spread_label = QLabel("0")
        self.time_label = QLabel("N/A")
        
        market_layout.addRow("Bid:", self.bid_label)
        market_layout.addRow("Ask:", self.ask_label)
        market_layout.addRow("Spread (pts):", self.spread_label)
        market_layout.addRow("Time:", self.time_label)
        
        # Account info
        account_group = QGroupBox("Account Information")
        account_layout = QFormLayout(account_group)
        
        self.balance_label = QLabel("0.00")
        self.equity_label = QLabel("0.00")
        self.margin_label = QLabel("0.00")
        self.pnl_label = QLabel("0.00")
        
        account_layout.addRow("Balance:", self.balance_label)
        account_layout.addRow("Equity:", self.equity_label)
        account_layout.addRow("Margin:", self.margin_label)
        account_layout.addRow("P&L:", self.pnl_label)
        
        # Add groups to layout
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
        
        # Connect signals
        self.connect_btn.clicked.connect(self.on_connect)
        self.disconnect_btn.clicked.connect(self.on_disconnect)
        self.start_btn.clicked.connect(self.on_start_bot)
        self.stop_btn.clicked.connect(self.on_stop_bot)
        self.shadow_mode_cb.toggled.connect(self.on_shadow_mode_toggle)
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        
        self.tab_widget.addTab(dashboard, "Dashboard")
    
    def create_strategy_tab(self):
        """Create strategy configuration tab"""
        strategy = QWidget()
        layout = QVBoxLayout(strategy)
        
        # EMA Settings
        ema_group = QGroupBox("EMA Settings")
        ema_layout = QFormLayout(ema_group)
        
        self.ema_fast_spin = QSpinBox()
        self.ema_fast_spin.setRange(1, 50)
        self.ema_fast_spin.setValue(9)
        
        self.ema_medium_spin = QSpinBox()
        self.ema_medium_spin.setRange(1, 100)
        self.ema_medium_spin.setValue(21)
        
        self.ema_slow_spin = QSpinBox()
        self.ema_slow_spin.setRange(1, 200)
        self.ema_slow_spin.setValue(50)
        
        ema_layout.addRow("Fast EMA:", self.ema_fast_spin)
        ema_layout.addRow("Medium EMA:", self.ema_medium_spin)
        ema_layout.addRow("Slow EMA:", self.ema_slow_spin)
        
        # RSI Settings
        rsi_group = QGroupBox("RSI Settings")
        rsi_layout = QFormLayout(rsi_group)
        
        self.rsi_period_spin = QSpinBox()
        self.rsi_period_spin.setRange(1, 50)
        self.rsi_period_spin.setValue(14)
        
        rsi_layout.addRow("RSI Period:", self.rsi_period_spin)
        
        # ATR Settings
        atr_group = QGroupBox("ATR Settings")
        atr_layout = QFormLayout(atr_group)
        
        self.atr_period_spin = QSpinBox()
        self.atr_period_spin.setRange(1, 50)
        self.atr_period_spin.setValue(14)
        
        atr_layout.addRow("ATR Period:", self.atr_period_spin)
        
        # Current indicators display
        indicators_group = QGroupBox("Current Indicators")
        indicators_layout = QFormLayout(indicators_group)
        
        self.ema9_m1_label = QLabel("N/A")
        self.ema21_m1_label = QLabel("N/A")
        self.ema50_m1_label = QLabel("N/A")
        self.rsi_m1_label = QLabel("N/A")
        self.atr_m1_label = QLabel("N/A")
        
        self.ema9_m5_label = QLabel("N/A")
        self.ema21_m5_label = QLabel("N/A")
        self.ema50_m5_label = QLabel("N/A")
        self.rsi_m5_label = QLabel("N/A")
        self.atr_m5_label = QLabel("N/A")
        
        indicators_layout.addRow("M1 EMA9:", self.ema9_m1_label)
        indicators_layout.addRow("M1 EMA21:", self.ema21_m1_label)
        indicators_layout.addRow("M1 EMA50:", self.ema50_m1_label)
        indicators_layout.addRow("M1 RSI:", self.rsi_m1_label)
        indicators_layout.addRow("M1 ATR:", self.atr_m1_label)
        
        indicators_layout.addRow("", QLabel(""))  # Spacer
        
        indicators_layout.addRow("M5 EMA9:", self.ema9_m5_label)
        indicators_layout.addRow("M5 EMA21:", self.ema21_m5_label)
        indicators_layout.addRow("M5 EMA50:", self.ema50_m5_label)
        indicators_layout.addRow("M5 RSI:", self.rsi_m5_label)
        indicators_layout.addRow("M5 ATR:", self.atr_m5_label)
        
        # Layout arrangement
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(ema_group)
        settings_layout.addWidget(rsi_group)
        settings_layout.addWidget(atr_group)
        
        layout.addLayout(settings_layout)
        layout.addWidget(indicators_group)
        layout.addStretch()
        
        self.tab_widget.addTab(strategy, "Strategy")
    
    def create_risk_tab(self):
        """Create risk management tab"""
        risk = QWidget()
        layout = QVBoxLayout(risk)
        
        # Risk settings
        risk_group = QGroupBox("Risk Management Settings")
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
        self.max_trades_spin.setValue(10)
        
        self.risk_multiple_spin = QDoubleSpinBox()
        self.risk_multiple_spin.setRange(0.5, 5.0)
        self.risk_multiple_spin.setValue(1.5)
        
        self.max_spread_spin = QSpinBox()
        self.max_spread_spin.setRange(10, 200)
        self.max_spread_spin.setValue(50)
        self.max_spread_spin.setSuffix(" pts")
        
        self.min_sl_spin = QSpinBox()
        self.min_sl_spin.setRange(50, 500)
        self.min_sl_spin.setValue(100)
        self.min_sl_spin.setSuffix(" pts")
        
        risk_layout.addRow("Risk per Trade:", self.risk_percent_spin)
        risk_layout.addRow("Max Daily Loss:", self.max_daily_loss_spin)
        risk_layout.addRow("Max Trades/Day:", self.max_trades_spin)
        risk_layout.addRow("Risk Multiple (R):", self.risk_multiple_spin)
        risk_layout.addRow("Max Spread:", self.max_spread_spin)
        risk_layout.addRow("Min SL Distance:", self.min_sl_spin)
        
        # Daily statistics
        stats_group = QGroupBox("Daily Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self.daily_trades_label = QLabel("0")
        self.daily_pnl_label = QLabel("0.00")
        self.win_rate_label = QLabel("0%")
        self.max_dd_label = QLabel("0.00")
        
        stats_layout.addRow("Trades Today:", self.daily_trades_label)
        stats_layout.addRow("Daily P&L:", self.daily_pnl_label)
        stats_layout.addRow("Win Rate:", self.win_rate_label)
        stats_layout.addRow("Max Drawdown:", self.max_dd_label)
        
        layout.addWidget(risk_group)
        layout.addWidget(stats_group)
        layout.addStretch()
        
        self.tab_widget.addTab(risk, "Risk Management")
    
    def create_execution_tab(self):
        """Create trade execution tab"""
        execution = QWidget()
        layout = QVBoxLayout(execution)
        
        # Current signal display
        signal_group = QGroupBox("Current Trading Signal")
        signal_layout = QFormLayout(signal_group)
        
        self.signal_type_label = QLabel("None")
        self.signal_entry_label = QLabel("N/A")
        self.signal_sl_label = QLabel("N/A")
        self.signal_tp_label = QLabel("N/A")
        self.signal_lot_label = QLabel("N/A")
        self.signal_risk_label = QLabel("N/A")
        
        signal_layout.addRow("Signal Type:", self.signal_type_label)
        signal_layout.addRow("Entry Price:", self.signal_entry_label)
        signal_layout.addRow("Stop Loss:", self.signal_sl_label)
        signal_layout.addRow("Take Profit:", self.signal_tp_label)
        signal_layout.addRow("Lot Size:", self.signal_lot_label)
        signal_layout.addRow("Risk/Reward:", self.signal_risk_label)
        
        # Positions table
        positions_group = QGroupBox("Open Positions")
        positions_layout = QVBoxLayout(positions_group)
        
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "Ticket", "Type", "Volume", "Entry", "SL", "TP", "Profit", "Comment"
        ])
        positions_layout.addWidget(self.positions_table)
        
        layout.addWidget(signal_group)
        layout.addWidget(positions_group)
        
        self.tab_widget.addTab(execution, "Execution")
    
    def create_logs_tab(self):
        """Create logs and history tab"""
        logs = QWidget()
        layout = QVBoxLayout(logs)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        
        # Log controls
        controls_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear Logs")
        save_btn = QPushButton("Save Logs")
        
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(save_btn)
        controls_layout.addStretch()
        
        layout.addWidget(self.log_text)
        layout.addLayout(controls_layout)
        
        # Connect buttons
        clear_btn.clicked.connect(self.clear_logs)
        save_btn.clicked.connect(self.save_logs)
        
        self.tab_widget.addTab(logs, "Logs")
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.statusBar().showMessage("Ready")
        
        # Add status indicators
        self.connection_status = QLabel("Disconnected")
        self.bot_status = QLabel("Stopped")
        self.mode_status = QLabel("Shadow")
        
        self.statusBar().addPermanentWidget(QLabel("Connection:"))
        self.statusBar().addPermanentWidget(self.connection_status)
        self.statusBar().addPermanentWidget(QLabel("Bot:"))
        self.statusBar().addPermanentWidget(self.bot_status)
        self.statusBar().addPermanentWidget(QLabel("Mode:"))
        self.statusBar().addPermanentWidget(self.mode_status)
    
    def connect_signals(self):
        """Connect controller signals to GUI slots"""
        # Connect all controller signals
        self.controller.signal_log.connect(self.log_message)
        self.controller.signal_status.connect(self.update_status)
        self.controller.signal_market_data.connect(self.update_market_data)
        self.controller.signal_trade_signal.connect(self.update_trade_signal)
        self.controller.signal_position_update.connect(self.update_positions)
        self.controller.signal_account_update.connect(self.update_account_display)
    
    # Event handlers
    def on_connect(self):
        """Handle connect button click"""
        if self.controller.connect_mt5():
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
    
    def on_disconnect(self):
        """Handle disconnect button click"""
        self.controller.disconnect_mt5()
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
    
    def on_start_bot(self):
        """Handle start bot button click"""
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
    
    def on_stop_bot(self):
        """Handle stop bot button click"""
        self.controller.stop_bot()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def on_test_signal(self):
        """Test signal generation"""
        self.controller.test_signal()
    
    def on_close_all_positions(self):
        """Close all open positions"""
        reply = QMessageBox.question(
            self, "Confirm", "Close all open positions?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.controller.close_all_positions()
    
    def on_export_logs(self):
        """Export trading logs"""
        file_path = self.controller.export_logs()
        if file_path:
            QMessageBox.information(self, "Success", f"Logs exported to {file_path}")
        else:
            QMessageBox.warning(self, "Error", "Failed to export logs")
    
    def on_shadow_mode_toggle(self, checked):
        """Handle shadow mode toggle"""
        self.controller.toggle_shadow_mode(checked)
        self.mode_status.setText("Shadow" if checked else "Live")
    
    def on_symbol_changed(self, symbol):
        """Handle symbol change"""
        # Update controller configuration
        self.controller.update_config({'symbol': symbol})
    
    # Slots for controller signals
    @Slot(str, str)
    def log_message(self, message: str, level: str):
        """Display log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {level}: {message}"
        self.log_text.append(formatted_msg)
    
    @Slot(str)
    def update_status(self, status: str):
        """Update status display"""
        self.status_label.setText(f"Status: {status}")
        self.bot_status.setText(status)
        
        if status == "Connected":
            self.connection_status.setText("Connected")
        elif status == "Disconnected":
            self.connection_status.setText("Disconnected")
    
    @Slot(dict)
    def update_market_data(self, data: Dict):
        """Update market data display"""
        self.bid_label.setText(f"{data['bid']:.5f}")
        self.ask_label.setText(f"{data['ask']:.5f}")
        self.spread_label.setText(f"{data['spread']}")
        self.time_label.setText(data['time'].strftime("%H:%M:%S"))
        
        # Update indicators
        if 'indicators_m1' in data:
            ind_m1 = data['indicators_m1']
            self.ema9_m1_label.setText(f"{ind_m1.get('ema_fast', 0):.5f}" if ind_m1.get('ema_fast') else "N/A")
            self.ema21_m1_label.setText(f"{ind_m1.get('ema_medium', 0):.5f}" if ind_m1.get('ema_medium') else "N/A")
            self.ema50_m1_label.setText(f"{ind_m1.get('ema_slow', 0):.5f}" if ind_m1.get('ema_slow') else "N/A")
            self.rsi_m1_label.setText(f"{ind_m1.get('rsi', 0):.2f}" if ind_m1.get('rsi') else "N/A")
            self.atr_m1_label.setText(f"{ind_m1.get('atr', 0):.5f}" if ind_m1.get('atr') else "N/A")
        
        if 'indicators_m5' in data:
            ind_m5 = data['indicators_m5']
            self.ema9_m5_label.setText(f"{ind_m5.get('ema_fast', 0):.5f}" if ind_m5.get('ema_fast') else "N/A")
            self.ema21_m5_label.setText(f"{ind_m5.get('ema_medium', 0):.5f}" if ind_m5.get('ema_medium') else "N/A")
            self.ema50_m5_label.setText(f"{ind_m5.get('ema_slow', 0):.5f}" if ind_m5.get('ema_slow') else "N/A")
            self.rsi_m5_label.setText(f"{ind_m5.get('rsi', 0):.2f}" if ind_m5.get('rsi') else "N/A")
            self.atr_m5_label.setText(f"{ind_m5.get('atr', 0):.5f}" if ind_m5.get('atr') else "N/A")
    
    @Slot(dict)
    def update_trade_signal(self, signal: Dict):
        """Update trade signal display"""
        self.signal_type_label.setText(signal['type'])
        self.signal_entry_label.setText(f"{signal['entry_price']:.5f}")
        self.signal_sl_label.setText(f"{signal['sl_price']:.5f}")
        self.signal_tp_label.setText(f"{signal['tp_price']:.5f}")
        self.signal_lot_label.setText(f"{signal['lot_size']:.2f}")
        self.signal_risk_label.setText(f"1:{signal['risk_reward']}")
    
    @Slot(list)
    def update_positions(self, positions: List[Dict]):
        """Update positions table"""
        self.positions_table.setRowCount(len(positions))
        
        for row, pos in enumerate(positions):
            self.positions_table.setItem(row, 0, QTableWidgetItem(str(pos['ticket'])))
            self.positions_table.setItem(row, 1, QTableWidgetItem(pos['type']))
            self.positions_table.setItem(row, 2, QTableWidgetItem(f"{pos['volume']:.2f}"))
            self.positions_table.setItem(row, 3, QTableWidgetItem(f"{pos['price_open']:.5f}"))
            self.positions_table.setItem(row, 4, QTableWidgetItem(f"{pos['sl']:.5f}"))
            self.positions_table.setItem(row, 5, QTableWidgetItem(f"{pos['tp']:.5f}"))
            self.positions_table.setItem(row, 6, QTableWidgetItem(f"{pos['profit']:.2f}"))
            self.positions_table.setItem(row, 7, QTableWidgetItem(pos['comment']))
    
    @Slot(dict)
    def update_account_display(self, account_data: Dict):
        """Update account information display"""
        self.balance_label.setText(f"{account_data['balance']:.2f}")
        self.equity_label.setText(f"{account_data['equity']:.2f}")
        self.margin_label.setText(f"{account_data['margin']:.2f}")
        self.pnl_label.setText(f"{account_data['profit']:.2f}")
    
    def update_gui_data(self):
        """Periodic GUI data update"""
        try:
            # Update positions
            positions = self.controller.get_positions()
            self.update_positions(positions)
            
            # Update account info if connected
            if self.controller.is_connected:
                try:
                    import MetaTrader5 as mt5
                    account_info = mt5.account_info()
                    if account_info:
                        self.balance_label.setText(f"{account_info.balance:.2f}")
                        self.equity_label.setText(f"{account_info.equity:.2f}")
                        self.margin_label.setText(f"{account_info.margin:.2f}")
                        self.pnl_label.setText(f"{account_info.profit:.2f}")
                except ImportError:
                    self.balance_label.setText("MT5 Not Available")
                    self.equity_label.setText("MT5 Not Available")
                    self.margin_label.setText("MT5 Not Available")
                    self.pnl_label.setText("MT5 Not Available")
        except Exception as e:
            pass  # Ignore errors during GUI updates
    
    def clear_logs(self):
        """Clear log display"""
        self.log_text.clear()
    
    def save_logs(self):
        """Save logs to file"""
        try:
            from PySide6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Logs", "trading_logs.txt", "Text Files (*.txt)"
            )
            if filename:
                with open(filename, 'w') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Success", "Logs saved successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save logs: {e}")
