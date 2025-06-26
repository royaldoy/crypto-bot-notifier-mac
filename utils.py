### utils.py
import json
import os

def log_signal(message):
    os.makedirs("logs", exist_ok=True)
    with open("logs/signal.log", "a") as f:
        f.write(message + "\n")

def load_cache():
    if not os.path.exists("data/history_cache.json"):
        return {}
    with open("data/history_cache.json") as f:
        return json.load(f)

def save_cache(cache):
    os.makedirs("data", exist_ok=True)
    with open("data/history_cache.json", "w") as f:
        json.dump(cache, f)
