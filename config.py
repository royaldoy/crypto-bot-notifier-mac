### config.py
ASSETS = [
    {"symbol": "SOL", "type": "crypto", "id": "solana"},
    {"symbol": "ETH", "type": "crypto", "id": "ethereum"},
    {"symbol": "AVAX", "type": "crypto", "id": "avalanche-2"},
]

INTERVAL_MINUTES = 10
RSI_PERIOD = 14
MA_SHORT = 7
MA_LONG = 21
VOLUME_SPIKE_MULTIPLIER = 1.5
BREAKOUT_LOOKBACK = 5