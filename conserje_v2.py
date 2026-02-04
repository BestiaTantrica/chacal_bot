import os
import sqlite3
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict

# --- CONFIGURACIÓN ---
CHECK_INTERVAL = 20
POLL_INTERVAL = 5
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
    full_msg = f"🐺 *CHACAL COMANDANTE* 🐺\n\n{msg}"
    params = {"chat_id": chat_id, "text": full_msg, "parse_mode": "Markdown"}
    
    if keyboard:
        params["reply_markup"] = keyboard
    
    call_tg("sendMessage", params, token)

def get_keyboard():
    """Teclado con botones para comandos"""
    return {
        "keyboard": [
            [{"text": "🔍 Auditoría"}, {"text": "📊 Reporte"}],
            [{"text": "🏆 Ganadores"}, {"text": "⚠️ Perdedores"}],
            [{"text": "💰 Balance"}, {"text": "📅 Hoy"}],
            [{"text": "📍 Estado"}, {"text": "🐺 Ping"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

# --- ANÁLISIS ---
def analyze_bot(name, db_path):
    """Analiza un bot y retorna métricas completas"""
    if not os.path.exists(db_path):
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT pair, close_profit, close_profit_abs FROM trades WHERE is_open=0")
        trades = c.fetchall()
        conn.close()
        
        if not trades:
            return {"name": name, "total": 0, "profit_abs": 0, "win_rate": 0}
        
        total = len(trades)
        wins = len([t for t in trades if t[1] and t[1] > 0])
        win_rate = (wins / total * 100) if total > 0 else 0
        profit_abs = sum(t[2] for t in trades if t[2])
        
        # Por par
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
            "by_pair": dict(by_pair)
        }
    except:
        return None

# --- COMANDOS ---

def cmd_audit(bot_name=None):
    """Auditoría completa - /a"""
    if bot_name:
        bot_name = bot_name.upper()
        if bot_name not in DB_FILES:
            return f"⚠️ Bot '{bot_name}' no encontrado"
        
        data = analyze_bot(bot_name, DB_FILES[bot_name])
        if not data or data["total"] == 0:
            return f"📭 {bot_name}: Sin datos"
        
        msg = f"*🔍 AUDITORÍA - {bot_name}*\n\n"
        msg += f"Trades: `{data['total']}`\n"
        msg += f"Win Rate: `{data['win_rate']:.1f}%`\n"
        msg += f"Profit: `${data['profit_abs']:.2f}`\n\n"
        
        pairs_sorted = sorted(data['by_pair'].items(), key=lambda x: x[1]['profit'], reverse=True)
        msg += "*Top Pares:*\n"
        for pair, pdata in pairs_sorted[:3]:
            wr = (pdata['wins'] / pdata['count'] * 100) if pdata['count'] > 0 else 0
            emoji = "✅" if pdata['profit'] > 0 else "⛔"
            msg += f"{emoji} `{pair}`: ${pdata['profit']:.2f} (WR {wr:.0f}%)\n"
        
        return msg
    
    # Auditoría de todos
    results = {}
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data and data["total"] > 0:
            results[name] = data
    
    if not results:
        return "📭 No hay datos disponibles"
    
    msg = "*🔍 AUDITORÍA COMPLETA*\n\n"
    ranked = sorted(results.values(), key=lambda x: x["profit_abs"], reverse=True)
    
    for bot in ranked:
        status = "✅" if bot["profit_abs"] > 0 else "⛔"
        msg += f"{status} *{bot['name']}*: ${bot['profit_abs']:.2f} | WR {bot['win_rate']:.0f}%\n"
    
    return msg

def cmd_winners():
    """Top ganadores - /w"""
    results = {}
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data and data["total"] > 0 and data["profit_abs"] > 0:
            results[name] = data
    
    if not results:
        return "🌙 No hay ganadores aún"
    
    ranked = sorted(results.values(), key=lambda x: x["profit_abs"], reverse=True)
    msg = "*🏆 TOP PERFORMERS*\n\n"
    
    for i, bot in enumerate(ranked[:5], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        msg += f"{medal} *{bot['name']}*: `${bot['profit_abs']:.2f}` (WR {bot['win_rate']:.0f}%)\n"
    
    return msg

def cmd_losers():
    """Bots en pérdida - /l"""
    results = {}
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data and data["total"] > 0 and data["profit_abs"] < 0:
            results[name] = data
    
    if not results:
        return "✅ Todos los bots en positivo"
    
    ranked = sorted(results.values(), key=lambda x: x["profit_abs"])
    msg = "*⚠️ BOTS EN ROJO*\n\n"
    
    for bot in ranked:
        worst_pair = min(bot['by_pair'].items(), key=lambda x: x[1]['profit']) if bot['by_pair'] else None
        msg += f"⛔ *{bot['name']}*: `${bot['profit_abs']:.2f}`\n"
        if worst_pair:
            msg += f"   Problema: `{worst_pair[0]}` (${worst_pair[1]['profit']:.2f})\n"
        msg += "\n"
    
    return msg

def cmd_report():
    """Reporte ejecutivo - /r"""
    results = {}
    for name, path in DB_FILES.items():
        data = analyze_bot(name, path)
        if data and data["total"] > 0:
            results[name] = data
    
    if not results:
        return "📭 No hay datos disponibles"
    
    total_profit = sum(b['profit_abs'] for b in results.values())
    total_trades = sum(b['total'] for b in results.values())
    global_wins = sum(b['wins'] for b in results.values())
    global_wr = (global_wins / total_trades * 100) if total_trades > 0 else 0
    
    msg = "*📊 REPORTE EJECUTIVO*\n\n"
    msg += f"💰 Capital: `${300 + total_profit:.2f}`\n"
    msg += f"📈 Profit: `${total_profit:.2f}` ({total_profit/300*100:.2f}%)\n"
    msg += f"📊 Trades: `{total_trades}` | WR: `{global_wr:.1f}%`\n\n"
    
    msg += "*Por Bot:*\n"
    for name, bot in sorted(results.items()):
        status = "✅" if bot["profit_abs"] > 0 else "⛔"
        msg += f"{status} {name}: `${bot['profit_abs']:.2f}`\n"
    
    losers = [b for b in results.values() if b['profit_abs'] < 0]
    if losers:
        msg += f"\n⚠️ *Alertas:* {len(losers)} bots en rojo"
    else:
        msg += "\n🚀 *Status:* Todos positivos"
    
    return msg

def cmd_balance():
    """Balance detallado - /b"""
    total_profit = 0.0
    detail = []
    
    for name, db_path in DB_FILES.items():
        if not os.path.exists(db_path):
            continue
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT SUM(close_profit_abs) FROM trades WHERE is_open=0")
            val = c.fetchone()[0]
            profit = val if val else 0
            total_profit += profit
            
            # Capital inicial por bot (aproximado)
            initial = 50  # Asumimos $50 inicial por bot
            current = initial + profit
            pct = (profit / initial * 100) if initial > 0 else 0
            
            status = "🚀" if profit > 5 else "✅" if profit > 0 else "⚠️" if profit > -5 else "🚨"
            detail.append(f"{status} {name}: `${current:.2f}` (`{profit:+.2f}` / `{pct:+.1f}%`)")
            
            conn.close()
        except:
            continue
    
    current = 300.0 + total_profit
    msg = f"*💰 BALANCE CONSOLIDADO*\n\n"
    msg += f"Capital Inicial: `$300.00`\n"
    msg += f"Capital Actual: `${current:.2f}`\n"
    msg += f"Ganancia: `${total_profit:+.2f}` (`{total_profit/300*100:+.2f}%`)\n\n"
    msg += "*Por Bot:*\n" + "\n".join(detail)
    
    return msg

def cmd_daily():
    """Performance hoy - /d"""
    daily_profit = 0.0
    detail = []
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    
    for name, db_path in DB_FILES.items():
        if not os.path.exists(db_path):
            continue
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT SUM(close_profit_abs), COUNT(*) FROM trades WHERE is_open=0 AND close_date LIKE ?", (f"{today_str}%",))
            val, count = c.fetchone()
            profit = val if val else 0
            count = count if count else 0
            daily_profit += profit
            
            if count > 0:
                status = "✅" if profit > 0 else "⚠️"
                detail.append(f"{status} {name}: `${profit:+.2f}` ({count} trades)")
            
            conn.close()
        except:
            continue
    
    msg = f"*📅 PERFORMANCE HOY*\n\n"
    msg += f"Total: `${daily_profit:+.2f}`\n\n"
    
    if detail:
        msg += "*Desglose:*\n" + "\n".join(detail)
    else:
        msg += "_No hay trades cerrados hoy_"
    
    return msg

def cmd_status():
    """Estado de operaciones - /s"""
    report = "*📍 ESTADO DE LA MANADA*\n\n"
    found = False
    for name, db_path in DB_FILES.items():
        if not os.path.exists(db_path):
            continue
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT pair, is_short, open_rate FROM trades WHERE is_open=1")
            rows = c.fetchall()
            conn.close()
            if rows:
                found = True
                report += f"*{name}*:\n"
                for r in rows:
                    side = "🔴 SHORT" if r[1] else "🟢 LONG"
                    report += f"  {side} `{r[0]}` @ `{r[2]}`\n"
                report += "\n"
        except:
            continue
    
    if not found:
        return "🌙 No hay operaciones abiertas"
    return report

# --- CORE ---

def run_comandante():
    log("Iniciando Comandante Chacal V2.0 (Con Botones)...")
    token, chat_id = get_tg_credentials()
    if not token or not chat_id:
        return

    last_ids = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                last_ids = json.load(f)
        except:
            pass

    last_update_id = 0
    keyboard = get_keyboard()
    send_telegram("🚀 *Comandante Chacal V2.0 en línea.*\nUsa los botones o comandos cortos.", token, chat_id, keyboard)

    last_check_time = 0

    while True:
        now_ts = time.time()
        
        # 1. ESCUCHAR COMANDOS
        updates = call_tg("getUpdates", {"offset": last_update_id + 1, "timeout": 5}, token)
        if updates and updates.get("ok"):
            for up in updates.get("result", []):
                last_update_id = up.get("update_id")
                msg = up.get("message", {})
                text = msg.get("text", "")
                cid = str(msg.get("chat", {}).get("id"))

                if cid != str(chat_id):
                    continue

                # Mapeo de botones y comandos
                if text in ["🔍 Auditoría", "/a", "/audit"]:
                    send_telegram(cmd_audit(), token, chat_id, keyboard)
                elif text in ["🏆 Ganadores", "/w", "/winners"]:
                    send_telegram(cmd_winners(), token, chat_id, keyboard)
                elif text in ["⚠️ Perdedores", "/l", "/losers"]:
                    send_telegram(cmd_losers(), token, chat_id, keyboard)
                elif text in ["📊 Reporte", "/r", "/report"]:
                    send_telegram(cmd_report(), token, chat_id, keyboard)
                elif text in ["💰 Balance", "/b", "/balance"]:
                    send_telegram(cmd_balance(), token, chat_id, keyboard)
                elif text in ["📅 Hoy", "/d", "/daily", "/performance"]:
                    send_telegram(cmd_daily(), token, chat_id, keyboard)
                elif text in ["📍 Estado", "/s", "/status"]:
                    send_telegram(cmd_status(), token, chat_id, keyboard)
                elif text in ["🐺 Ping", "/ping", "/start"]:
                    send_telegram("🐺 ¡Presente! La Manada está operando.", token, chat_id, keyboard)

        # 2. ESCANEAR NOTIFICACIONES
        if now_ts - last_check_time > CHECK_INTERVAL:
            for name, db_path in DB_FILES.items():
                if not os.path.exists(db_path):
                    continue
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, pair, is_short, open_rate, close_rate, close_profit, is_open FROM trades ORDER BY id DESC LIMIT 5")
                    trades = cursor.fetchall()
                    conn.close()
                    if not trades:
                        continue

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
                except:
                    continue
            
            with open(STATE_FILE, 'w') as f:
                json.dump(last_ids, f)
            last_check_time = now_ts

        time.sleep(1)

if __name__ == "__main__":
    run_comandante()
