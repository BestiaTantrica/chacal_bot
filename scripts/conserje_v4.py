import os
import sqlite3
import time
import json
import urllib.request
import urllib.parse
import threading
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('/home/ec2-user/chacal_bot/.env.aws')

DBS = {
    "ALPHA": "/home/ec2-user/chacal_bot/user_data/tradesv3_alpha_dry.sqlite",
    "BETA": "/home/ec2-user/chacal_bot/user_data/tradesv3_beta_dry.sqlite",
    "GAMMA": "/home/ec2-user/chacal_bot/user_data/tradesv3_gamma_dry.sqlite",
    "DELTA": "/home/ec2-user/chacal_bot/user_data/tradesv3_delta_dry.sqlite"
}

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def log(msg):
    print(f"[{datetime.now()}] {msg}", flush=True)

def send_tg(msg):
    if not TOKEN: return False
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r: 
            return True
    except Exception as e:
        log(f"Error sending TG: {e}")
        return False

# --- MONITOR TRADES (SOLO SALIDA) ---
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

def monitor_loop():
    log("Iniciando Monitor Loop (Solo Notificaciones)...")
    last_ids = {name: get_last_id(path) for name, path in DBS.items()}
    
    while True:
        try:
            for name, path in DBS.items():
                if not os.path.exists(path): continue
                current = get_last_id(path)
                if current > last_ids[name]:
                    for tid in range(last_ids[name]+1, current+1):
                        info = get_trade_info(path, tid)
                        if info:
                            pair, is_open, profit, open_r, close_r = info
                            icon = "🚀 APERTURA" if is_open else "✅ CIERRE"
                            msg = f"<b>[{name}] {icon}</b>\nPar: <code>{pair}</code>\n"
                            if not is_open: msg += f"Profit: <b>${profit:+.2f}</b>"
                            send_tg(msg)
                    last_ids[name] = current
        except: pass
        time.sleep(10)

if __name__ == "__main__":
    if not TOKEN: exit(1)
    
    # Start Monitor Thread
    t_mon = threading.Thread(target=monitor_loop)
    t_mon.daemon = True
    t_mon.start()
    
    # Start Vigilante (External Process)
    subprocess.Popen(["python3", "/home/ec2-user/chacal_bot/scripts/vigilante_sniper.py"])
    log("Vigilante Sniper lanzado en paralelo.")
    
    # Mantener vivo el script
    while True: time.sleep(60)
