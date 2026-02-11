import sqlite3
import os
from datetime import datetime, timezone

# Protocolo Sniper V4 - Rutas de las Torres
DBS = {
    "ALPHA": "/home/ec2-user/chacal_bot/user_data/tradesv3_alpha_dry.sqlite",
    "BETA": "/home/ec2-user/chacal_bot/user_data/tradesv3_beta_dry.sqlite",
    "GAMMA": "/home/ec2-user/chacal_bot/user_data/tradesv3_gamma_dry.sqlite",
    "DELTA": "/home/ec2-user/chacal_bot/user_data/tradesv3_delta_dry.sqlite"
}

def is_magic_hour():
    now = datetime.now(timezone.utc)
    # Londres: 08-10 UTC | NY: 13:30-17:30 UTC
    if (8 <= now.hour < 10) or (now.hour == 13 and now.minute >= 30) or (14 <= now.hour < 17) or (now.hour == 17 and now.minute <= 30):
        return True
    return False

def analyze_torre(name, path):
    if not os.path.exists(path): 
        # Intentar ruta relativa si la absoluta falla (para pruebas locales)
        local_path = os.path.join("user_data", os.path.basename(path))
        if os.path.exists(local_path): path = local_path
        else: return None
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        
        # 1. Histórico (Cerradas)
        c.execute("SELECT close_profit_abs FROM trades WHERE is_open=0")
        closed = [x[0] for x in c.fetchall() if x[0] is not None]
        
        # 2. Activas (Abiertas)
        c.execute("PRAGMA table_info(trades)")
        cols = [col[1] for col in c.fetchall()]
        q = "SELECT pair, current_profit_abs FROM trades WHERE is_open=1" if "current_profit_abs" in cols else "SELECT pair, 0 FROM trades WHERE is_open=1"
        c.execute(q)
        open_trades = c.fetchall()
        
        conn.close()
        return {
            "name": name,
            "closed_profit": sum(closed),
            "closed_count": len(closed),
            "open_count": len(open_trades),
            "open_details": open_trades
        }
    except: return None

def report():
    hunting = is_magic_hour()
    now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
    
    print(f"🛰️ <b>SISTEMA SNIPER V4</b> | {now_str} UTC")
    print(f"ESTADO GLOBAL: {'🏹 <b>CAZANDO (HUNTING)</b>' if hunting else '💤 <b>MODO ESPERA (IDLE)</b>'}\n")
    
    total_p = 0
    total_open = 0
    
    for name, path in DBS.items():
        data = analyze_torre(name, path)
        if not data:
            print(f"<b>[{name}]</b>: ⚪ Sin conexión")
            continue
            
        total_p += data['closed_profit']
        total_open += data['open_count']
        
        status = "🏹" if (hunting and data['open_count'] == 0) else ("🔥" if data['open_count'] > 0 else "💤")
        
        print(f"<b>[{name}]</b> {status} | Cerrado: <b>${data['closed_profit']:+.2f}</b> | Abiertas: <b>{data['open_count']}</b>")
        for ot in data['open_details']:
            print(f"   └ 🎯 {ot[0].split('/')[0]} ({ot[1]:+.2f}%)")
            
    print("\n" + "═"*25)
    print(f"💰 <b>PROFIT TOTAL: ${total_p:+.2f}</b>")
    print(f"⚖️ <b>USDT ESTIMADO: ${(75*4)+total_p:.2f}</b>")
    print(f"📡 <b>OPS ACTIVAS: {total_open}</b>")
    # Asegurar que el mensaje no sea demasiado largo
    
if __name__ == "__main__":
    report()
