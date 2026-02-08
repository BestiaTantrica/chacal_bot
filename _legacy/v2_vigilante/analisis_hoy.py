import sqlite3
import glob
import datetime
import os

print('--- ANÁLISIS DE TRADES DE HOY (SERVER) ---')
# Get today's date in YYYY-MM-DD
today = datetime.date.today().isoformat()
print(f"Fecha: {today}")

# Check all DBs
dbs = glob.glob('user_data/tradesv3_*.sqlite')
total_profit = 0

for db_file in dbs:
    try:
        name = os.path.basename(db_file).replace('tradesv3_', '').replace('.sqlite', '').upper()
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Query for today's exits
        cursor.execute("SELECT pair, close_profit_abs, exit_reason, close_date, close_rate FROM trades WHERE date(close_date) >= ?", (today,))
        rows = cursor.fetchall()
        
        if rows:
            print(f'\nBOT: {name}')
            for r in rows:
                profit = r[1]
                reason = r[2]
                time = r[3].split()[1] if r[3] else "?"
                total_profit += profit
                icon = "✅" if profit > 0 else "❌"
                print(f"  {icon} {r[0]}: ${profit:.2f} | {reason} | Hora: {time}")
        
        conn.close()
    except Exception as e:
        print(f"Error leyendo {db_file}: {e}")

print(f"\nTOTAL HOY: ${total_profit:.2f}")
