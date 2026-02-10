import os
import sqlite3
import time
import json
import urllib.request
from datetime import datetime

# Protocolo Chacal: Conserje Central V4.1
DBS = {
    "ALPHA": "/home/ec2-user/chacal_bot/user_data/tradesv3_alpha_dry.sqlite",
    "BETA": "/home/ec2-user/chacal_bot/user_data/tradesv3_beta_dry.sqlite",
    "GAMMA": "/home/ec2-user/chacal_bot/user_data/tradesv3_gamma_dry.sqlite",
    "DELTA": "/home/ec2-user/chacal_bot/user_data/tradesv3_delta_dry.sqlite"
}

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r: return True
    except: return False

def get_last_id(db):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("SELECT MAX(id) FROM trades")
        res = c.fetchone()[0]
        conn.close()
        return res or 0
    except: return 0

def get_trade_info(db, trade_id):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("SELECT pair, is_open, close_profit_abs, open_rate, close_rate FROM trades WHERE id=?", (trade_id,))
        res = c.fetchone()
        conn.close()
        return res
    except: return None

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID: exit()
    print("Conserje Sniper V4 (Monitor) Iniciado...")
    
    # Store last known IDs to only notify NEW trades
    last_ids = {name: get_last_id(path) for name, path in DBS.items()}
    
    while True:
        for name, path in DBS.items():
            current_max = get_last_id(path)
            if current_max > last_ids[name]:
                # New trade detected!
                for tid in range(last_ids[name] + 1, current_max + 1):
                    info = get_trade_info(path, tid)
                    if info:
                        pair, is_open, profit, open_r, close_r = info
                        status = "ABIERTA 🚀" if is_open else "CERRADA ✅"
                        msg = f"<b>[TORRE {name}]</b>\nOperación {status}\nPar: {pair}\n"
                        if not is_open:
                            msg += f"Profit: ${profit:+.2f}\n"
                        send_tg(msg)
                last_ids[name] = current_max
        time.sleep(30)
