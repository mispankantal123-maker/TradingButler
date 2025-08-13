# MT5 Scalping Bot - Installation Guide

## Prerequisites

### 1. MetaTrader 5 Platform
- Download and install MetaTrader 5 from your broker
- Ensure MT5 Python API is enabled in Tools > Options > Expert Advisors
- Allow DLL imports and automated trading

### 2. Python Requirements
Install the following packages:

```bash
pip install MetaTrader5>=5.0.45
pip install PySide6>=6.5.0
pip install pandas>=2.0.0
pip install numpy>=1.24.0
pip install requests>=2.31.0
```

## Installation Steps

### 1. Setup MT5 Connection
1. Open MetaTrader 5
2. Login to your trading account
3. Go to Tools > Options > Expert Advisors
4. Check "Allow DLL imports"
5. Check "Allow automated trading"
6. Check "Allow WebRequest for listed URL"

### 2. Run the Bot
```bash
python main.py
```

### 3. Configuration
1. Click "Connect" to connect to MT5
2. Select symbol (XAUUSD, XAUUSDm, or XAUUSDc)
3. Configure risk settings in Risk Management tab
4. Enable/disable Shadow Mode for testing
5. Click "Start Bot" to begin trading

## Important Notes for Live Trading

### Risk Management
- Default risk per trade: 0.5% of account balance
- Maximum daily loss: 2% of account balance
- Maximum trades per day: 10
- Always test in Shadow Mode first

### Trading Sessions
- Bot trades during London and NY sessions
- Avoids low liquidity periods
- Automatic session detection

### Symbol Configuration
- Supports XAUUSD, XAUUSDm, and XAUUSDc
- Automatically validates symbol availability
- Dynamic spread checking

### Telegram Notifications (Optional)
Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

## Troubleshooting

1. **Connection Failed**: Ensure MT5 is running and logged in
2. **Symbol Not Found**: Check symbol availability with your broker
3. **Order Execution Failed**: Verify account permissions and margin
4. **High Spread**: Bot automatically skips trades during high spread periods

## Support

For issues related to:
- MT5 connection: Check MT5 settings and account permissions
- Trading performance: Review risk settings and market conditions
- Technical issues: Check logs in the Logs tab