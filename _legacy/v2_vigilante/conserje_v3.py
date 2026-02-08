import os
import sqlite3
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict

# --- CONFIGURACIÓN ---
CHECK_INTERVAL = 30
POLL_INTERVAL = 5
CONFIG_FILE = "user_data/config_alpha.json"
# SOLO Los Hunters activos (Alpha, Beta, Gamma, Delta)
DB_FILES = {
    "ALPHA": "user_data/tradesv3_alpha.sqlite",
    "BETA": "user_data/tradesv3_beta.sqlite",
    "GAMMA": "user_data/tradesv3_gamma.sqlite",
    "DELTA": "user_data/tradesv3_delta.sqlite"
}
STATE_FILE = "user_data/conserje_state.json"

def log(msg):
    print(f"[{datetime.now()}] [COMANDANTE] {msg}", flush=True)

def get_tg_credentials():
    try:
        path = CONFIG_FILE
        if not os.path.exists(path): path = "config_alpha.json"
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            tg = config.get('telegram', {})
            return tg.get('token'), tg.get('chat_id')
    except Exception as e:
        log(f"Error cargando credenciales: {e}")
        return None, None

def call_tg(method, params, token):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(params).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except: return None

def send_telegram(msg, token, chat_id, keyboard=None):
    # Usamos prefijos de texto en lugar de emojis complejos que fallan en codificacion
    full_msg = f"*CHACAL COMANDANTE V3.2*\n\n{msg}"
    params = {"chat_id": chat_id, "text": full_msg, "parse_mode": "Markdown"}
    if keyboard: params["reply_markup"] = keyboard
    call_tg("sendMessage", params, token)

def get_keyboard():
    return {
        "keyboard": [
            [{"text": "Estado"}, {"text": "Reporte"}],
            [{"text": "Auditoria"}, {"text": "Hoy"}],
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
            return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0, "open_trades": open_trades, "status": "ESPERA"}
        
        total = len(trades)
        wins = len([t for t in trades if t[1] and t[1] > 0])
        win_rate = (wins / total * 100) if total > 0 else 0
        profit_abs = sum(t[2] for t in trades if t[2])
        return {"name": name, "total": total, "profit_abs": profit_abs, "win_rate": win_rate, "open_trades": open_trades, "status": "OK"}
    except: return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0, "status": "ERR"}

def cmd_status():
    report = "*ESTADO DE LOS HUNTERS*\n\n"
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
                active_ops += f"[*] *{name}*:\n"
                for r in rows:
                    side = "SHORT" if r[1] else "LONG"
                    active_ops += f"  - {side} {r[0]} @ {r[2]}\n"
                active_ops += "\n"
            except: pass
        else:
            idle_bots.append(name)

    if active_ops:
        report += active_ops
    else:
        report += "Sin operaciones abiertas.\n\n"
        
    if idle_bots:
        report += "Buscando entrada: " + ", ".join(idle_bots) + "\n"
        
    return report

def cmd_report():
    report = "*REPORTE DE RENDIMIENTO*\n"
    report += "---------------------\n"
    total_profit = 0
    total_trades = 0
    
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        total_profit += data["profit_abs"]
        total_trades += data["total"]
        status_sym = "[+]" if data["profit_abs"] >= 0 else "[-]"
        report += f"{status_sym} {name}: ${data['profit_abs']:+.2f} (WR {data['win_rate']:.0f}%)\n"
    
    report += "---------------------\n"
    report += f"TOTAL: ${total_profit:+.2f} ({total_profit/300*100:+.1f}%)\n"
    report += f"TRADES: {total_trades}"
    return report

def cmd_audit():
    msg = "*AUDITORIA POR BOT*\n\n"
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data["total"] > 0:
            msg += f"- {name}: ${data['profit_abs']:.2f} ({data['total']} trades)\n"
        else:
            msg += f"- {name}: Sin historial (Delta/Otras)\n"
    return msg

def cmd_daily():
    daily_profit = 0
    now = datetime.now().strftime('%Y-%m-%d')
    found = False
    for name, path in DB_FILES.items():
        if not os.path.exists(path): continue
        try:
            conn = sqlite3.connect(path)
            c = conn.cursor()
            c.execute("SELECT SUM(close_profit_abs) FROM trades WHERE is_open=0 AND close_date LIKE ?", (f"{now}%",))
            res = c.fetchone()[0]
            if res:
                daily_profit += res
                found = True
            conn.close()
        except: continue
    return f"*PERFORMANCE HOY:* ${daily_profit:+.2f}" if found else "No hay cierres hoy todavia."

def run_comandante():
    log("Iniciando Comandante Chacal V3.2 (Clean/No Epsilon/No Zeta)...")
    token, chat_id = get_tg_credentials()
    if not token or not chat_id: return

    last_ids = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f: last_ids = json.load(f)
        except: pass

    last_update_id = 0
    keyboard = get_keyboard()
    send_telegram("Comandante Chacal V3.2 Online\nSetup: ALPHA, BETA, GAMMA, DELTA.\nSin Zeta ni Epsilon.", token, chat_id, keyboard)

    last_check_time = 0
    while True:
        now_ts = time.time()
        updates = call_tg("getUpdates", {"offset": last_update_id + 1, "timeout": 5}, token)
        if updates and updates.get("ok"):
            for up in updates.get("result", []):
                last_update_id = up.get("update_id")
                msg = up.get("message", {})
                text = msg.get("text", "")
                if str(msg.get("chat", {}).get("id")) != str(chat_id): continue

                if text in ["Estado", "/status"]: send_telegram(cmd_status(), token, chat_id, keyboard)
                elif text in ["Reporte", "/report"]: send_telegram(cmd_report(), token, chat_id, keyboard)
                elif text in ["Auditoria", "/audit"]: send_telegram(cmd_audit(), token, chat_id, keyboard)
                elif text in ["Hoy", "/daily"]: send_telegram(cmd_daily(), token, chat_id, keyboard)
                elif text in ["Balance", "/balance"]: send_telegram(cmd_report(), token, chat_id, keyboard)
                elif text in ["Ping", "/ping"]: send_telegram("¡Vigilando!", token, chat_id, keyboard)

        if now_ts - last_check_time > CHECK_INTERVAL:
            for name, db_path in DB_FILES.items():
                if not os.path.exists(db_path): continue
                try:
                    conn = sqlite3.connect(db_path)
                    c = conn.cursor()
                    c.execute("SELECT id, pair, is_short, open_rate, close_profit, is_open FROM trades ORDER BY id DESC LIMIT 1")
                    last = c.fetchone()
                    conn.close()
                    if not last: continue
                    tid, pair, is_short, rate, profit, is_open = last
                    prev = last_ids.get(name, 0)
                    if tid > prev:
                        side = "SHORT" if is_short else "LONG"
                        status = "ENTRADA" if is_open else "CIERRE"
                        msg = f"{name} >> {side} {status}\nPar: {pair}"
                        if not is_open:
                            msg += f"\nProfit: {profit*100:.2f}%"
                        send_telegram(msg, token, chat_id)
                        last_ids[name] = tid
                except: continue
            with open(STATE_FILE, 'w') as f: json.dump(last_ids, f)
            last_check_time = now_ts
        time.sleep(1)

if __name__ == "__main__":
    run_comandante()
