import sqlite3
import os

dbs = ["alpha", "beta", "gamma", "delta"]
base_path = "/home/ec2-user/chacal_bot/user_data/"

print("--- AUDITORIA DE TRADES (DRY RUN V4) ---")
for db in dbs:
    path = os.path.join(base_path, f"tradesv3_{db}_dry.sqlite")
    if not os.path.exists(path):
        print(f"DB {db}: No existe")
        continue
    
    conn = sqlite3.connect(path)
    c = conn.cursor()
    print(f"\n[TORRE {db.upper()}]")
    c.execute("SELECT pair, close_profit_abs, close_date, exit_reason, stake_amount FROM trades WHERE is_open=0")
    rows = c.fetchall()
    for r in rows:
        print(f"  PAIR: {r[0]} | PROFIT: ${r[1]:.2f} | DATE: {r[2]} | REASON: {r[3]} | STAKE: ${r[4]:.2f}")
    
    c.execute("SELECT pair, open_date, stake_amount FROM trades WHERE is_open=1")
    opens = c.fetchall()
    for o in opens:
        print(f"  * OPEN: {o[0]} | DATE: {o[1]} | STAKE: ${o[2]:.2f}")
    conn.close()
