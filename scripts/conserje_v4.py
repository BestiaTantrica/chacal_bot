import os
import sqlite3
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime
from collections import defaultdict

# Configuración
CHECK_INTERVAL = 300  # 5 minutos (sin autospam)
DB_FILES = {
    "ALPHA": "user_data/tradesv3_alpha_dry.sqlite",
    "BETA": "user_data/tradesv3_beta_dry.sqlite",
    "GAMMA": "user_data/tradesv3_gamma_dry.sqlite",
    "DELTA": "user_data/tradesv3_delta_dry.sqlite"
}
STATE_FILE = "user_data/conserje_dry_state.json"

def log(msg):
    print(f"[{datetime.now()}] [CONSERJE-DRY] {msg}", flush=True)

def get_tg_credentials():
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    return token, chat_id

def call_tg(method, params, token):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(params).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return None

def send_telegram(msg, token, chat_id, keyboard=None):
    full_msg = f"*CHACAL DRY RUN*\\n\\n{msg}"
    params = {"chat_id": chat_id, "text": full_msg, "parse_mode": "Markdown"}
    if keyboard:
        params["reply_markup"] = keyboard
    call_tg("sendMessage", params, token)

def get_keyboard():
    return {
        "keyboard": [
            [{"text": "Estado"}, {"text": "Reporte"}],
            [{"text": "Hoy"}, {"text": "Detalle"}],
            [{"text": "Balance"}, {"text": "Ping"}]
        ],
        "resize_keyboard": True
    }

def analyze_bot(name, db_path):
    if not os.path.exists(db_path):
        return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0, "status": "OFF"}
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT pair, close_profit, close_profit_abs FROM trades WHERE is_open=0")
        trades = c.fetchall()
        c.execute("SELECT COUNT(*) FROM trades WHERE is_open=1")
        open_trades = c.fetchone()[0]
        conn.close()
        
        if not trades:
            return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0, "open_trades": open_trades, "status": "IDLE"}
        
        total = len(trades)
        wins = len([t for t in trades if t[1] and t[1] > 0])
        win_rate = (wins / total * 100) if total > 0 else 0
        profit_abs = sum(t[2] for t in trades if t[2])
        return {"name": name, "total": total, "profit_abs": profit_abs, "win_rate": win_rate, "open_trades": open_trades, "status": "OK"}
    except:
        return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0, "status": "ERR"}

def cmd_estado():
    report = "*ESTADO DE LAS TORRES*\\n\\n"
    active_ops = ""
    idle_bots = []
    
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data.get("open_trades", 0) > 0:
            try:
                conn = sqlite3.connect(path)
                c = conn.cursor()
                c.execute("SELECT pair, is_short, open_rate FROM trades WHERE is_open=1")
                rows = c.fetchall()
                conn.close()
                active_ops += f"[*] *{name}*:\\n"
                for r in rows:
                    side = "SHORT" if r[1] else "LONG"
                    active_ops += f"  - {side} {r[0]} @ {r[2]}\\n"
                active_ops += "\\n"
            except:
                pass
        else:
            idle_bots.append(name)
    
    if active_ops:
        report += active_ops
    else:
        report += "Sin operaciones abiertas.\\n\\n"
        
    if idle_bots:
        report += "Buscando entrada: " + ", ".join(idle_bots) + "\\n"
        
    return report

def cmd_reporte():
    report = "*REPORTE DE RENDIMIENTO*\\n"
    report += "---------------------\\n"
    total_profit = 0
    total_trades = 0
    
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        total_profit += data["profit_abs"]
        total_trades += data["total"]
        status_sym = "[+]" if data["profit_abs"] >= 0 else "[-]"
        report += f"{status_sym} {name}: ${data['profit_abs']:+.2f} (WR {data['win_rate']:.0f}%)\\n"
    
    report += "---------------------\\n"
    report += f"TOTAL: ${total_profit:+.2f} ({total_profit/4000*100:+.1f}%)\\n"
    report += f"TRADES: {total_trades}"
    return report

def cmd_detalle():
    msg = "*ULTIMOS 5 TRADES POR TORRE*\\n\\n"
    for name, path in DB_FILES.items():
        if not os.path.exists(path):
            continue
        try:
            conn = sqlite3.connect(path)
            c = conn.cursor()
            c.execute("SELECT pair, close_profit, close_date FROM trades WHERE is_open=0 ORDER BY id DESC LIMIT 5")
            rows = c.fetchall()
            conn.close()
            if rows:
                msg += f"*{name}*:\\n"
                for r in rows:
                    msg += f"  {r[0]}: {r[1]*100:+.2f}%\\n"
                msg += "\\n"
        except:
            continue
    return msg

def cmd_balance():
    balance = 4000.0  # 4 torres x $1000
    total_profit = sum(analyze_bot(name, path)["profit_abs"] for name, path in DB_FILES.items())
    return f"*BALANCE DRY RUN*\\nInicial: ${balance:.2f}\\nProfit: ${total_profit:+.2f}\\nActual: ${balance + total_profit:.2f}"

def run_conserje():
   log("Iniciando Conserje Chacal v4 (Dry Run Edition)...")
    token, chat_id = get_tg_credentials()
    if not token or not chat_id:
        log("ERROR: Credenciales de Telegram no encontradas en ENV")
        return
    
    last_update_id = 0
    keyboard = get_keyboard()
    send_telegram("Conserje v4 Online\\nSetup: ALPHA, BETA, GAMMA, DELTA (DRY RUN)", token, chat_id, keyboard)
    
    while True:
        updates = call_tg("getUpdates", {"offset": last_update_id + 1, "timeout": 5}, token)
        if updates and updates.get("ok"):
            for up in updates.get("result", []):
                last_update_id = up.get("update_id")
                msg = up.get("message", {})
                text = msg.get("text", "")
                if str(msg.get("chat", {}).get("id")) != str(chat_id):
                    continue
                
                if text in ["Estado", "/status"]:
                    send_telegram(cmd_estado(), token, chat_id, keyboard)
                elif text in ["Reporte", "/report"]:
                    send_telegram(cmd_reporte(), token, chat_id, keyboard)
                elif text in ["Hoy", "/daily"]:
                    send_telegram(cmd_detalle(), token, chat_id, keyboard)
                elif text in ["Detalle", "/detail"]:
                    send_telegram(cmd_detalle(), token, chat_id, keyboard)
                elif text in ["Balance", "/balance"]:
                    send_telegram(cmd_balance(), token, chat_id, keyboard)
                elif text in ["Ping", "/ping"]:
                    send_telegram("Vigilando!", token, chat_id, keyboard)
        
        time.sleep(2)

if __name__ == "__main__":
    run_conserje()
