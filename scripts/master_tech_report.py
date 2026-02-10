import sqlite3
import os
import json
from datetime import datetime

DBS = {
    "ALPHA": "/home/ec2-user/chacal_bot/user_data/tradesv3_alpha_dry.sqlite",
    "BETA": "/home/ec2-user/chacal_bot/user_data/tradesv3_beta_dry.sqlite",
    "GAMMA": "/home/ec2-user/chacal_bot/user_data/tradesv3_gamma_dry.sqlite",
    "DELTA": "/home/ec2-user/chacal_bot/user_data/tradesv3_delta_dry.sqlite"
}

def get_tech_data(name, path):
    if not os.path.exists(path): return {"name": name, "status": "FILE_NOT_FOUND"}
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        
        # Balance simulado (debería venir del config, pero estimamos por ahora)
        c.execute("SELECT close_profit_abs, pair, open_date, close_date, is_open FROM trades")
        trades = c.fetchall()
        
        total_profit = sum(t[0] for t in trades if t[0] is not None and not t[4])
        open_trades = [t for t in trades if t[4]]
        
        conn.close()
        return {
            "name": name,
            "profit": total_profit,
            "count": len([t for t in trades if not t[4]]),
            "open": len(open_trades),
            "last_trade": trades[-1][3] if trades else "None"
        }
    except Exception as e:
        return {"name": name, "status": f"ERROR: {str(e)}"}

def master_report():
    print("🛰️ <b>SNIPER V4 - STATUS TÉCNICO</b>")
    total_p = 0
    any_open = False
    
    for name, path in DBS.items():
        data = get_tech_data(name, path)
        if "status" in data:
            print(f"<b>[{name}]</b>: ⚠️ {data['status']}")
            continue
        
        total_p += data['profit']
        icon = "🦅" if data['open'] > 0 else "💤"
        print(f"<b>[{name}]</b> {icon} | P: <b>${data['profit']:+.4f}</b> | Ops: {data['count']} | Open: {data['open']}")
        if data['open'] > 0: any_open = True
            
    print("═" * 15)
    print(f"💰 <b>TOTAL PROFIT: ${total_p:+.4f}</b>")
    print(f"💵 <b>WALLET EST:  ${(75 * 4) + total_p:.2f}</b>")
    if not any_open: print("<i>No hay operaciones abiertas en este momento.</i>")

if __name__ == "__main__":
    master_report()
