
"""
MT5 Scalping Bot - Entry Point
Professional automated trading bot for XAUUSD symbols with PySide6 GUI
PRODUCTION READY FOR REAL MONEY TRADING
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
import logging

# Ensure proper imports
try:
    from gui import MainWindow
    from controller import BotController
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def setup_logging():
    """Configure comprehensive logging system"""
    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger with detailed format
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'trading_bot.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set specific loggers
        logger = logging.getLogger(__name__)
        logging.getLogger('PySide6').setLevel(logging.WARNING)
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        
        return logger
    except Exception as e:
        print(f"Logging setup failed: {e}")
        return logging.getLogger(__name__)

def check_mt5_availability():
    """Check if MetaTrader 5 is available and properly configured"""
    try:
        import MetaTrader5 as mt5
        
        # Test initialization
        if not mt5.initialize():
            error = mt5.last_error()
            return False, f"MT5 initialization failed: {error}"
        
        # Get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            mt5.shutdown()
            return False, "Cannot get terminal information"
        
        # Check if trading is allowed
        if not terminal_info.trade_allowed:
            mt5.shutdown()
            return False, "Trading is not allowed in MT5 terminal"
        
        mt5.shutdown()
        return True, "MT5 available and ready"
        
    except ImportError:
        return False, "MetaTrader5 module not installed"
    except Exception as e:
        return False, f"MT5 check failed: {e}"

def main():
    """Main application entry point with comprehensive error handling"""
    logger = setup_logging()
    logger.info("=== MT5 PROFESSIONAL SCALPING BOT STARTUP ===")
    
    # Check MT5 availability first
    mt5_available, mt5_message = check_mt5_availability()
    if mt5_available:
        logger.info(f"✅ {mt5_message}")
    else:
        logger.error(f"❌ {mt5_message}")
        logger.error("Bot will run in demo mode - NO REAL TRADING POSSIBLE")
    
    # Create QApplication with error handling
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("MT5 Professional Scalping Bot")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("MT5 Trading Solutions")
        
        # Set application properties for better integration
        from PySide6.QtCore import Qt
        if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
            app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
    except Exception as e:
        logger.error(f"Failed to create QApplication: {e}")
        return 1
    
    try:
        # Initialize bot controller with error handling
        logger.info("Initializing trading controller...")
        controller = BotController()
        
        # Create main window with error handling
        logger.info("Creating main window...")
        main_window = MainWindow(controller)
        
        # Verify all GUI components are properly initialized
        if not hasattr(main_window, 'connect_btn'):
            raise AttributeError("GUI components not properly initialized")
        
        # Show warning for real trading
        if mt5_available:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.warning(
                None, 
                "⚠️ REAL TRADING WARNING", 
                "This bot will trade with REAL MONEY!\n\n"
                "• Always start in Shadow Mode first\n"
                "• Test thoroughly before live trading\n"
                "• Monitor your account carefully\n"
                "• Use proper risk management\n\n"
                "Continue with EXTREME caution!",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                logger.info("User cancelled - exiting safely")
                return 0
        
        # Show main window
        main_window.show()
        
        # Log successful startup
        logger.info("✅ Application initialized successfully")
        logger.info("✅ GUI loaded and ready")
        logger.info("✅ All systems operational")
        
        if mt5_available:
            logger.info("🚀 READY FOR REAL TRADING - USE SHADOW MODE FIRST!")
        else:
            logger.info("📊 DEMO MODE - For testing purposes only")
        
        # Start the application event loop
        result = app.exec()
        
        logger.info("Application shutdown complete")
        return result
        
    except Exception as e:
        logger.error(f"Fatal application error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        try:
            # Show error dialog if possible
            QMessageBox.critical(
                None,
                "Fatal Error",
                f"Application failed to start:\n{e}\n\nCheck logs for details."
            )
        except:
            pass
        
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unhandled exception: {e}")
        sys.exit(1)
