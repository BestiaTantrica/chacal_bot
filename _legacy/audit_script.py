import sqlite3
import os
from datetime import datetime, timedelta

# Note: Inside the container, user_data is at /freqtrade/user_data
DB_FILES = {
    "ALPHA": "/freqtrade/user_data/tradesv3_alpha.sqlite",
    "BETA": "/freqtrade/user_data/tradesv3_beta.sqlite",
    "GAMMA": "/freqtrade/user_data/tradesv3_gamma.sqlite"
}

def audit_db(name, db_path):
    if not os.path.exists(db_path):
        print(f"[{name}] Archivo no encontrado: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check columns
        cursor.execute("PRAGMA table_info(trades)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Get trades from today (UTC)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        
        # Query trades
        query = f"SELECT id, pair, open_date, close_date, close_profit, close_profit_abs, is_open FROM trades WHERE open_date >= '{today_start}' OR close_date >= '{today_start}'"
        cursor.execute(query)
        trades = cursor.fetchall()
        
        print(f"\n--- REPORTE {name} (Hoy) ---")
        print(f"Columnas detectadas: {columns}")
        
        closed_trades = [t for t in trades if t[6] == 0]
        open_trades = [t for t in trades if t[6] == 1]
        
        print(f"Operaciones cerradas hoy: {len(closed_trades)}")
        print(f"Operaciones abiertas actualmente: {len(open_trades)}")
        
        total_profit_pct = sum(t[4] if t[4] is not None else 0 for t in closed_trades) * 100
        total_profit_abs = sum(t[5] if t[5] is not None else 0 for t in closed_trades)
        
        print(f"Ganancia Total %: {total_profit_pct:.2f}%")
        print(f"Ganancia Total Abs: {total_profit_abs:.2f} USDT")
        
        if closed_trades:
            print("Detalle de cierres:")
            for t in closed_trades:
                print(f"  - {t[1]}: {t[4]*100 if t[4] else 0:.2f}% ({t[5] if t[5] else 0:.2f} USDT)")
        
        conn.close()
    except Exception as e:
        print(f"[{name}] Error: {e}")

if __name__ == "__main__":
    print(f"Auditoría iniciada: {datetime.utcnow()} UTC")
    for name, path in DB_FILES.items():
        audit_db(name, path)
