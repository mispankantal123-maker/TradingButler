
"""
Technical Indicators for MT5 Scalping Bot
Implements EMA, RSI, ATR calculations for market analysis
PRODUCTION READY - Optimized for real-time trading
"""

import numpy as np
import pandas as pd
from typing import List, Optional
import logging

class TechnicalIndicators:
    """Technical indicators calculator for scalping strategy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Exponential Moving Average
        
        Args:
            data: Price data array
            period: EMA period
            
        Returns:
            EMA values array
        """
        try:
            if len(data) < period:
                return np.full(len(data), np.nan)
            
            # Calculate multiplier
            multiplier = 2.0 / (period + 1)
            
            # Initialize EMA array
            ema_values = np.zeros(len(data))
            
            # First EMA value is SMA
            ema_values[period-1] = np.mean(data[:period])
            
            # Calculate EMA for remaining values
            for i in range(period, len(data)):
                ema_values[i] = (data[i] * multiplier) + (ema_values[i-1] * (1 - multiplier))
            
            # Set initial values to NaN
            ema_values[:period-1] = np.nan
            
            return ema_values
            
        except Exception as e:
            self.logger.error(f"EMA calculation error: {e}")
            return np.full(len(data), np.nan)
    
    def rsi(self, data: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calculate Relative Strength Index
        
        Args:
            data: Price data array
            period: RSI period (default 14)
            
        Returns:
            RSI values array
        """
        try:
            if len(data) < period + 1:
                return np.full(len(data), 50.0)
            
            # Calculate price changes
            delta = np.diff(data)
            
            # Separate gains and losses
            gains = np.where(delta > 0, delta, 0)
            losses = np.where(delta < 0, -delta, 0)
            
            # Calculate average gains and losses using EMA (Wilder's smoothing)
            alpha = 1.0 / period
            
            avg_gains = np.zeros(len(gains))
            avg_losses = np.zeros(len(losses))
            
            # First average is SMA
            avg_gains[period-1] = np.mean(gains[:period])
            avg_losses[period-1] = np.mean(losses[:period])
            
            # EMA for remaining values
            for i in range(period, len(gains)):
                avg_gains[i] = alpha * gains[i] + (1 - alpha) * avg_gains[i-1]
                avg_losses[i] = alpha * losses[i] + (1 - alpha) * avg_losses[i-1]
            
            # Calculate RSI
            rsi_values = np.zeros(len(data))
            
            for i in range(period-1, len(data)):
                if avg_losses[i] == 0:
                    rsi_values[i] = 100.0
                else:
                    rs = avg_gains[i] / avg_losses[i]
                    rsi_values[i] = 100.0 - (100.0 / (1.0 + rs))
            
            # Set initial values to 50
            rsi_values[:period-1] = 50.0
            
            return rsi_values
            
        except Exception as e:
            self.logger.error(f"RSI calculation error: {e}")
            return np.full(len(data), 50.0)
    
    def atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calculate Average True Range
        
        Args:
            high: High prices array
            low: Low prices array
            close: Close prices array
            period: ATR period (default 14)
            
        Returns:
            ATR values array
        """
        try:
            if len(high) < period + 1:
                return np.full(len(high), 0.001)
            
            # Calculate True Range
            tr_list = []
            
            for i in range(1, len(high)):
                tr1 = high[i] - low[i]
                tr2 = abs(high[i] - close[i-1])
                tr3 = abs(low[i] - close[i-1])
                tr = max(tr1, tr2, tr3)
                tr_list.append(tr)
            
            tr_array = np.array(tr_list)
            
            # Calculate ATR using EMA
            atr_values = np.zeros(len(high))
            atr_values[0] = 0.001  # Default for first value
            
            if len(tr_array) >= period:
                # Initial ATR is SMA of TR
                atr_values[period] = np.mean(tr_array[:period])
                
                # Calculate subsequent ATR values
                multiplier = 1.0 / period
                for i in range(period + 1, len(high)):
                    if i - 1 < len(tr_array):
                        atr_values[i] = ((atr_values[i-1] * (period - 1)) + tr_array[i-1]) / period
                    else:
                        atr_values[i] = atr_values[i-1]
                
                # Fill initial values
                for i in range(1, period):
                    atr_values[i] = atr_values[period]
            else:
                atr_values.fill(0.001)
            
            return atr_values
            
        except Exception as e:
            self.logger.error(f"ATR calculation error: {e}")
            return np.full(len(high), 0.001)
    
    def calculate_ema(self, data: List[float], period: int) -> Optional[float]:
        """
        Calculate single EMA value (for compatibility)
        
        Args:
            data: Price data list
            period: EMA period
            
        Returns:
            Current EMA value or None
        """
        try:
            if len(data) < period:
                return None
            
            data_array = np.array(data, dtype=np.float64)
            ema_values = self.ema(data_array, period)
            
            # Return last valid EMA value
            valid_values = ema_values[~np.isnan(ema_values)]
            return float(valid_values[-1]) if len(valid_values) > 0 else None
            
        except Exception as e:
            self.logger.error(f"Single EMA calculation error: {e}")
            return None
    
    def calculate_rsi(self, data: List[float], period: int) -> float:
        """
        Calculate single RSI value (for compatibility)
        
        Args:
            data: Price data list
            period: RSI period
            
        Returns:
            Current RSI value
        """
        try:
            if len(data) < period + 1:
                return 50.0
            
            data_array = np.array(data, dtype=np.float64)
            rsi_values = self.rsi(data_array, period)
            
            return float(rsi_values[-1])
            
        except Exception as e:
            self.logger.error(f"Single RSI calculation error: {e}")
            return 50.0
    
    def calculate_atr(self, high: List[float], low: List[float], close: List[float], period: int) -> float:
        """
        Calculate single ATR value (for compatibility)
        
        Args:
            high: High prices list
            low: Low prices list
            close: Close prices list
            period: ATR period
            
        Returns:
            Current ATR value
        """
        try:
            if len(high) < period + 1:
                return 0.001
            
            high_array = np.array(high, dtype=np.float64)
            low_array = np.array(low, dtype=np.float64)
            close_array = np.array(close, dtype=np.float64)
            
            atr_values = self.atr(high_array, low_array, close_array, period)
            
            return float(atr_values[-1])
            
        except Exception as e:
            self.logger.error(f"Single ATR calculation error: {e}")
            return 0.001
    
    def bollinger_bands(self, data: np.ndarray, period: int = 20, std_dev: float = 2.0) -> tuple:
        """
        Calculate Bollinger Bands
        
        Args:
            data: Price data array
            period: Moving average period
            std_dev: Standard deviation multiplier
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        try:
            if len(data) < period:
                return np.full(len(data), np.nan), np.full(len(data), np.nan), np.full(len(data), np.nan)
            
            # Calculate SMA (middle band)
            sma = np.zeros(len(data))
            std = np.zeros(len(data))
            
            for i in range(period - 1, len(data)):
                sma[i] = np.mean(data[i - period + 1:i + 1])
                std[i] = np.std(data[i - period + 1:i + 1])
            
            # Calculate bands
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            # Set initial values to NaN
            sma[:period-1] = np.nan
            upper_band[:period-1] = np.nan
            lower_band[:period-1] = np.nan
            
            return upper_band, sma, lower_band
            
        except Exception as e:
            self.logger.error(f"Bollinger Bands calculation error: {e}")
            nan_array = np.full(len(data), np.nan)
            return nan_array, nan_array, nan_array
    
    def macd(self, data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            data: Price data array
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        try:
            if len(data) < slow:
                nan_array = np.full(len(data), np.nan)
                return nan_array, nan_array, nan_array
            
            # Calculate EMAs
            ema_fast = self.ema(data, fast)
            ema_slow = self.ema(data, slow)
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line
            signal_line = self.ema(macd_line[~np.isnan(macd_line)], signal)
            
            # Align signal line with MACD line
            aligned_signal = np.full(len(data), np.nan)
            valid_start = slow - 1 + signal - 1
            if valid_start < len(data) and len(signal_line) > 0:
                end_idx = min(valid_start + len(signal_line), len(data))
                aligned_signal[valid_start:end_idx] = signal_line[:end_idx - valid_start]
            
            # Calculate histogram
            histogram = macd_line - aligned_signal
            
            return macd_line, aligned_signal, histogram
            
        except Exception as e:
            self.logger.error(f"MACD calculation error: {e}")
            nan_array = np.full(len(data), np.nan)
            return nan_array, nan_array, nan_array
