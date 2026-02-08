import os
import sqlite3
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict

# --- CONFIGURACIÓN ---
CHECK_INTERVAL = 30  # Escaneo de notificaciones
POLL_INTERVAL = 5    # Escucha de comandos
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
        return None

def send_telegram(msg, token, chat_id, keyboard=None):
    full_msg = f"🐺 *CHACAL COMANDANTE V3* 🐺\n\n{msg}"
    params = {"chat_id": chat_id, "text": full_msg, "parse_mode": "Markdown"}
    if keyboard:
        params["reply_markup"] = keyboard
    call_tg("sendMessage", params, token)

def get_keyboard():
    return {
        "keyboard": [
            [{"text": "📍 Estado"}, {"text": "📊 Reporte"}],
            [{"text": "🔍 Auditoría"}, {"text": "📅 Hoy"}],
            [{"text": "💰 Balance"}, {"text": "🏆 Ganadores"}],
            [{"text": "⚠️ Perdedores"}, {"text": "🐺 Ping"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

# --- ANÁLISIS ---
def analyze_bot(name, db_path):
    if not os.path.exists(db_path):
        return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0, "status": "Offline"}
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT pair, close_profit, close_profit_abs FROM trades WHERE is_open=0")
        trades = c.fetchall()
        
        c.execute("SELECT COUNT(*) FROM trades WHERE is_open=1")
        open_trades = c.fetchone()[0]
        conn.close()
        
        if not trades:
            return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0, "open_trades": open_trades, "status": "Online/Idle"}
        
        total = len(trades)
        wins = len([t for t in trades if t[1] > 0] if trades else [])
        win_rate = (wins / total * 100) if total > 0 else 0
        profit_abs = sum(t[2] for t in trades if t[2])
        
        by_pair = defaultdict(lambda: {"profit": 0, "count": 0, "wins": 0})
        for pair, pct, abs_val in trades:
            by_pair[pair]["profit"] += abs_val if abs_val else 0
            by_pair[pair]["count"] += 1
            if pct and pct > 0:
                by_pair[pair]["wins"] += 1
        
        return {
            "name": name,
            "total": total,
            "wins": wins,
            "win_rate": win_rate,
            "profit_abs": profit_abs,
            "by_pair": dict(by_pair),
            "open_trades": open_trades,
            "status": "Active"
        }
    except:
        return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0, "status": "Error"}

# --- COMANDOS ---
def cmd_status():
    report = "*📍 ESTADO DE LA MANADA*\n\n"
    active_ops = ""
    offline_bots = []
    idle_bots = []
    
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data["status"] == "Offline":
            offline_bots.append(name)
            continue
            
        if data.get("open_trades", 0) > 0:
            try:
                conn = sqlite3.connect(path)
                c = conn.cursor()
                c.execute("SELECT pair, is_short, open_rate FROM trades WHERE is_open=1")
                rows = c.fetchall()
                conn.close()
                active_ops += f"🔸 *{name}*:\n"
                for r in rows:
                    side = "🔴 SHORT" if r[1] else "🟢 LONG"
                    active_ops += f"  {side} `{r[0]}` @ `{r[2]}`\n"
                active_ops += "\n"
            except: pass
        else:
            idle_bots.append(name)

    if active_ops:
        report += "*OPERACIONES EN CURSO:*\n" + active_ops
    else:
        report += "🌙 _Sin operaciones abiertas_\n\n"
        
    if idle_bots:
        report += "💤 *En Espera:* " + ", ".join([f"`{b}`" for b in idle_bots]) + "\n"
    if offline_bots:
        report += "💀 *Offline:* " + ", ".join([f"`{b}`" for b in offline_bots]) + "\n"
        
    return report

def cmd_report():
    results = {}
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        results[name] = data
    
    total_profit = sum(b['profit_abs'] for b in results.values())
    total_trades = sum(b['total'] for b in results.values())
    global_wins = sum(b.get('wins', 0) for b in results.values())
    global_wr = (global_wins / total_trades * 100) if total_trades > 0 else 0
    
    msg = "*📊 REPORTE GENERADO*\n"
    msg += f"───────────────────\n"
    msg += f"💰 *Profit Total:* `${total_profit:+.2f}`\n"
    msg += f"📈 *Win Rate:* `{global_wr:.1f}%`\n"
    msg += f"📊 *Total Trades:* `{total_trades}`\n"
    msg += f"───────────────────\n\n"
    
    for name, bot in sorted(results.items()):
        status_emoji = "✅" if bot["profit_abs"] > 0 else "⛔" if bot["profit_abs"] < 0 else "⚪"
        msg += f"{status_emoji} *{name}*: `${bot['profit_abs']:+.2f}` | WR `{bot['win_rate']:.0f}%`\n"
    
    return msg

def cmd_audit():
    msg = "*🔍 AUDITORÍA DETALLADA*\n\n"
    found = False
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data["total"] == 0: continue
        found = True
        msg += f"🐺 *{name}*\n"
        msg += f"└ Profit: `${data['profit_abs']:.2f}`\n"
        msg += f"└ Trades: `{data['total']}` (WR: `{data['win_rate']:.1f}%`)\n"
        
        pairs_sorted = sorted(data.get('by_pair', {}).items(), key=lambda x: x[1]['profit'], reverse=True)
        if pairs_sorted:
            msg += f"└ Top: `{pairs_sorted[0][0]}` (`${pairs_sorted[0][1]['profit']:.2f}`)\n"
        msg += "\n"
        
    if not found:
        return "📭 No hay datos históricos para auditar."
    return msg

def cmd_daily():
    daily_profit = 0.0
    detail = []
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    
    for name, path in DB_FILES.items():
        if not os.path.exists(path): continue
        try:
            conn = sqlite3.connect(path)
            c = conn.cursor()
            c.execute("SELECT SUM(close_profit_abs), COUNT(*) FROM trades WHERE is_open=0 AND close_date LIKE ?", (f"{today_str}%",))
            val, count = c.fetchone()
            profit = val if val else 0
            count = count if count else 0
            daily_profit += profit
            if count > 0:
                status = "✅" if profit > 0 else "⚠️"
                detail.append(f"{status} {name}: `${profit:+.2f}` ({count}t)")
            conn.close()
        except: continue
    
    msg = f"*📅 PERFORMANCE HOY*\n\n"
    msg += f"Total Hoy: `${daily_profit:+.2f}`\n"
    if detail:
        msg += "\n" + "\n".join(detail)
    else:
        msg += "\n_Sin trades cerrados hoy_"
    return msg

def cmd_balance():
    total_profit = 0.0
    detail = []
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        profit = data["profit_abs"]
        total_profit += profit
        status = "🚀" if profit > 5 else "✅" if profit >= 0 else "🚨"
        detail.append(f"{status} {name}: `${profit:+.2f}`")
        
    current = 300.0 + total_profit
    msg = f"*💰 BALANCE GLOBAL*\n\n"
    msg += f"Capital Actual: `${current:.2f}`\n"
    msg += f"Ganancia: `${total_profit:+.2f}` (`{total_profit/300*100:+.1f}%`)\n\n"
    msg += "*Detalle por Bot:*\n" + "\n".join(detail)
    return msg

def cmd_winners():
    results = []
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data["total"] > 0 and data["profit_abs"] > 0:
            results.append(data)
    
    if not results: return "🌙 No hay ganadores acumulados."
    
    ranked = sorted(results, key=lambda x: x["profit_abs"], reverse=True)
    msg = "*🏆 MEJORES CHACALES*\n\n"
    for i, bot in enumerate(ranked[:3], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        msg += f"{medal} *{bot['name']}*: `${bot['profit_abs']:.2f}`\n"
    return msg

def cmd_losers():
    results = []
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data["total"] > 0 and data["profit_abs"] < 0:
            results.append(data)
            
    if not results: return "✅ Todos los bots están en positivo."
    
    ranked = sorted(results, key=lambda x: x["profit_abs"])
    msg = "*⚠️ BOTS EN ROJO*\n\n"
    for bot in ranked:
        msg += f"⛔ *{bot['name']}*: `${bot['profit_abs']:.2f}`\n"
    return msg

# --- CORE ---
def run_comandante():
    log("Iniciando Comandante Chacal V3.0...")
    token, chat_id = get_tg_credentials()
    if not token or not chat_id: return

    last_ids = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f: last_ids = json.load(f)
        except: pass

    last_update_id = 0
    keyboard = get_keyboard()
    
    # Registrar comandos
    commands = [
        {"command": "status", "description": "📍 Estado"},
        {"command": "report", "description": "📊 Reporte"},
        {"command": "audit", "description": "🔍 Auditoría"},
        {"command": "daily", "description": "📅 Hoy"},
        {"command": "balance", "description": "💰 Balance"},
        {"command": "winners", "description": "🏆 Ganadores"},
        {"command": "losers", "description": "⚠️ En pérdida"},
        {"command": "ping", "description": "🐺 Ping"}
    ]
    call_tg("setMyCommands", {"commands": commands}, token)
    
    send_telegram("🚀 *Comandante Chacal V3.0 en línea.*\nPanel de control actualizado para la Manada.", token, chat_id, keyboard)

    last_check_time = 0
    while True:
        now_ts = time.time()
        
        # Polling
        updates = call_tg("getUpdates", {"offset": last_update_id + 1, "timeout": 5}, token)
        if updates and updates.get("ok"):
            for up in updates.get("result", []):
                last_update_id = up.get("update_id")
                msg = up.get("message", {})
                text = msg.get("text", "")
                cid = str(msg.get("chat", {}).get("id"))
                if cid != str(chat_id): continue

                if text in ["📍 Estado", "/status"]: send_telegram(cmd_status(), token, chat_id, keyboard)
                elif text in ["📊 Reporte", "/report"]: send_telegram(cmd_report(), token, chat_id, keyboard)
                elif text in ["🔍 Auditoría", "/audit"]: send_telegram(cmd_audit(), token, chat_id, keyboard)
                elif text in ["📅 Hoy", "/daily"]: send_telegram(cmd_daily(), token, chat_id, keyboard)
                elif text in ["💰 Balance", "/balance"]: send_telegram(cmd_balance(), token, chat_id, keyboard)
                elif text in ["🏆 Ganadores", "/winners"]: send_telegram(cmd_winners(), token, chat_id, keyboard)
                elif text in ["⚠️ Perdedores", "/losers"]: send_telegram(cmd_losers(), token, chat_id, keyboard)
                elif text in ["🐺 Ping", "/ping", "/start"]: send_telegram("🐺 ¡Presente! La Manada opera bajo mi vigilancia.", token, chat_id, keyboard)

        # Notificaciones
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
                                    txt = f"🐺 *{name}* >> {side}\n✅ *ENTRADA*\nPar: `{pair}`\nPrecio: `{rate}`"
                                else:
                                    p_pct = (profit * 100) if profit else 0
                                    emoji = "💰" if p_pct > 0 else "📉"
                                    txt = f"🐺 *{name}* >> {side}\n{emoji} *CIERRE*\nPar: `{pair}`\nProfit: `{p_pct:.2f}%`"
                                send_telegram(txt, token, chat_id)
                        last_ids[name] = current_max_id
                except: continue
            
            with open(STATE_FILE, 'w') as f: json.dump(last_ids, f)
            last_check_time = now_ts
        time.sleep(1)

if __name__ == "__main__":
    run_comandante()
