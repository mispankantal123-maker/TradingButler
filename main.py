"""
MT5 Scalping Bot - Entry Point
Professional automated trading bot for XAUUSD symbols with PySide6 GUI
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import logging

from gui import MainWindow
from controller import BotController

# Setup logging
def setup_logging():
    """Configure logging to file and console"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'trading_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logger for this module
    logger = logging.getLogger(__name__)
    return logger

def main():
    """Main application entry point"""
    logger = setup_logging()
    logger.info("Starting MT5 Scalping Bot Application")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("MT5 Scalping Bot")
    app.setApplicationVersion("1.0.0")
    
    try:
        # Initialize bot controller
        controller = BotController()
        
        # Create main window
        main_window = MainWindow(controller)
        
        # Connect controller signals to GUI
        controller.signal_log.connect(main_window.log_message)
        controller.signal_status.connect(main_window.update_status)
        controller.signal_market_data.connect(main_window.update_market_data)
        controller.signal_trade_signal.connect(main_window.update_trade_signal)
        controller.signal_position_update.connect(main_window.update_positions)
        
        # Show main window
        main_window.show()
        
        logger.info("Application initialized successfully")
        
        # Start the application event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
