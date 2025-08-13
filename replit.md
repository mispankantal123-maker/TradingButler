# Overview

This is a professional automated trading bot for MetaTrader 5 (MT5) designed specifically for XAUUSD scalping strategies. The application features a modern PySide6 GUI interface with real-time market data monitoring, technical analysis using EMA/RSI/ATR indicators, and comprehensive risk management. The bot implements a dual-timeframe strategy using M5 trend filtering combined with M1 pullback continuation entries, focusing on precise order execution with proper bid/ask handling and ATR-based position sizing.

# User Preferences

Preferred communication style: Simple, everyday language.

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