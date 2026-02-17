import sqlite3
import os
import subprocess
from datetime import datetime, timezone, timedelta

# Protocolo Sniper V4 - Rutas de las Torres
DBS = {
    "ALPHA": "/home/ec2-user/chacal_bot/user_data/tradesv3_alpha_dry.sqlite",
    "BETA": "/home/ec2-user/chacal_bot/user_data/tradesv3_beta_dry.sqlite",
    "GAMMA": "/home/ec2-user/chacal_bot/user_data/tradesv3_gamma_dry.sqlite",
    "DELTA": "/home/ec2-user/chacal_bot/user_data/tradesv3_delta_dry.sqlite"
}

def is_magic_hour():
    now = datetime.now(timezone.utc)
    # Ventana Londres: 08:00 - 10:00 UTC (+15m gracia = 10:15)
    londres = (now.hour == 8 or now.hour == 9) or (now.hour == 10 and now.minute <= 15)
    
    # Ventana NY: 13:30 - 17:30 UTC (+15m gracia = 17:45)
    ny = (now.hour == 13 and now.minute >= 30) or (14 <= now.hour <= 16) or (now.hour == 17 and now.minute <= 45)
    
    return londres or ny

def analyze_torre(name, path):
    if not os.path.exists(path): return None
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        
        # Histórico (Cerradas)
        c.execute("SELECT close_profit_abs FROM trades WHERE is_open=0")
        closed = [x[0] for x in c.fetchall() if x[0] is not None]
        
        # Activas (Abiertas)
        c.execute("PRAGMA table_info(trades)")
        cols = [col[1] for col in c.fetchall()]
        q = "SELECT pair, current_profit_abs, open_date FROM trades WHERE is_open=1" if "current_profit_abs" in cols else "SELECT pair, 0, open_date FROM trades WHERE is_open=1"
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
    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.strftime('%H:%M:%S')
    
    print(f"🛰️ <b>CHACAL V4 | REPORTE PREMIUM</b>\n⏰ <code>{now_str} UTC</code>")
    print(f"ESTADO: {'🏹 <b>HUNTING</b>' if hunting else '💤 <b>IDLE (FUERA DE HORA)</b>'}\n")
    
    total_p = 0
    total_open = 0
    
    for name, path in DBS.items():
        data = analyze_torre(name, path)
        if not data:
            print(f"<b>[{name}]</b>: ⚪ Offline")
            continue
            
        total_p += data['closed_profit']
        total_open += data['open_count']
        
        status = "🏹" if (hunting and data['open_count'] == 0) else ("🔥" if data['open_count'] > 0 else "💤")
        
        # Visual: [NAME] 🔥 | $ +1.20 | 1 Activa
        print(f"<b>[{name}] {status}</b> | <code>${data['closed_profit']:+.2f}</code> | {data['open_count']}A")
        for ot in data['open_details']:
            pair = ot[0].split('/')[0]
            profit = ot[1]
            print(f"   └ 🎯 {pair} (<code>{profit:+.2f}%</code>)")
            
    print("\n" + "═"*25)
    print(f"💰 <b>PROFIT TOTAL: ${total_p:+.2f}</b>")
    print(f"⚖️ <b>SOPORTE USDT: ${300 + total_p:.2f}</b>")
    print(f"📡 <b>OPS ACTIVAS: {total_open}</b>")
    
    if hunting:
        print("\n🎯 <b>VENTANA ABIERTA:</b> Operando a full.")
    else:
        print("\n💤 <b>ZONA MUERTA:</b> El Vigilante gestionará el ahorro de energía.")

if __name__ == "__main__":
    report()
