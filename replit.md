# Overview

This is a professional automated trading bot for MetaTrader 5 (MT5) designed specifically for XAUUSD scalping strategies with REAL MONEY TRADING capability. The application features a modern PySide6 GUI interface with real-time market data monitoring, technical analysis using EMA/RSI/ATR indicators, and comprehensive risk management. The bot implements a dual-timeframe strategy using M5 trend filtering combined with M1 pullback continuation entries, focusing on precise order execution with proper bid/ask handling and ATR-based position sizing.

⚠️ **CRITICAL FOR LIVE TRADING**: This bot is production-ready for Windows with MetaTrader 5. All calculations, order execution, and risk management are optimized for real trading with actual funds. Demo mode is only used when MetaTrader5 module is unavailable.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes - August 14, 2025

## Major Bug Fixes Applied
1. **Analysis Threading Fixed**: Implemented proper AnalysisWorker(QThread) with heartbeat logging every 1 second
2. **Auto-Order Execution Fixed**: Added handle_trading_signal() with automatic order execution for non-shadow mode
3. **TP/SL Input System Added**: Created dynamic GUI inputs for ATR/Points/Pips/Balance% modes
4. **Real-time Data Feed**: Implemented continuous tick and bar data fetching with error handling
5. **Risk Management Enhanced**: Added daily loss limits, position monitoring, and emergency controls

## Files Created/Fixed
- `fixed_controller.py`: Main controller with proper threading and signal execution
- `fixed_gui.py`: Enhanced GUI with dynamic TP/SL inputs and status indicators  
- `fixed_main.py`: Production-ready entry point with comprehensive error handling
- `PERBAIKAN_SELESAI.md`: Complete documentation of all fixes applied

## Status
All critical issues resolved. Bot now ready for professional trading on Windows with MT5, or demo mode on other platforms.

# System Architecture

## Frontend Architecture
- **GUI Framework**: PySide6 (Qt6 for Python) providing a modern tabbed interface
- **Main Window Structure**: Tabbed layout with dedicated sections for Dashboard, Strategy, Risk Management, Execution, and Logs
- **Real-time Updates**: QTimer-based GUI refresh system for live market data, positions, and trading signals
- **Signal-Slot Communication**: Qt signals connect the backend controller to frontend widgets for thread-safe updates

## Backend Architecture
- **Controller Pattern**: Central BotController class manages all trading operations and state
- **Threading Model**: Separate threads for market data processing and GUI updates to prevent blocking
- **Strategy Engine**: Dual-timeframe analysis system (M5 trend filter + M1 entry signals)
- **Risk Management Module**: Integrated position sizing, daily loss limits, and trade count restrictions

## Technical Analysis System
- **Indicator Library**: Custom TechnicalIndicators class with accurate EMA, RSI, and ATR calculations
- **Timeframe Management**: Simultaneous M1 and M5 data processing for strategy execution
- **Signal Generation**: Trend filtering using EMA crossovers with pullback continuation entries

## Trading Execution
- **MT5 Integration**: Direct connection to MetaTrader 5 Python API for live market access
- **Order Management**: Precise bid/ask order placement with immediate SL/TP assignment
- **Position Tracking**: Real-time monitoring of open positions and trade performance

## Risk Management
- **Percentage-based Sizing**: Dynamic lot calculation based on account risk percentage
- **ATR-based Stops**: Stop loss and take profit levels calculated using Average True Range
- **Daily Limits**: Maximum daily loss and trade count restrictions with automatic reset

## Data Management
- **Market Data**: Real-time tick data and OHLC candle processing from MT5
- **State Persistence**: Configuration and trading session data management
- **Logging System**: Comprehensive logging with file output and GUI display

# External Dependencies

## Trading Platform
- **MetaTrader 5**: Primary trading platform integration via official Python API
- **MT5 Python API**: Real-time market data, order execution, and account management

## GUI Framework
- **PySide6**: Modern Qt6-based GUI framework for cross-platform desktop applications
- **Qt Core**: Threading, signals, timers, and application lifecycle management

## Data Processing
- **NumPy**: Numerical computations for technical indicator calculations
- **Pandas**: Time series data manipulation and analysis for market data

## System Integration
- **Python Standard Library**: Logging, threading, datetime, and file system operations
- **Windows Compatibility**: Designed specifically for Windows environment with MT5 integration

## Development Tools
- **Logging**: Built-in Python logging with file and console output
- **Path Management**: Pathlib for cross-platform file system operations