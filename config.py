"""
Trading Configuration for MT5 Scalping Bot
CRITICAL: All settings optimized for live trading with real money
"""

# SYMBOL CONFIGURATION
SUPPORTED_SYMBOLS = ["XAUUSD", "XAUUSDm", "XAUUSDc"]
DEFAULT_SYMBOL = "XAUUSD"

# RISK MANAGEMENT (Conservative settings for live trading)
RISK_PERCENT_PER_TRADE = 0.5    # 0.5% risk per trade (conservative)
MAX_DAILY_LOSS_PERCENT = 2.0    # Maximum 2% daily loss
MAX_TRADES_PER_DAY = 10         # Maximum trades per day
MAX_CONSECUTIVE_LOSSES = 3       # Stop after 3 consecutive losses
COOLDOWN_MINUTES = 30           # Cooldown period after max losses

# TECHNICAL ANALYSIS SETTINGS
EMA_PERIODS = {
    'fast': 9,      # Fast EMA for trend detection
    'medium': 21,   # Medium EMA for pullback identification  
    'slow': 50      # Slow EMA for major trend filter
}

RSI_PERIOD = 14                 # RSI period for momentum
ATR_PERIOD = 14                 # ATR period for volatility

# POSITION SIZING
MIN_SL_POINTS = 100             # Minimum stop loss distance (points)
RISK_MULTIPLE = 1.5             # Risk/Reward ratio (1:1.5)
MAX_SPREAD_POINTS = 50          # Maximum allowed spread (points)

# EXECUTION SETTINGS
DEVIATION_POINTS_BASE = 20      # Base deviation for order execution
MAX_RETRIES = 3                 # Maximum order retry attempts
RETRY_DELAY_MS = 100           # Delay between retries (milliseconds)

# TRADING SESSIONS (GMT time)
TRADING_SESSIONS = {
    'london': {
        'start': (8, 0),    # 08:00 GMT
        'end': (17, 0)      # 17:00 GMT
    },
    'new_york': {
        'start': (13, 0),   # 13:00 GMT
        'end': (22, 0)      # 22:00 GMT
    }
}

# AVOID TRADING PERIODS (Low liquidity)
AVOID_PERIODS = [
    ((22, 0), (1, 0)),    # Asian session start/end
    ((17, 0), (18, 0)),   # London close gap
]

# SIGNAL FILTERS (Enhanced for higher winrate)
SIGNAL_FILTERS = {
    'min_volatility': 0.00005,      # Minimum ATR for scalping
    'rsi_overbought': 75,           # RSI overbought level
    'rsi_oversold': 25,             # RSI oversold level
    'trend_strength_min': 0.9999,   # Minimum trend strength ratio
    'pullback_tolerance': 0.0001    # Pullback tolerance from EMA
}

# MAGIC NUMBER for order identification
MAGIC_NUMBER = 987654321

# LOGGING CONFIGURATION
LOG_LEVEL = "INFO"              # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True              # Enable file logging
LOG_TO_TELEGRAM = False         # Enable Telegram notifications

# GUI UPDATE INTERVALS
MARKET_DATA_UPDATE_MS = 1000    # Market data update interval
GUI_REFRESH_MS = 1000           # GUI refresh interval
POSITION_UPDATE_MS = 5000       # Position update interval

# VALIDATION SETTINGS
VALIDATE_ORDERS = True          # Enable order validation
CHECK_MARGIN = True             # Check margin before trading
VERIFY_SYMBOL_SPECS = True      # Verify symbol specifications

# EMERGENCY STOPS
EMERGENCY_STOP_LOSS_PERCENT = 5.0   # Emergency stop at 5% account loss
MAX_DRAWDOWN_PERCENT = 3.0          # Maximum allowed drawdown

# PERFORMANCE OPTIMIZATION
USE_DYNAMIC_DEVIATION = True    # Use ATR-based deviation
OPTIMIZE_LOT_SIZING = True      # Optimize lot size calculation
FAST_EXECUTION_MODE = True      # Enable fast execution mode