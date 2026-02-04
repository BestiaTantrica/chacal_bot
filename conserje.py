import os
import sqlite3
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
CHECK_INTERVAL = 20  # Intervalo de escaneo de notificaciones
POLL_INTERVAL = 5    # Intervalo de escucha de comandos
CONFIG_FILE = "user_data/config_alpha.json"
DB_FILES = {
    "ALPHA": "user_data/tradesv3_alpha.sqlite",
    "BETA": "user_data/tradesv3_beta.sqlite",
    "GAMMA": "user_data/tradesv3_gamma.sqlite",
    "DELTA": "user_data/tradesv3_delta.sqlite",
    "EPSILON": "user_data/tradesv3_epsilon.sqlite",
    "ZETA": "user_data/tradesv3_zeta.sqlite"
}
STATE_FILE = "user_data/conserje_state.json"

def log(msg):
    print(f"[{datetime.now()}] [COMANDANTE] {msg}", flush=True)

def get_tg_credentials():
    try:
        path = CONFIG_FILE
        if not os.path.exists(path):
            path = "config_alpha.json"
        with open(path, 'r') as f:
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
    except Exception as e:
        # log(f"Error en {method}: {e}") # Silencioso para evitar spam en logs
        return None

def send_telegram(msg, token, chat_id):
    full_msg = f"🐺 *CHACAL COMANDANTE* 🐺\n\n{msg}"
    call_tg("sendMessage", {"chat_id": chat_id, "text": full_msg, "parse_mode": "Markdown"}, token)

# --- COMANDOS ---

def cmd_status():
    report = "*ESTADO DE LA MANADA*\n\n"
    found = False
    for name, db_path in DB_FILES.items():
        if not os.path.exists(db_path): continue
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT pair, is_short, open_rate, close_profit FROM trades WHERE is_open=1")
            rows = c.fetchall()
            conn.close()
            if rows:
                found = True
                report += f"📍 *{name}*:\n"
                for r in rows:
                    side = "🔴 SHORT" if r[1] else "🟢 LONG"
                    report += f"- `{r[0]}` {side} (@{r[2]})\n"
        except: continue
    
    if not found:
        return "🌙 No hay operaciones abiertas ahora mismo."
    return report

def cmd_balance():
    total_profit = 0.0
    for db_path in DB_FILES.values():
        if not os.path.exists(db_path): continue
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT SUM(close_profit_abs) FROM trades WHERE is_open=0")
            val = c.fetchone()[0]
            if val: total_profit += val
            conn.close()
        except: continue
    
    current = 300.0 + total_profit
    return f"💰 *BALANCE CONSOLIDADO*\n\nInversión: `$300.00`\nActual: `${current:.2f}`\nGanancia total: `${total_profit:.2f}`"

def cmd_daily():
    daily_profit = 0.0
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    for db_path in DB_FILES.values():
        if not os.path.exists(db_path): continue
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            # Freqtrade guarda fechas en formato texto a veces, buscamos trades cerrados hoy
            c.execute("SELECT SUM(close_profit_abs) FROM trades WHERE is_open=0 AND close_date LIKE ?", (f"{today_str}%",))
            val = c.fetchone()[0]
            if val: daily_profit += val
            conn.close()
        except: continue
    
    return f"📅 *PERFORMANCE HOY*\n\nCosechado: `${daily_profit:.2f}`"

# --- CORE ---

def run_comandante():
    log("Iniciando Comandante Chacal (Interactivo)...")
    token, chat_id = get_tg_credentials()
    if not token or not chat_id: return

    last_ids = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                last_ids = json.load(f)
        except: pass

    last_update_id = 0
    send_telegram("🚀 *Comandante Chacal en línea.* Notificaciones y Comandos activos.", token, chat_id)

    last_check_time = 0

    while True:
        now_ts = time.time()
        
        # 1. ESCUCHAR COMANDOS (Polling)
        updates = call_tg("getUpdates", {"offset": last_update_id + 1, "timeout": 5}, token)
        if updates and updates.get("ok"):
            for up in updates.get("result", []):
                last_update_id = up.get("update_id")
                msg = up.get("message", {})
                text = msg.get("text", "")
                cid = str(msg.get("chat", {}).get("id"))

                if cid != str(chat_id): continue # Ignorar extraños

                if text.startswith("/status"):
                    send_telegram(cmd_status(), token, chat_id)
                elif text.startswith("/balance"):
                    send_telegram(cmd_balance(), token, chat_id)
                elif text.startswith("/daily") or text.startswith("/performance"):
                    send_telegram(cmd_daily(), token, chat_id)
                elif text.startswith("/ping") or text.startswith("/start"):
                    send_telegram("🐺 ¡Presente! La Manada está operando.", token, chat_id)

        # 2. ESCANEAR NOTIFICACIONES (Cada CHECK_INTERVAL)
        if now_ts - last_check_time > CHECK_INTERVAL:
            for name, db_path in DB_FILES.items():
                if not os.path.exists(db_path): continue
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, pair, is_short, open_rate, close_rate, close_profit, is_open FROM trades ORDER BY id DESC LIMIT 5")
                    trades = cursor.fetchall()
                    conn.close()
                    if not trades: continue

                    current_max_id = trades[0][0]
                    prev_max_id = last_ids.get(name, 0)

                    if prev_max_id == 0:
                        last_ids[name] = current_max_id
                        continue

                    if current_max_id > prev_max_id:
                        for trade in reversed(trades):
                            tid, pair, is_short, rate, close_rate, profit, is_open = trade
                            if tid > prev_max_id:
                                side = "🔴 SHORT" if is_short else "🟢 LONG"
                                if is_open:
                                    txt = f"*{name}* >> {side} *ENTRADA*\nPar: `{pair}`\nPrecio: `{rate}`"
                                else:
                                    p_pct = (profit * 100) if profit else 0
                                    emoji = "💰" if p_pct > 0 else "📉"
                                    txt = f"*{name}* >> {emoji} *CIERRE {side}*\nPar: `{pair}`\nProfit: `{p_pct:.2f}%`"
                                send_telegram(txt, token, chat_id)
                        last_ids[name] = current_max_id
                except: continue
            
            with open(STATE_FILE, 'w') as f:
                json.dump(last_ids, f)
            last_check_time = now_ts

        time.sleep(1)

if __name__ == "__main__":
    run_comandante()
