import MetaTrader5 as mt5
import time
import datetime
import numpy as np
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import requests
import csv
import os

# ======================
# Konfigurasi Awal
# ======================
TELEGRAM_BOT_TOKEN = "TOKEN"
TELEGRAM_CHAT_ID = "CHAT_ID"
TP_PERSEN_DEFAULT = 0.01
SL_PERSEN_DEFAULT = 0.05
MAX_ORDER_PER_SESSION = 10
RESET_ORDER_HOUR = 0
SALDO_MINIMAL = 1000
LONJAKAN_THRESHOLD = 10
SKOR_MINIMAL = 4

order_counter = 0
last_reset_date = datetime.date.today()
running = False
last_price = None

# ======================
# GUI Setup
# ======================
root = tk.Tk()
root.title("Trading Bot Aman Cuan")

symbol_var = tk.StringVar(value="XAUUSDm")
lot_var = tk.StringVar(value="0.01")
interval_var = tk.StringVar(value="10")
tp_var = tk.StringVar(value=str(TP_PERSEN_DEFAULT * 100))
sl_var = tk.StringVar(value=str(SL_PERSEN_DEFAULT * 100))

frame = tk.Frame(root)
frame.pack(pady=5)

for i, (label, var) in enumerate([
    ("Symbol:", symbol_var),
    ("Lot:", lot_var),
    ("Interval:", interval_var),
    ("TP (%):", tp_var),
    ("SL (%):", sl_var)
]):
    tk.Label(frame, text=label).grid(row=0, column=i*2)
    tk.Entry(frame, textvariable=var).grid(row=0, column=i*2+1)

start_button = tk.Button(root, text="Start", bg="green", fg="white")
stop_button = tk.Button(root, text="Stop", bg="red", fg="white")
start_button.pack(pady=2)
stop_button.pack(pady=2)
log_box = ScrolledText(root, width=100, height=20)
log_box.pack(pady=10)

# ======================
# Logging dan Telegram
# ======================
def log_to_file(text):
    with open("log_trading.txt", "a") as f:
        f.write(f"{datetime.datetime.now()} - {text}\n")

def log(text):
    timestamp = f"{datetime.datetime.now():%H:%M:%S}"
    log_box.insert(tk.END, f"{timestamp} - {text}\n")
    log_box.see(tk.END)
    log_to_file(text)

def send_telegram(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    except:
        pass

# ======================
# Analisa Teknis
# ======================
def get_ma(symbol, period=10):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, period)
    return np.mean([r['close'] for r in rates]) if rates is not None and len(rates) == period else None

def get_ema(symbol, period=50):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, period+1)
    if rates is None or len(rates) < period:
        return None
    prices = np.array([r['close'] for r in rates])
    weights = np.exp(np.linspace(-1., 0., period))
    weights /= weights.sum()
    return np.convolve(prices, weights, mode='valid')[-1]

def get_wma(symbol, period=5):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, period)
    if rates is None or len(rates) < period:
        return None
    prices = np.array([r['close'] for r in rates])
    weights = np.arange(1, period+1)
    return np.dot(prices, weights) / weights.sum()

def get_rsi(symbol, period=14):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, period+1)
    if rates is None or len(rates) < period+1:
        return None
    close = np.array([r['close'] for r in rates])
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.mean(gain)
    avg_loss = np.mean(loss)
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    return 100 - (100 / (1 + rs))

def get_bollinger_bands(symbol, period=20):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, period)
    if rates is None or len(rates) < period:
        return None, None
    close = np.array([r['close'] for r in rates])
    sma = np.mean(close)
    std = np.std(close)
    return sma + (2 * std), sma - (2 * std)

def is_symbol_active(symbol):
    info = mt5.symbol_info(symbol)
    return False if info is None else (mt5.symbol_select(symbol, True) if not info.visible else True)

def get_total_open_orders():
    positions = mt5.positions_get()
    return len(positions) if positions else 0

# ======================
# Bot Utama
# ======================
def stop_bot():
    global running
    running = False

def trading_bot():
    global running, order_counter, last_reset_date, last_price
    running = True
    symbol = symbol_var.get()

    try:
        lot = float(lot_var.get())
        interval = int(interval_var.get())
        TP_PERSEN = float(tp_var.get()) / 100
        SL_PERSEN = float(sl_var.get()) / 100
    except ValueError:
        log("Input tidak valid.")
        return

    if not mt5.initialize():
        log("MT5 gagal inisialisasi.")
        return

    if not is_symbol_active(symbol):
        log(f"Symbol '{symbol}' tidak aktif!")
        return

    account = mt5.account_info()
    if account:
        log(f"Login: {account.login} | Balance: {account.balance:.2f}")
    else:
        log("Gagal ambil info akun!")

    while running:
        now = datetime.datetime.now()
        if now.hour == RESET_ORDER_HOUR and now.date() != last_reset_date:
            order_counter = 0
            last_reset_date = now.date()
            log("Counter order direset.")

        if get_total_open_orders() >= MAX_ORDER_PER_SESSION:
            log("Order aktif penuh, menunggu...")
            time.sleep(interval)
            continue

        tick = mt5.symbol_info_tick(symbol)
        if not tick or tick.ask == 0.0:
            log("Gagal ambil harga")
            time.sleep(interval)
            continue

        harga = tick.ask
        if last_price is not None and abs(harga - last_price) > LONJAKAN_THRESHOLD:
            log("Lonjakan harga terdeteksi, skip 1 cycle")
            last_price = harga
            time.sleep(interval)
            continue

        last_price = harga
        ma10 = get_ma(symbol)
        ema9 = get_ema(symbol, 9)
        ema21 = get_ema(symbol, 21)
        ema50 = get_ema(symbol, 50)
        wma5 = get_wma(symbol, 5)
        wma10 = get_wma(symbol, 10)
        rsi = get_rsi(symbol)
        bb_upper, bb_lower = get_bollinger_bands(symbol)

        if None in [ma10, ema9, ema21, ema50, wma5, wma10, rsi, bb_upper, bb_lower]:
            log("Gagal ambil data indikator")
            time.sleep(interval)
            continue

        log(f"Harga: {harga:.2f} | MA10: {ma10:.2f} | EMA9: {ema9:.2f} | EMA21: {ema21:.2f} | EMA50: {ema50:.2f} | WMA5: {wma5:.2f} | WMA10: {wma10:.2f} | RSI: {rsi:.2f}")

        sinyal = None
        skor_buy = sum([
            rsi >= 20,
            harga > ema50,
            harga > ema9,
            ema9 > ema21,
            harga > wma5,
            harga < bb_upper
        ])
        skor_sell = sum([
            rsi <= 80,
            harga < ema50,
            harga < ema9,
            ema9 < ema21,
            harga < wma5,
            harga > bb_lower
        ])

        if skor_buy >= SKOR_MINIMAL:
            sinyal = "BUY"
            sl = harga * (1 - SL_PERSEN)
            tp = harga * (1 + TP_PERSEN)
            order_type = mt5.ORDER_TYPE_BUY
        elif skor_sell >= SKOR_MINIMAL:
            sinyal = "SELL"
            sl = harga * (1 + SL_PERSEN)
            tp = harga * (1 - TP_PERSEN)
            order_type = mt5.ORDER_TYPE_SELL
        else:
            log("Sinyal tidak valid, menunggu...")
            time.sleep(interval)
            continue

        if account.balance < SALDO_MINIMAL:
            log("Saldo terlalu rendah.")
            time.sleep(interval)
            continue

        order = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": harga,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 123456,
            "comment": f"Order {sinyal} dari Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(order)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            log(f"Gagal order {sinyal}: {result.retcode}")
            send_telegram(f"Gagal order {sinyal}: {result.retcode}")
        else:
            order_counter += 1
            log(f"Order {sinyal} berhasil! Harga: {harga:.2f}")
            send_telegram(f"Order {sinyal} berhasil! Harga: {harga:.2f}")

        time.sleep(interval)

    mt5.shutdown()
    log("Bot dihentikan.")

start_button.config(command=lambda: threading.Thread(target=trading_bot).start())
stop_button.config(command=stop_bot)
root.mainloop()
