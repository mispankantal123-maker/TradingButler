#!/usr/bin/env python3
"""
Complete MT5 Scalping Bot - Production Ready
All features implemented as requested: live data, signals, execution, risk management
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication

# Import the working controller and GUI
from controller import BotController as ScalpingBotController
from gui import MainWindow

# Check MT5 availability
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

def setup_logging():
    """Configure comprehensive logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'scalping_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Main application entry point"""
    logger = setup_logging()
    logger.info("Starting Complete MT5 Scalping Bot")
    
    if not MT5_AVAILABLE:
        logger.warning("MetaTrader5 not available - using fallback mode")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("MT5 Professional Scalping Bot")
    app.setApplicationVersion("2.0.0")
    
    try:
        # Initialize controller with all features
        controller = ScalpingBotController()
        
        # Create enhanced main window
        main_window = MainWindow(controller)
        main_window.show()
        
        logger.info("Application initialized successfully")
        logger.info("Features: Live data, Signals, Execution, Risk management")
        logger.info("Ready for professional scalping on XAUUSD")
        
        # Start event loop
        return app.exec()
        
    except Exception as e:
        logger.error(f"Application startup error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())