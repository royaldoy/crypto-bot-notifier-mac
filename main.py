import threading
from pystray import Icon as TrayIcon, Menu, MenuItem as Item
from PIL import Image
from time import sleep
from pycoingecko import CoinGeckoAPI
import pandas as pd
import ta
from datetime import datetime
import os
import logging
import subprocess

# === Konfigurasi ===
cg = CoinGeckoAPI()
monthly_budget_idr = 6_000_000
coins = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "tether": "USDT",
    "binancecoin": "BNB",
    "solana": "SOL",
    "usd-coin": "USDC",
    "ripple": "XRP",
    "dogecoin": "DOGE",
    "toncoin": "TON",
    "cardano": "ADA",
    "avalanche-2": "AVAX",
    "shiba-inu": "SHIB",
    "polkadot": "DOT",
    "tron": "TRX",
    "chainlink": "LINK",
    "wrapped-bitcoin": "WBTC",
    "uniswap": "UNI",
    "internet-computer": "ICP",
    "litecoin": "LTC",
    "polygon": "MATIC",
    "dai": "DAI",
    "near": "NEAR",
    "ethereum-classic": "ETC",
    "aptos": "APT",
    "leo-token": "LEO",
    "monero": "XMR",
    "stellar": "XLM",
    "injective-protocol": "INJ",
    "okb": "OKB",
    "arbitrum": "ARB",
    "vechain": "VET",
    "mantle": "MNT",
    "maker": "MKR",
    "filecoin": "FIL",
    "the-graph": "GRT",
    "hedera-hashgraph": "HBAR",
    "render-token": "RNDR",
    "algorand": "ALGO",
    "quant-network": "QNT",
    "sui": "SUI",
    "rocket-pool": "RPL",
    "mina-protocol": "MINA",
    "theta-token": "THETA",
    "kaspa": "KAS",
    "flow": "FLOW",
    "gala": "GALA",
    "axie-infinity": "AXS",
    "bittorrent": "BTT",
    "aave": "AAVE",
    "synthetix-network-token": "SNX"
}

each_allocation = monthly_budget_idr // len(coins)
total_spent = 0
tray = None
latest_signal_log = "Belum ada sinyal terbaru."

# === Logging ===
LOG_FILE = "crypto-bot.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

def log_print(msg):
    global latest_signal_log
    print(msg)
    logging.info(msg)
    latest_signal_log = msg

# === Notifikasi ===
def notify(title, message):
    subprocess.run([
        "osascript",
        "-e",
        f'display notification "{message}" with title "{title}"'
    ])

# === Data dan Sinyal ===
def fetch_data(coin_id, days=90):
    try:
        data = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency='usd', days=days, interval='daily')
        prices = data['prices']
        volumes = data.get('total_volumes', [[x[0], 1] for x in prices])
        df = pd.DataFrame(prices, columns=["timestamp", "Close"])
        df["volume"] = [v[1] for v in volumes]
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
        df.set_index("timestamp", inplace=True)
        return df
    except Exception as e:
        log_print(f"{coin_id}: Gagal ambil data: {e}")
        return None

def check_buy_signal(df):
    try:
        if len(df) < 35:
            return False, "❌ Data terlalu pendek (minimal 35 hari)"

        if "volume" not in df.columns:
            df["volume"] = 1

        # Indikator teknikal
        df["rsi"] = ta.momentum.RSIIndicator(close=df["Close"]).rsi()
        macd = ta.trend.MACD(close=df["Close"])
        df["macd_diff"] = macd.macd_diff()
        df["sma5"] = ta.trend.SMAIndicator(close=df["Close"], window=5).sma_indicator()
        df["low_support"] = df["Close"].rolling(window=5).min()

        df.dropna(inplace=True)
        if len(df) < 3:
            return False, "❌ Data indikator belum valid"

        rsi_prev, rsi_curr = df["rsi"].iloc[-2], df["rsi"].iloc[-1]
        macd_prev, macd_curr = df["macd_diff"].iloc[-2], df["macd_diff"].iloc[-1]
        vol_prev, vol_curr = df["volume"].iloc[-2], df["volume"].iloc[-1]

        rsi_ok = rsi_prev < 30 and rsi_curr > rsi_prev
        macd_ok = macd_prev < 0 and macd_curr > 0
        volume_ok = vol_curr > vol_prev * 1.1

        if rsi_ok and macd_ok and volume_ok:
            low = df["low_support"].iloc[-1]
            sma = df["sma5"].iloc[-1]
            buy_range = f"${low:.2f} - ${sma:.2f}"
            reason = (
                f"✅ RSI rebound ({rsi_prev:.2f}→{rsi_curr:.2f}), "
                f"MACD crossover ({macd_prev:.5f}→{macd_curr:.5f}), "
                f"volume naik ({vol_prev:.2f}→{vol_curr:.2f})\n"
                f"💰 Rekomendasi Buy Limit di range: {buy_range}"
            )
            return True, reason
        else:
            reasons = []
            if not rsi_ok:
                reasons.append(f"RSI belum rebound ({rsi_curr:.2f})")
            if not macd_ok:
                reasons.append(f"MACD belum crossover ({macd_curr:.5f})")
            if not volume_ok:
                reasons.append(f"Volume belum naik ({vol_curr:.2f})")
            return False, "❌ " + ", ".join(reasons)
    except Exception as e:
        return False, f"❌ Error analisis teknikal: {e}"

# === Icon ===
def load_icon(path):
    return Image.open(path)

def update_tray_icon(color):
    if tray:
        icon_path = "icon-green.png" if color == "green" else "icon-red.png"
        tray.icon = load_icon(icon_path)

# === Aksi Tray ===
def open_log(icon, item):
    os.system(f"open -a TextEdit {LOG_FILE}")

def show_last_log(icon, item):
    notify("Log Terakhir", latest_signal_log)

def quit_app(icon, item):
    icon.stop()

# === Loop Bot ===
def bot_loop():
    global total_spent
    while True:
        log_print(f"\n== Update sinyal beli kripto [CoinGecko] ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ==")
        any_signal = False

        for coin_id, symbol in coins.items():
            df = fetch_data(coin_id)
            if df is not None:
                signal, reason = check_buy_signal(df)
                if signal:
                    total_spent += each_allocation
                    log_message = f"{symbol}: 💹 BELI → Rp{each_allocation:,} | {reason}"
                    log_print(log_message)
                    notify(f"Sinyal BELI {symbol}", reason)
                    any_signal = True
                else:
                    log_print(f"{symbol}: ❌ TIDAK BELI → {reason}")
            else:
                log_print(f"{symbol}: Data tidak cukup atau kosong.")

        remaining = monthly_budget_idr - total_spent
        log_print(f"💰 Total Terpakai: Rp{total_spent:,} | Sisa Budget: Rp{remaining:,}")
        update_tray_icon("green" if any_signal else "red")
        sleep(600)

# === Mulai Tray ===
def start_tray():
    global tray
    tray_menu = Menu(
        Item('📄 Buka Log', open_log),
        Item('🕒 Log Terakhir', show_last_log),
        Item('❌ Keluar', quit_app)
    )
    tray = TrayIcon("CryptoBot", load_icon("icon-red.png"), menu=tray_menu)
    threading.Thread(target=bot_loop, daemon=True).start()
    tray.run()

if __name__ == "__main__":
    start_tray()
