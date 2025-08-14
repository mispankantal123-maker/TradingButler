#!/usr/bin/env python3
"""
Fixed MT5 Scalping Bot - Main Entry Point
Solusi untuk masalah krusial yang telah diperbaiki:

BUGS YANG DIPERBAIKI:
1. ✅ Bot TIDAK melakukan analisa saat Start → Analysis Worker dengan heartbeat setiap 1 detik
2. ✅ Bot TIDAK mengambil order otomatis → Auto-execute signal di handle_trading_signal  
3. ✅ Tidak ada input TP/SL untuk user → TP/SL dinamis (ATR, Points, Pips, Balance%)
4. ✅ Threading yang benar → AnalysisWorker dengan QThread
5. ✅ Pre-flight checks → MT5 connection validation lengkap
6. ✅ Real-time indicators → Live data feed dengan error handling
7. ✅ Risk controls → Daily limits, consecutive losses, emergency stop
8. ✅ GUI tidak freeze → Separate threads untuk semua operasi MT5

ACCEPTANCE TESTS YANG HARUS LULUS:
1. ✅ Start → Logs menampilkan "[START] analysis thread starting..." dan "[HB] analyzer alive..."
2. ✅ Sinyal valid → Logs tampil "[SIGNAL]" lalu "[EXECUTE]" dan "[ORDER OK/FAIL]"
3. ✅ TP/SL Mode dinamis → Order terkirim dengan harga SL/TP sesuai mode
4. ✅ Risk controls → Auto stop saat daily loss limit tercapai
5. ✅ Emergency Stop → Menutup semua posisi

FITUR UTAMA:
- Threading Analysis Worker dengan heartbeat log setiap 1 detik
- Pre-flight checks lengkap (MT5 init, symbol validation, account info)
- Real-time data feed (tick + bars M1/M5) dengan error handling dan retry
- Strategi dual-timeframe: M5 trend filter + M1 pullback continuation
- TP/SL modes: ATR, Points, Pips, Balance% dengan input dinamis GUI
- Risk management: Daily loss limit, max trades, spread filter, session filter
- Order execution: BUY pakai Ask, SELL pakai Bid, dengan SL/TP terpasang
- Position monitoring dan emergency close all
- Comprehensive logging dengan CSV export
- Diagnostic doctor untuk troubleshooting
"""

import sys
import os
from pathlib import Path
import logging
import traceback
from datetime import datetime
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

# Import the FIXED controller and GUI
from fixed_controller import BotController
from fixed_gui import MainWindow

def setup_logging():
    """Configure comprehensive logging dengan Windows console fix"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Fix Windows console encoding untuk emoji
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        pass
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'scalping_bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Main application entry point dengan error handling lengkap"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("STARTING FIXED MT5 SCALPING BOT - PRODUCTION READY")
    logger.info("=" * 60)
    
    # Import check - gunakan teks biasa untuk log
    try:
        import MetaTrader5 as mt5
        MT5_AVAILABLE = True
        logger.info("MetaTrader5 module available - LIVE TRADING MODE")
    except ImportError:
        MT5_AVAILABLE = False
        logger.warning("MetaTrader5 not available - DEMO MODE (mock data)")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("MT5 Professional Scalping Bot - FIXED")
    app.setApplicationVersion("2.1.0")
    app.setAttribute(Qt.AA_DontUseNativeMenuBar, True)  # Fix untuk beberapa sistem
    
    try:
        logger.info("Initializing FIXED controller...")
        
        # Initialize FIXED controller dengan semua perbaikan
        controller = BotController()
        
        logger.info("Creating FIXED main window...")
        
        # Create FIXED main window dengan TP/SL input dinamis
        main_window = MainWindow(controller)
        main_window.show()
        
        logger.info("FIXED Bot Application initialized successfully!")
        logger.info("PERBAIKAN YANG TELAH DITERAPKAN:")
        logger.info("1. Analysis Worker dengan heartbeat setiap 1 detik")
        logger.info("2. Auto-execute signals (non-shadow mode)")
        logger.info("3. TP/SL input dinamis (ATR/Points/Pips/Balance%)")
        logger.info("4. Pre-flight checks lengkap")
        logger.info("5. Real-time data feed dengan error handling")
        logger.info("6. Risk management dan emergency controls")
        logger.info("7. Comprehensive logging dan diagnostics")
        logger.info("=" * 60)
        logger.info("READY FOR PROFESSIONAL SCALPING ON XAUUSD")
        logger.info("Start → Connect → Start Bot untuk mulai trading!")
        logger.info("=" * 60)
        
        # Start event loop
        return app.exec()
        
    except Exception as e:
        error_msg = f"Application startup error: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        
        # Show error dialog
        if 'app' in locals():
            QMessageBox.critical(None, "Startup Error", 
                               f"Failed to start application:\n\n{str(e)}\n\nCheck logs for details.")
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    
    print("\n" + "=" * 60)
    print("FIXED MT5 SCALPING BOT - SHUTDOWN")
    if exit_code == 0:
        print("Application closed normally")
    else:
        print("Application exited with errors")
    print("=" * 60)
    
    sys.exit(exit_code)