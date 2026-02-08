import os
import sqlite3
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict

# --- CONFIGURACION PEGASO ---
CHECK_INTERVAL = 30
POLL_INTERVAL = 3
CONFIG_FILE = "user_data/config_alpha.json"

# SOLO HUNTERS - Epsilon y Zeta descartados segun orden directa
DB_FILES = {
    "ALPHA": "user_data/tradesv3_alpha.sqlite",
    "BETA": "user_data/tradesv3_beta.sqlite",
    "GAMMA": "user_data/tradesv3_gamma.sqlite",
    "DELTA": "user_data/tradesv3_delta.sqlite"
}
STATE_FILE = "user_data/conserje_state.json"

def log(msg):
    print(f"[{datetime.now()}] [PEGASO] {msg}", flush=True)

def get_tg_credentials():
    try:
        path = CONFIG_FILE
        if not os.path.exists(path): path = "config_alpha.json"
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            tg = config.get('telegram', {})
            return tg.get('token'), tg.get('chat_id')
    except Exception as e:
        log(f"Error credenciales: {e}")
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
    # Usamos texto plano para evitar problemas de codificacion (UTF-8)
    # Prefijo distintivo PEGASO
    full_msg = f"== PEGASO TRADER COMPANION ==\n\n{msg}"
    params = {"chat_id": chat_id, "text": full_msg, "parse_mode": "Markdown"}
    if keyboard: params["reply_markup"] = keyboard
    call_tg("sendMessage", params, token)

def get_keyboard():
    return {
        "keyboard": [
            [{"text": "Estado"}, {"text": "Reporte"}],
            [{"text": "Hoy"}, {"text": "Historia"}],
            [{"text": "Auditoria"}, {"text": "Ganadores"}],
            [{"text": "Ping"}]
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
            return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0, "open_trades": open_trades, "status": "WAIT"}
        
        total = len(trades)
        wins = [t for t in trades if t[1] and t[1] > 0]
        win_rate = (len(wins) / total * 100) if total > 0 else 0
        profit_abs = sum(t[2] for t in trades if t[2])
        return {"name": name, "total": total, "profit_abs": profit_abs, "win_rate": win_rate, "open_trades": open_trades, "status": "OK", "wins_count": len(wins)}
    except: return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0, "status": "ERR"}

def cmd_status():
    report = "*ESTADO ACTUAL DE OPERACIONES*\n\n"
    found = False
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data.get("open_trades", 0) > 0:
            found = True
            try:
                conn = sqlite3.connect(path)
                c = conn.cursor()
                c.execute("SELECT pair, is_short, open_rate FROM trades WHERE is_open=1")
                rows = c.fetchall()
                conn.close()
                report += f"[{name}]:\n"
                for r in rows:
                    side = "SHORT" if r[1] else "LONG"
                    report += f"  - {side} {r[0]} @ {r[2]}\n"
            except: pass
    
    if not found:
        return "No hay operaciones abiertas en este momento."
    return report

def cmd_report():
    # Reporte Financiero Conciso
    msg = "*REPORTE FINANCIERO ESTIMADO*\n"
    msg += "----------------------------\n"
    total_prof = 0
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        total_prof += data["profit_abs"]
        msg += f"{name}: ${data['profit_abs']:+.2f}\n"
    
    msg += "----------------------------\n"
    msg += f"CAPITAL INICIAL: $300.00\n"
    msg += f"PROF TOTAL: ${total_prof:+.2f} ({total_prof/3.0:+.1f}%)\n"
    msg += f"FONDO ACTUAL: ${300 + total_prof:.2f}"
    return msg

def cmd_audit():
    # Auditoria Tecnica
    msg = "*AUDITORIA TECNICA (Historial)*\n\n"
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        msg += f"Bot {name}:\n"
        msg += f"  - Trades: {data['total']}\n"
        msg += f"  - WinRate: {data['win_rate']:.1f}%\n"
        msg += f"  - Estado: {data['status']}\n\n"
    return msg

def cmd_daily():
    # Performance de HOY (00:00 a ahora)
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    msg = f"*PERFORMANCE HOY ({today_str})*\n\n"
    total_today = 0
    found = False
    for name, path in DB_FILES.items():
        if not os.path.exists(path): continue
        try:
            conn = sqlite3.connect(path)
            c = conn.cursor()
            c.execute("SELECT SUM(close_profit_abs), COUNT(*) FROM trades WHERE is_open=0 AND close_date LIKE ?", (f"{today_str}%",))
            res, count = c.fetchone()
            conn.close()
            if count and count > 0:
                p = res if res else 0
                total_today += p
                msg += f"Bot {name}: ${p:+.2f} ({count} trades)\n"
                found = True
        except: continue
    
    if not found:
        return "No hay trades cerrados el dia de hoy."
    msg += f"\nTOTAL HOY: ${total_today:+.2f}"
    return msg

def cmd_history():
    # Ultimos 7 dias
    msg = "*RESUMEN ULTIMA SEMANA*\n\n"
    history = defaultdict(float)
    for name, path in DB_FILES.items():
        if not os.path.exists(path): continue
        try:
            conn = sqlite3.connect(path)
            c = conn.cursor()
            c.execute("SELECT close_date, close_profit_abs FROM trades WHERE is_open=0 AND close_date IS NOT NULL")
            rows = c.fetchall()
            conn.close()
            for date_str, profit in rows:
                day = date_str.split(' ')[0]
                history[day] += profit if profit else 0
        except: continue
    
    if not history:
        return "No hay historial suficiente."
        
    sorted_days = sorted(history.keys(), reverse=True)[:7]
    for d in sorted_days:
        msg += f"{d}: ${history[d]:+.2f}\n"
    return msg

def cmd_winners():
    # Top Ganadores por profit absoluto
    results = []
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data["total"] > 0:
            results.append(data)
    
    if not results: return "Sin datos."
    
    # Ordenar por ganancia
    results.sort(key=lambda x: x["profit_abs"], reverse=True)
    msg = "*TOP GANADORES (Acumulado)*\n\n"
    for i, bot in enumerate(results, 1):
        msg += f"{i}. {bot['name']} -> ${bot['profit_abs']:.2f} (WR: {bot['win_rate']:.0f}%)\n"
    return msg

def run_pegaso():
    log("Iniciando Agente Pegaso Companion...")
    token, chat_id = get_tg_credentials()
    if not token or not chat_id:
        log("Error: Sin credenciales.")
        return

    last_ids = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f: last_ids = json.load(f)
        except: pass

    last_update_id = 0
    keyboard = get_keyboard()
    
    # Registrar comandos en la interfaz
    commands = [
        {"command": "status", "description": "Operaciones actuales"},
        {"command": "report", "description": "Balance Financiero"},
        {"command": "daily", "description": "Lo de hoy"},
        {"command": "history", "description": "Ultimos 7 dias"},
        {"command": "audit", "description": "Detalle tecnico"},
        {"command": "winners", "description": "Ranking bots"},
        {"command": "ping", "description": "Estado bot"}
    ]
    call_tg("setMyCommands", {"commands": commands}, token)
    
    send_telegram("SISTEMA PEGASO ONLINE\nMonitor remoto activado para ALPHA, BETA, GAMMA, DELTA.", token, chat_id, keyboard)

    last_check_time = 0
    while True:
        now_ts = time.time()
        
        # 1. ESCUCHAR COMANDOS (Polling Rapido)
        updates = call_tg("getUpdates", {"offset": last_update_id + 1, "timeout": 2}, token)
        if updates and updates.get("ok"):
            for up in updates.get("result", []):
                last_update_id = up.get("update_id")
                msg = up.get("message", {})
                text = msg.get("text", "")
                cid = str(msg.get("chat", {}).get("id"))
                if cid != str(chat_id): continue

                if text in ["Estado", "/status"]: send_telegram(cmd_status(), token, chat_id, keyboard)
                elif text in ["Reporte", "/report"]: send_telegram(cmd_report(), token, chat_id, keyboard)
                elif text in ["Hoy", "/daily"]: send_telegram(cmd_daily(), token, chat_id, keyboard)
                elif text in ["Historia", "/history"]: send_telegram(cmd_history(), token, chat_id, keyboard)
                elif text in ["Auditoria", "/audit"]: send_telegram(cmd_audit(), token, chat_id, keyboard)
                elif text in ["Ganadores", "/winners"]: send_telegram(cmd_winners(), token, chat_id, keyboard)
                elif text in ["Ping", "/ping"]: send_telegram("PEGASO: Vigilando desde las sombras.", token, chat_id, keyboard)

        # 2. NOTIFICACIONES DE TRADES
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
                        notif = f"BOT {name} >> {side} {status}\nPar: {pair}"
                        if not is_open:
                            p_pct = profit * 100 if profit else 0
                            notif += f"\nProfit: {p_pct:+.2f}%"
                        send_telegram(notif, token, chat_id)
                        last_ids[name] = tid
                except: continue
            
            with open(STATE_FILE, 'w') as f: json.dump(last_ids, f)
            last_check_time = now_ts
        
        time.sleep(1)

if __name__ == "__main__":
    run_pegaso()
