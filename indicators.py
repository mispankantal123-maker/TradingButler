"""
Technical Indicators Module
Accurate calculations for EMA, RSI, ATR and other indicators
"""

import numpy as np
import pandas as pd
from typing import List, Optional
import logging

class TechnicalIndicators:
    """Technical indicators calculator"""
    
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
                return np.array([])
            
            # Calculate smoothing factor
            alpha = 2.0 / (period + 1)
            
            # Initialize EMA array
            ema_values = np.zeros_like(data)
            
            # First EMA value is SMA of first 'period' values
            ema_values[period-1] = np.mean(data[:period])
            
            # Calculate subsequent EMA values
            for i in range(period, len(data)):
                ema_values[i] = alpha * data[i] + (1 - alpha) * ema_values[i-1]
            
            return ema_values[period-1:]
            
        except Exception as e:
            self.logger.error(f"EMA calculation error: {e}")
            return np.array([])
    
    def sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Simple Moving Average
        
        Args:
            data: Price data array
            period: SMA period
            
        Returns:
            SMA values array
        """
        try:
            if len(data) < period:
                return np.array([])
            
            sma_values = []
            for i in range(period-1, len(data)):
                sma_values.append(np.mean(data[i-period+1:i+1]))
            
            return np.array(sma_values)
            
        except Exception as e:
            self.logger.error(f"SMA calculation error: {e}")
            return np.array([])
    
    def rsi(self, data: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calculate Relative Strength Index
        
        Args:
            data: Price data array
            period: RSI period
            
        Returns:
            RSI values array
        """
        try:
            if len(data) < period + 1:
                return np.array([])
            
            # Calculate price changes
            deltas = np.diff(data)
            
            # Separate gains and losses
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Calculate initial average gain and loss
            avg_gain = np.mean(gains[:period])
            avg_loss = np.mean(losses[:period])
            
            rsi_values = []
            
            # Calculate first RSI value
            if avg_loss != 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 100
            rsi_values.append(rsi)
            
            # Calculate subsequent RSI values using Wilder's smoothing
            for i in range(period, len(deltas)):
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
                
                if avg_loss != 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                else:
                    rsi = 100
                
                rsi_values.append(rsi)
            
            return np.array(rsi_values)
            
        except Exception as e:
            self.logger.error(f"RSI calculation error: {e}")
            return np.array([])
    
    def atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calculate Average True Range
        
        Args:
            high: High prices array
            low: Low prices array
            close: Close prices array
            period: ATR period
            
        Returns:
            ATR values array
        """
        try:
            if len(high) != len(low) or len(low) != len(close):
                raise ValueError("Price arrays must have same length")
            
            if len(high) < period + 1:
                return np.array([])
            
            # Calculate True Range
            tr_values = []
            
            for i in range(1, len(high)):
                tr1 = high[i] - low[i]  # Current high - current low
                tr2 = abs(high[i] - close[i-1])  # Current high - previous close
                tr3 = abs(low[i] - close[i-1])   # Current low - previous close
                
                tr = max(tr1, tr2, tr3)
                tr_values.append(tr)
            
            tr_array = np.array(tr_values)
            
            # Calculate ATR using Wilder's smoothing
            atr_values = []
            
            # First ATR is simple average of first 'period' TR values
            atr = np.mean(tr_array[:period])
            atr_values.append(atr)
            
            # Subsequent ATR values use Wilder's smoothing
            for i in range(period, len(tr_array)):
                atr = (atr * (period - 1) + tr_array[i]) / period
                atr_values.append(atr)
            
            return np.array(atr_values)
            
        except Exception as e:
            self.logger.error(f"ATR calculation error: {e}")
            return np.array([])
    
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
                return np.array([]), np.array([]), np.array([])
            
            # Calculate middle band (SMA)
            middle_band = self.sma(data, period)
            
            # Calculate standard deviation
            std_values = []
            for i in range(period-1, len(data)):
                std_val = np.std(data[i-period+1:i+1])
                std_values.append(std_val)
            
            std_array = np.array(std_values)
            
            # Calculate upper and lower bands
            upper_band = middle_band + (std_dev * std_array)
            lower_band = middle_band - (std_dev * std_array)
            
            return upper_band, middle_band, lower_band
            
        except Exception as e:
            self.logger.error(f"Bollinger Bands calculation error: {e}")
            return np.array([]), np.array([]), np.array([])
    
    def macd(self, data: np.ndarray, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> tuple:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            data: Price data array
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        try:
            if len(data) < slow_period:
                return np.array([]), np.array([]), np.array([])
            
            # Calculate fast and slow EMAs
            ema_fast = self.ema(data, fast_period)
            ema_slow = self.ema(data, slow_period)
            
            # Align arrays (slow EMA starts later)
            start_idx = slow_period - fast_period
            ema_fast_aligned = ema_fast[start_idx:]
            
            # Calculate MACD line
            macd_line = ema_fast_aligned - ema_slow
            
            # Calculate signal line
            signal_line = self.ema(macd_line, signal_period)
            
            # Calculate histogram
            macd_aligned = macd_line[signal_period-1:]
            histogram = macd_aligned - signal_line
            
            return macd_line, signal_line, histogram
            
        except Exception as e:
            self.logger.error(f"MACD calculation error: {e}")
            return np.array([]), np.array([]), np.array([])
    
    def stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, 
                  k_period: int = 14, d_period: int = 3) -> tuple:
        """
        Calculate Stochastic Oscillator
        
        Args:
            high: High prices array
            low: Low prices array
            close: Close prices array
            k_period: %K period
            d_period: %D period
            
        Returns:
            Tuple of (%K, %D)
        """
        try:
            if len(high) < k_period:
                return np.array([]), np.array([])
            
            k_values = []
            
            for i in range(k_period-1, len(close)):
                period_high = np.max(high[i-k_period+1:i+1])
                period_low = np.min(low[i-k_period+1:i+1])
                
                if period_high != period_low:
                    k = ((close[i] - period_low) / (period_high - period_low)) * 100
                else:
                    k = 50  # Neutral when no range
                
                k_values.append(k)
            
            k_array = np.array(k_values)
            
            # Calculate %D (SMA of %K)
            d_array = self.sma(k_array, d_period)
            
            return k_array, d_array
            
        except Exception as e:
            self.logger.error(f"Stochastic calculation error: {e}")
            return np.array([]), np.array([])
    
    def williams_r(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calculate Williams %R
        
        Args:
            high: High prices array
            low: Low prices array
            close: Close prices array
            period: Calculation period
            
        Returns:
            Williams %R values array
        """
        try:
            if len(high) < period:
                return np.array([])
            
            wr_values = []
            
            for i in range(period-1, len(close)):
                period_high = np.max(high[i-period+1:i+1])
                period_low = np.min(low[i-period+1:i+1])
                
                if period_high != period_low:
                    wr = ((period_high - close[i]) / (period_high - period_low)) * -100
                else:
                    wr = -50  # Neutral when no range
                
                wr_values.append(wr)
            
            return np.array(wr_values)
            
        except Exception as e:
            self.logger.error(f"Williams %R calculation error: {e}")
            return np.array([])
"""
Technical Indicators Module
Implements EMA, RSI, and ATR calculations for trading strategy
"""

import numpy as np
from typing import Union, List
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Technical indicators calculator for trading strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def ema(self, data: Union[np.ndarray, List[float]], period: int) -> np.ndarray:
        """
        Calculate Exponential Moving Average (EMA)
        
        Args:
            data: Price data array
            period: EMA period
            
        Returns:
            np.ndarray: EMA values
        """
        try:
            data = np.array(data, dtype=np.float64)
            if len(data) < period:
                return np.array([])
            
            # Calculate smoothing factor
            alpha = 2.0 / (period + 1)
            
            # Initialize EMA array
            ema_values = np.zeros_like(data)
            ema_values[0] = data[0]
            
            # Calculate EMA
            for i in range(1, len(data)):
                ema_values[i] = alpha * data[i] + (1 - alpha) * ema_values[i-1]
            
            return ema_values
            
        except Exception as e:
            self.logger.error(f"Error calculating EMA: {e}")
            return np.array([])
    
    def sma(self, data: Union[np.ndarray, List[float]], period: int) -> np.ndarray:
        """
        Calculate Simple Moving Average (SMA)
        
        Args:
            data: Price data array
            period: SMA period
            
        Returns:
            np.ndarray: SMA values
        """
        try:
            data = np.array(data, dtype=np.float64)
            if len(data) < period:
                return np.array([])
            
            # Calculate SMA using convolution
            sma_values = np.convolve(data, np.ones(period)/period, mode='valid')
            
            # Pad with NaN for consistency
            result = np.full(len(data), np.nan)
            result[period-1:] = sma_values
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating SMA: {e}")
            return np.array([])
    
    def rsi(self, data: Union[np.ndarray, List[float]], period: int = 14) -> np.ndarray:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            data: Price data array
            period: RSI period (default 14)
            
        Returns:
            np.ndarray: RSI values
        """
        try:
            data = np.array(data, dtype=np.float64)
            if len(data) < period + 1:
                return np.array([])
            
            # Calculate price changes
            delta = np.diff(data)
            
            # Separate gains and losses
            gains = np.where(delta > 0, delta, 0)
            losses = np.where(delta < 0, -delta, 0)
            
            # Calculate average gains and losses
            avg_gains = np.zeros(len(gains))
            avg_losses = np.zeros(len(losses))
            
            # Initial averages (simple average for first period)
            avg_gains[period-1] = np.mean(gains[:period])
            avg_losses[period-1] = np.mean(losses[:period])
            
            # Calculate exponential averages
            for i in range(period, len(gains)):
                avg_gains[i] = (avg_gains[i-1] * (period-1) + gains[i]) / period
                avg_losses[i] = (avg_losses[i-1] * (period-1) + losses[i]) / period
            
            # Calculate RSI
            rsi_values = np.full(len(data), np.nan)
            
            for i in range(period, len(data)):
                if avg_losses[i-1] == 0:
                    rsi_values[i] = 100
                else:
                    rs = avg_gains[i-1] / avg_losses[i-1]
                    rsi_values[i] = 100 - (100 / (1 + rs))
            
            return rsi_values
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return np.array([])
    
    def atr(self, high: Union[np.ndarray, List[float]], 
            low: Union[np.ndarray, List[float]], 
            close: Union[np.ndarray, List[float]], 
            period: int = 14) -> np.ndarray:
        """
        Calculate Average True Range (ATR)
        
        Args:
            high: High price data
            low: Low price data  
            close: Close price data
            period: ATR period (default 14)
            
        Returns:
            np.ndarray: ATR values
        """
        try:
            high = np.array(high, dtype=np.float64)
            low = np.array(low, dtype=np.float64)
            close = np.array(close, dtype=np.float64)
            
            if len(high) != len(low) or len(low) != len(close):
                raise ValueError("High, low, and close arrays must have same length")
            
            if len(close) < period + 1:
                return np.array([])
            
            # Calculate True Range components
            tr1 = high - low
            tr2 = np.abs(high - np.roll(close, 1))
            tr3 = np.abs(low - np.roll(close, 1))
            
            # True Range is the maximum of the three
            true_range = np.maximum(tr1, np.maximum(tr2, tr3))
            
            # Set first TR value (no previous close)
            true_range[0] = high[0] - low[0]
            
            # Calculate ATR using EMA of True Range
            atr_values = self.ema(true_range, period)
            
            return atr_values
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return np.array([])
    
    def bollinger_bands(self, data: Union[np.ndarray, List[float]], 
                       period: int = 20, std_dev: float = 2.0) -> tuple:
        """
        Calculate Bollinger Bands
        
        Args:
            data: Price data array
            period: Period for moving average
            std_dev: Standard deviation multiplier
            
        Returns:
            tuple: (upper_band, middle_band, lower_band)
        """
        try:
            data = np.array(data, dtype=np.float64)
            if len(data) < period:
                return np.array([]), np.array([]), np.array([])
            
            # Calculate SMA (middle band)
            middle_band = self.sma(data, period)
            
            # Calculate standard deviation
            std_values = np.full(len(data), np.nan)
            for i in range(period-1, len(data)):
                std_values[i] = np.std(data[i-period+1:i+1])
            
            # Calculate upper and lower bands
            upper_band = middle_band + (std_dev * std_values)
            lower_band = middle_band - (std_dev * std_values)
            
            return upper_band, middle_band, lower_band
            
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return np.array([]), np.array([]), np.array([])
    
    def macd(self, data: Union[np.ndarray, List[float]], 
             fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> tuple:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            data: Price data array
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            
        Returns:
            tuple: (macd_line, signal_line, histogram)
        """
        try:
            data = np.array(data, dtype=np.float64)
            if len(data) < slow_period:
                return np.array([]), np.array([]), np.array([])
            
            # Calculate fast and slow EMAs
            fast_ema = self.ema(data, fast_period)
            slow_ema = self.ema(data, slow_period)
            
            # Calculate MACD line
            macd_line = fast_ema - slow_ema
            
            # Calculate signal line
            signal_line = self.ema(macd_line, signal_period)
            
            # Calculate histogram
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return np.array([]), np.array([]), np.array([])
    
    def stochastic(self, high: Union[np.ndarray, List[float]], 
                   low: Union[np.ndarray, List[float]], 
                   close: Union[np.ndarray, List[float]], 
                   k_period: int = 14, d_period: int = 3) -> tuple:
        """
        Calculate Stochastic Oscillator
        
        Args:
            high: High price data
            low: Low price data
            close: Close price data
            k_period: %K period
            d_period: %D period
            
        Returns:
            tuple: (%K, %D)
        """
        try:
            high = np.array(high, dtype=np.float64)
            low = np.array(low, dtype=np.float64)
            close = np.array(close, dtype=np.float64)
            
            if len(high) != len(low) or len(low) != len(close):
                raise ValueError("High, low, and close arrays must have same length")
            
            if len(close) < k_period:
                return np.array([]), np.array([])
            
            # Calculate %K
            k_values = np.full(len(close), np.nan)
            
            for i in range(k_period-1, len(close)):
                highest_high = np.max(high[i-k_period+1:i+1])
                lowest_low = np.min(low[i-k_period+1:i+1])
                
                if highest_high != lowest_low:
                    k_values[i] = 100 * (close[i] - lowest_low) / (highest_high - lowest_low)
                else:
                    k_values[i] = 50
            
            # Calculate %D (SMA of %K)
            d_values = self.sma(k_values, d_period)
            
            return k_values, d_values
            
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic: {e}")
            return np.array([]), np.array([])
