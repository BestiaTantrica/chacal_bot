import os
import sqlite3
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime

# Configuración
DB_FILES = {
    "ALPHA": "user_data/tradesv3_alpha_dry.sqlite",
    "BETA": "user_data/tradesv3_beta_dry.sqlite",
    "GAMMA": "user_data/tradesv3_gamma_dry.sqlite",
    "DELTA": "user_data/tradesv3_delta_dry.sqlite"
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_tg_credentials():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, val = line.strip().split("=", 1)
                        if key == "TELEGRAM_TOKEN": token = val
                        if key == "TELEGRAM_CHAT_ID": chat_id = val
    return token, chat_id

def call_tg(method, params, token):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(params).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except: return None

def send_telegram(msg, token, chat_id):
    params = {"chat_id": chat_id, "text": f"<code>{msg}</code>", "parse_mode": "HTML"}
    call_tg("sendMessage", params, token)

def analyze_bot(name, db_path):
    if not os.path.exists(db_path): return {"name": name, "status": "OFF"}
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT close_profit_abs FROM trades WHERE is_open=0")
        closed = [t[0] for t in c.fetchall() if t[0]]
        c.execute("SELECT pair, is_short, open_rate FROM trades WHERE is_open=1")
        open_trades = c.fetchall()
        conn.close()
        return {"name": name, "profit": sum(closed), "trades": len(closed), "open": open_trades}
    except: return {"name": name, "status": "ERR"}

def cmd_status():
    out = "ESTADO DE FLOTA\n"
    out += "---------------\n"
    any_open = False
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data.get("open"):
            any_open = True
            out += f"BOT {name}:\n"
            for op in data["open"]:
                side = "S" if op[1] else "L"
                out += f"  {op[0]} {side} @ {op[2]:.4f}\n"
    if not any_open: out += "Sin ops abiertas.\n"
    return out

def cmd_report():
    out = "REPORTE RENDIMIENTO\n"
    out += "-------------------\n"
    total_p = 0
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        p = data.get("profit", 0)
        total_p += p
        out += f"{name}: ${p:+.2f} ({data.get('trades',0)} t)\n"
    out += "-------------------\n"
    out += f"TOTAL: ${total_p:+.2f}\n"
    return out

def cmd_balance():
    cap = 300.0
    total_p = sum(analyze_bot(n, p).get("profit", 0) for n, p in DB_FILES.items())
    out = "BALANCE DRY RUN\n"
    out += "---------------\n"
    out += f"Inicial: $300.00\n"
    out += f"Profit:  ${total_p:+.2f}\n"
    out += f"Actual:  ${cap + total_p:.2f}\n"
    out += f"Var:     {(total_p/cap*100):+.2f}%\n"
    return out

def run_conserje():
    token, chat_id = get_tg_credentials()
    if not token or not chat_id: return
    log("Conserje v4 SECO iniciado.")
    
    last_update_id = 0
    while True:
        try:
            updates = call_tg("getUpdates", {"offset": last_update_id + 1, "timeout": 10}, token)
            if updates and updates.get("ok"):
                for up in updates.get("result", []):
                    last_update_id = up.get("update_id")
                    msg = up.get("message", {})
                    text = msg.get("text", "").lower()
                    if str(msg.get("chat", {}).get("id")) != str(chat_id): continue
                    
                    if "status" in text or "estado" in text:
                        send_telegram(cmd_status(), token, chat_id)
                    elif "report" in text or "reporte" in text:
                        send_telegram(cmd_report(), token, chat_id)
                    elif "balance" in text:
                        send_telegram(cmd_balance(), token, chat_id)
                    elif "ping" in text:
                        send_telegram("PONG - Chacal Online", token, chat_id)
        except: pass
        time.sleep(2)

if __name__ == "__main__":
    run_conserje()
